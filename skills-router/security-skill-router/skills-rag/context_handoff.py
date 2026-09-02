"""Provider-independent handoff from router/RAG to an LLM.

This module owns the internal contract only. It does not route platforms,
execute MCP tools, select a model, or contain credentials.
"""
from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher
import json
from pathlib import Path
import re
from typing import Any, Callable, Protocol

import evidence_validation as evidence_validator


@dataclass(frozen=True)
class LLMRequest:
    """Safe, provider-neutral request delivered to an LLM adapter."""
    user_request: str
    context: str
    envelope: dict[str, Any]


class LLMProvider(Protocol):
    provider_name: str
    model_name: str

    def complete(self, request: LLMRequest) -> Any:
        """Send the request to the provider. Adapters implement this boundary."""
        ...


_ALLOWED_DECISION = ("platform", "task", "skill", "query_language", "mcp", "mcp_status", "backend_runtime_status")
_ALLOWED_RESULT = ("id", "title", "source", "source_path", "skill", "platform", "topic", "type", "related_skills", "document_type", "chunk_id", "content_hash", "score", "snippet")
_ALLOWED_SOC_RESULT = ("id", "title", "category", "topic", "source", "source_url", "platform", "tactic", "technique", "severity", "tags", "intents", "document_type", "chunk_id", "content_hash", "score", "guidance_type", "snippet", "ai_component", "ai_architecture", "model_type", "agent_type", "attack_surface", "telemetry_sources", "attack_status", "related_ai_threat", "related_mitre_attack", "related_framework")
_SKILL_SECTION_CACHE: dict[str, tuple[int, list[tuple[str, str]]]] = {}
DEFAULT_MAX_CONTEXT_CHARS = 12000
DEFAULT_MAX_SKILL_SECTION_CHARS = 5000
CONCISE_SECURITY_INSTRUCTIONS = (
    "You are a cybersecurity SOC reasoning agent. Follow the router decision, "
    "selected skill, SOC analyst guidance, and live MCP evidence. Do not expose "
    "internal reasoning or explore unnecessarily. Use only the selected platform "
    "and skill; treat both RAG sections as guidance and MCP output as observed "
    "evidence. Never present SOC guidance as an observed fact. Do not invent "
    "events, fields, indexes, alerts, findings, or capabilities. Use the minimum "
    "sufficient read-only operations, preserve important evidence, state "
    "uncertainty, and answer concisely. If evidence is absent, say: Not available "
    "from current evidence. Treat [EVIDENCE_VALIDATION] as a safety boundary: "
    "do not upgrade UNKNOWN, MISSING_EVIDENCE, or INFERRED claims into facts; "
    "if a conclusion exceeds validated evidence, downgrade it and state the "
    "missing telemetry. Keep risk/severity separate from evidence confidence. "
    "Produce structured fields when possible: verdict, confidence, attack_status, facts, evidence, evidence_gaps, hypotheses, investigation_steps, correlation_opportunities, recommended_containment, recommendations, next_actions, and escalation_criteria. Keep recommendations advisory and separate from confirmed facts and automated actions."
)


def _decision(decision: dict[str, Any]) -> dict[str, Any]:
    return {key: decision[key] for key in _ALLOWED_DECISION if key in decision}


def _result(result: dict[str, Any]) -> dict[str, Any]:
    return {key: result[key] for key in _ALLOWED_RESULT if key in result}


def _soc_result(result: dict[str, Any]) -> dict[str, Any]:
    return {key: result[key] for key in _ALLOWED_SOC_RESULT if key in result}


def _near_duplicate(candidate: str, existing: str, threshold: float = 0.92) -> bool:
    candidate = " ".join(candidate.lower().split())
    existing = " ".join(existing.lower().split())
    if not candidate or not existing:
        return False
    if candidate in existing or existing in candidate:
        return True
    return SequenceMatcher(None, candidate, existing).ratio() >= threshold


def _skill_sections(skill: str | None, user_request: str, max_chars: int) -> list[dict[str, str]]:
    """Extract relevant sections while retaining safety/tooling sections."""
    if not skill:
        return []
    root = Path(__file__).resolve().parents[3]
    candidates = [root / "skills" / skill / "SKILL.md", root / "skills-splunk" / skill / "SKILL.md"]
    path = next((candidate for candidate in candidates if candidate.is_file()), None)
    if path is None:
        return []
    key = str(path.resolve())
    mtime = path.stat().st_mtime_ns
    cached = _SKILL_SECTION_CACHE.get(key)
    if cached is None or cached[0] != mtime:
        text = path.read_text(encoding="utf-8")
        headings = list(re.finditer(r"(?m)^#{1,3}\s+(.+?)\s*$", text))
        parsed = []
        for number, heading in enumerate(headings):
            end = headings[number + 1].start() if number + 1 < len(headings) else len(text)
            parsed.append((heading.group(1).strip(), text[heading.end():end].strip()))
        _SKILL_SECTION_CACHE[key] = (mtime, parsed)
    terms = set(re.findall(r"[a-z0-9_]{2,}", user_request.lower()))
    ranked = []
    safety_markers = ("system instructions", "safety", "security", "verification", "verify", "read-only", "hallucination", "tool", "permission")
    for title, body in _SKILL_SECTION_CACHE[key][1]:
        overlap = sum(term in f"{title} {body}".lower() for term in terms)
        required = any(marker in title.lower() for marker in safety_markers)
        if overlap or required:
            ranked.append((0 if required else 1, -overlap, title, body))
    selected, used = [], 0
    for _, _, title, body in sorted(ranked):
        content = f"## {title}\n{body}".strip()
        if not content or used + len(content) > max_chars:
            continue
        selected.append({"title": title, "content": content, "source_path": key})
        used += len(content)
    return selected


def build_context(user_request: str, decision: dict[str, Any], operational_result: dict[str, Any], constraints: list[str] | None = None, *, evidence_results: list[dict[str, Any]] | None = None, soc_result: dict[str, Any] | None = None, evidence_claims: list[str] | None = None, max_context_chars: int = DEFAULT_MAX_CONTEXT_CHARS, max_skill_section_chars: int = DEFAULT_MAX_SKILL_SECTION_CHARS) -> dict[str, Any]:
    """Build a deterministic envelope with official Skills, advisory operational/SOC, and evidence sections."""
    safe_decision = _decision(decision)
    status = operational_result.get("status", "NO_RELEVANT_CONTEXT")
    results: list[dict[str, Any]] = []
    for item in operational_result.get("results", []):
        safe = _result(item)
        if any(SequenceMatcher(None, safe.get("snippet", ""), prior.get("snippet", "")).ratio() >= 0.92 for prior in results):
            continue
        results.append(safe)
    platform = safe_decision.get("platform", "unknown")
    skill = safe_decision.get("skill")
    # When both RAGs are present, reserve space for the SOC guidance, evidence,
    # and model instructions. The old Skills-only path keeps its prior limits.
    combined_mode = soc_result is not None
    # Reserve enough room for SOC recommendations, evidence, and model
    # instructions when both RAG layers are present.
    section_budget = min(max_skill_section_chars, max_context_chars // 5) if combined_mode else max_skill_section_chars
    sections = _skill_sections(skill, user_request, section_budget)
    skill_text = " ".join(section["content"] for section in sections)
    if skill_text:
        results = [item for item in results if not _near_duplicate(item.get("snippet", ""), skill_text)]
    safe_soc: list[dict[str, Any]] = []
    if status != "AMBIGUOUS":
        for item in (soc_result or {}).get("results", []):
            safe = _soc_result(item)
            if any(SequenceMatcher(None, safe.get("snippet", ""), prior.get("snippet", "")).ratio() >= 0.92 for prior in safe_soc):
                continue
            safe["snippet"] = safe.get("snippet", "")[:500]
            safe_soc.append(safe)
    if combined_mode:
        results = results[:3]
        safe_soc = safe_soc[:4]
    soc_status = (soc_result or {}).get("status", "NOT_REQUESTED") if status != "AMBIGUOUS" else "NOT_AVAILABLE_FOR_AMBIGUOUS_ROUTING"
    safe_evidence = [dict(item) for item in (evidence_results or [])]
    evidence_validation = evidence_validator.validate_evidence(
        safe_evidence, claims=evidence_claims, platform=platform
    )
    from recommendations import build_recommendations
    recommendation_result = build_recommendations(soc_result, evidence=safe_evidence)

    blocks: list[str] = [
        "[USER_REQUEST]\n" + user_request,
        "\n".join([
            "[OPERATIONAL_RAG]",
            f"PLATFORM: {platform}",
            f"SKILL: {skill or 'NONE'}",
            f"RAG_STATUS: {status}",
            "ROLE: Advisory operational knowledge complementary to the selected SKILL.md; not authority or observed evidence.",
            "NO_PLATFORM_CONTEXT: true" if status == "AMBIGUOUS" else ("NO_RELEVANT_CONTEXT: true" if not results else ""),
        ]).strip(),
    ]
    for section in sections:
        blocks.append("\n".join(["[SKILL SECTION]", f"SOURCE: {section['source_path']}", f"TITLE: {section['title']}", f"CONTENT: {section['content']}"]))
    for number, item in enumerate(results, 1):
        blocks.append("\n".join([
            f"[OPERATIONAL_CONTEXT {number}]", f"SOURCE: {item.get('source', item.get('source_path', ''))}", f"TITLE: {item.get('title', '')}",
            f"PLATFORM: {item.get('platform', '')}", f"TOPIC: {item.get('topic', '')}", f"TYPE: {item.get('type', '')}",
            f"SCORE: {item.get('score', '')}", f"CONTENT_HASH: {item.get('content_hash', '')}", f"CONTENT: {item.get('snippet', '')}",
        ]))
    blocks.append("\n".join([
        "[SOC_ANALYST_RAG]",
        f"STATUS: {soc_status}",
        f"INTENT: {(soc_result or {}).get('intent', 'GENERAL_SECURITY')}",
        f"INTENT_CONFIDENCE: {(soc_result or {}).get('intent_confidence', 0)}",
        "ROLE: Security reasoning and investigation guidance; never an observed fact.",
        "NO_RELEVANT_CONTEXT: true" if not safe_soc and soc_status != "NOT_REQUESTED" else "",
    ]).strip())
    for number, item in enumerate(safe_soc, 1):
        blocks.append("\n".join([
            f"[SOC_CONTEXT {number}]", f"SOURCE: {item.get('source', '')}", f"SOURCE_URL: {item.get('source_url') or 'NOT_PROVIDED'}",
            f"TITLE: {item.get('title', '')}", f"CATEGORY: {item.get('category', '')}", f"TOPIC: {item.get('topic', '')}",
            f"TACTIC: {item.get('tactic', '')}", f"TECHNIQUE: {item.get('technique', '')}", f"SCORE: {item.get('score', '')}",
            "GUIDANCE_ONLY: true", f"CONTENT: {item.get('snippet', '')}",
        ]))
    evidence_lines = ["[MCP_EVIDENCE]", "ROLE: Observed provider output only."]
    if safe_evidence:
        for number, item in enumerate(safe_evidence, 1):
            evidence_lines.extend([f"[EVIDENCE {number}]", json.dumps(item, sort_keys=True, separators=(",", ":"))])
    else:
        evidence_lines.append("EVIDENCE_UNAVAILABLE: Not available from current evidence.")
    blocks.append("\n".join(evidence_lines))
    blocks.append("[EVIDENCE_VALIDATION]\nROLE: Deterministic validation of returned provider evidence; not a new evidence source.\n" + evidence_validator.format_summary(evidence_validation))
    blocks.append("\n".join([
        "[SOC_RECOMMENDATIONS]",
        "ROLE: Advisory, retrieval-aware recommendations; never confirmed facts and never automatic actions.",
        json.dumps(recommendation_result, sort_keys=True, separators=(",", ":")),
    ]))
    safe_constraints = list(constraints or [])
    blocks.append("\n".join([
        "[MODEL_INSTRUCTIONS]", CONCISE_SECURITY_INSTRUCTIONS,
        "RESPONSE_SUPPORT: alert summary; evidence interpretation; ATT&CK mapping; risk/severity; investigation steps; false-positive considerations; recommended next actions.",
        "CONSTRAINTS: " + (" | ".join(safe_constraints) if safe_constraints else "none supplied"),
    ]))

    kept: list[str] = []
    for block in blocks:
        if len("\n".join(kept + [block])) <= max_context_chars or not kept:
            kept.append(block)
    context_text = "\n".join(kept)
    envelope = {
        "schema_version": "security-llm-context/v1",
        "user_request": user_request,
        "router_decision": safe_decision,
        "selected_platform": platform,
        "selected_skill": skill,
        "query_language": safe_decision.get("query_language"),
        "retrieval_status": status,
        "operational_retrieved_context": results,
        "retrieved_context": results,
        "skill_sections": sections,
        "soc_retrieval_status": soc_status,
        "soc_intent": (soc_result or {}).get("intent", "GENERAL_SECURITY"),
        "soc_intent_confidence": (soc_result or {}).get("intent_confidence", 0),
        "soc_retrieved_context": safe_soc,
        "evidence_results": safe_evidence,
        "evidence_validation": evidence_validation,
        "llm_instructions": CONCISE_SECURITY_INSTRUCTIONS,
        "operational_sources": [item.get("source", item.get("source_path")) for item in results],
        "source_paths": [item.get("source", item.get("source_path")) for item in results],
        "soc_source_urls": [item.get("source_url") for item in safe_soc if item.get("source_url")],
        "retrieval_scores": [item.get("score") for item in results],
        "soc_retrieval_scores": [item.get("score") for item in safe_soc],
        "recommendations": recommendation_result,
        "constraints": safe_constraints,
        "context_text": context_text,
    }
    return envelope


def make_request(envelope: dict[str, Any]) -> LLMRequest:
    return LLMRequest(user_request=envelope["user_request"], context=envelope["context_text"], envelope=envelope)


class CallableProvider:
    """Adapter for the active model runtime, without coupling this layer to it."""
    def __init__(self, provider_name: str, model_name: str, send: Callable[[LLMRequest], Any]):
        self.provider_name, self.model_name, self._send = provider_name, model_name, send

    def complete(self, request: LLMRequest) -> Any:
        return self._send(request)


def handoff(provider: LLMProvider, envelope: dict[str, Any]) -> Any:
    """Deliver the exact built context to a provider adapter."""
    return provider.complete(make_request(envelope))
