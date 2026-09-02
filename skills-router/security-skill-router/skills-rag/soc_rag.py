"""Small, provider-independent SOC Analyst RAG.

This module deliberately owns a separate corpus and index from ``skills_rag``.
SOC documents are guidance about security reasoning; they are never MCP
evidence and never select a platform or authorize an action.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import uuid
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Iterable

from skills_rag import tokens

TOKEN_RE = re.compile(r"[a-z0-9_.-]{2,}")
DEFAULT_TOP_K = 6
DEFAULT_MAX_TOP_K = 8
DEFAULT_MIN_SCORE_RATIO = 0.42
DEFAULT_REDUNDANCY_THRESHOLD = 0.92
DEFAULT_MAX_CONTEXT_CHARS = 4200
DEFAULT_CHUNK_CHARS = 1200
DEFAULT_CHUNK_OVERLAP = 180
DEFAULT_VECTOR_SIZE = 384
VECTOR_STATUS_DISABLED = "DISABLED"

SUPPORTED_INTENTS = (
    "TRIAGE",
    "INVESTIGATION",
    "IOC_ANALYSIS",
    "MITRE_MAPPING",
    "RISK_ASSESSMENT",
    "FALSE_POSITIVE",
    "THREAT_HUNTING",
    "INCIDENT_RESPONSE",
    "DETECTION",
    "AUTHENTICATION",
    "NETWORK_ANALYSIS",
    "MALWARE_ANALYSIS",
    "WINDOWS_ANALYSIS",
    "LINUX_ANALYSIS",
    "AI_SECURITY",
    "AI_ALERT_TRIAGE",
    "PROMPT_INJECTION_ANALYSIS",
    "RAG_SECURITY_ANALYSIS",
    "AI_AGENT_SECURITY",
    "AI_DATA_LEAKAGE",
    "AI_THREAT_HUNTING",
    "AI_INCIDENT_RESPONSE",
    "AI_DETECTION_ENGINEERING",
    "GENERAL_SECURITY",
)

_INTENT_RULES = {
    "TRIAGE": ("triage", "security alert", "alert", "notable", "classify", "classification", "disposition"),
    "INVESTIGATION": ("investigate", "investigation", "suspicious process", "suspicious PowerShell", "network connection", "authentication", "analyze", "analysis", "evidence", "context"),
    "IOC_ANALYSIS": ("ioc", "indicator", "hash", "ip", "domain", "url", "enrich", "correlate"),
    "MITRE_MAPPING": ("mitre", "attack", "att&ck", "kerberoasting", "tactic", "technique", "t1558", "t1059", "mapping", "map"),
    "RISK_ASSESSMENT": ("risk", "severity", "confidence", "impact", "prioritize", "score", "brute force", "likely"),
    "FALSE_POSITIVE": ("false positive", "benign", "noise", "exception", "allowlist", "suppress", "tuning"),
    "THREAT_HUNTING": ("hunt", "hunting", "baseline", "rare", "unusual", "anomalous", "search for"),
    "INCIDENT_RESPONSE": ("incident response", "contain", "escalate", "case", "remediate", "next action"),
    "DETECTION": ("detection", "rule", "correlation", "threshold", "alert logic", "detection engineering"),
    "AUTHENTICATION": ("authentication", "login", "logon", "password", "kerberos", "ntlm", "lockout", "impossible travel"),
    "NETWORK_ANALYSIS": ("dns", "http", "https", "tls", "proxy", "firewall", "beacon", "exfiltration", "outbound"),
    "MALWARE_ANALYSIS": ("malware", "hash", "sha256", "obfuscation", "injection", "unsigned", "file reputation"),
    "WINDOWS_ANALYSIS": ("windows event", "event id", "sysmon", "security log", "process creation"),
    "LINUX_ANALYSIS": ("linux", "auth.log", "ssh", "sudo", "cron", "systemd", "bash history"),
    "AI_SECURITY": ("ai security", "llm security", "ai system", "model security", "ai attack"),
    "AI_ALERT_TRIAGE": ("llm alert", "ai alert", "ai security alert", "model alert"),
    "PROMPT_INJECTION_ANALYSIS": ("prompt injection", "instruction override", "system prompt extraction", "context manipulation", "indirect injection"),
    "RAG_SECURITY_ANALYSIS": ("rag", "rag poisoning", "retrieval poisoning", "vector database", "retrieved content", "retrieved document", "knowledge base", "malicious instruction inside"),
    "AI_AGENT_SECURITY": ("ai agent", "agent tool", "tool invocation", "unauthorized tool", "agent called", "agent hijacking", "agent memory"),
    "AI_DATA_LEAKAGE": ("ai data leakage", "model leaked", "ai leaked", "data exposure", "another user's data", "cross-tenant", "system prompt exposure", "secret exposure"),
    "AI_THREAT_HUNTING": ("ai threat hunt", "agent behavior hunt", "token baseline", "token consumption", "abnormal token", "model endpoint usage"),
    "AI_INCIDENT_RESPONSE": ("ai incident response", "contain ai", "contain agent", "ai escalation"),
    "AI_DETECTION_ENGINEERING": ("ai detection", "llm detection", "prompt injection detection", "token threshold", "ai correlation rule"),
}
_INTENT_CATEGORY = {
    "TRIAGE": "alert_triage",
    "INVESTIGATION": "investigation",
    "IOC_ANALYSIS": "ioc_analysis",
    "MITRE_MAPPING": "mitre_attack",
    "RISK_ASSESSMENT": "risk_assessment",
    "FALSE_POSITIVE": "false_positive",
    "THREAT_HUNTING": "threat_hunting",
    "INCIDENT_RESPONSE": "incident_response",
    "DETECTION": "detection_engineering",
    "AUTHENTICATION": "authentication",
    "NETWORK_ANALYSIS": "network_analysis",
    "MALWARE_ANALYSIS": "malware_analysis",
    "WINDOWS_ANALYSIS": "windows_analysis",
    "LINUX_ANALYSIS": "linux_analysis",
    "AI_SECURITY": "ai_security",
    "AI_ALERT_TRIAGE": "ai_alert_triage",
    "PROMPT_INJECTION_ANALYSIS": "prompt_injection",
    "RAG_SECURITY_ANALYSIS": "rag_security",
    "AI_AGENT_SECURITY": "ai_agent_security",
    "AI_DATA_LEAKAGE": "ai_data_leakage",
    "AI_THREAT_HUNTING": "ai_threat_hunting",
    "AI_INCIDENT_RESPONSE": "ai_incident_response",
    "AI_DETECTION_ENGINEERING": "ai_detection_engineering",
}

ALLOWED_INTENTS = frozenset(SUPPORTED_INTENTS)

_INDEX_CACHE: dict[str, Any] | None = None
_INDEX_CACHE_MTIME_NS: int | None = None
_CONFIG_CACHE: dict[str, Any] | None = None
_CONFIG_CACHE_MTIME_NS: int | None = None
_LAST_VECTOR_STATUS: dict[str, Any] = {"status": VECTOR_STATUS_DISABLED}


def _config_path() -> Path:
    return Path(__file__).resolve().parent / "config.yaml"


def load_config() -> dict[str, Any]:
    """Read SOC scalar settings without adding a YAML dependency."""
    global _CONFIG_CACHE, _CONFIG_CACHE_MTIME_NS
    path = _config_path()
    mtime = path.stat().st_mtime_ns if path.exists() else None
    if _CONFIG_CACHE is not None and _CONFIG_CACHE_MTIME_NS == mtime:
        return _CONFIG_CACHE
    values: dict[str, Any] = {
        "soc_index_path": ".rag/soc-index.json",
        "soc_data_path": "soc-knowledge/documents.jsonl",
        "soc_expanded_data_path": "soc-knowledge/documents_expanded.jsonl",
        "soc_ai_data_path": "soc-knowledge/documents_ai_security.jsonl",
        "soc_max_top_k": DEFAULT_MAX_TOP_K,
        "soc_min_score_ratio": DEFAULT_MIN_SCORE_RATIO,
        "soc_redundancy_threshold": DEFAULT_REDUNDANCY_THRESHOLD,
        "soc_max_context_chars": DEFAULT_MAX_CONTEXT_CHARS,
        "soc_chunk_chars": DEFAULT_CHUNK_CHARS,
        "soc_chunk_overlap": DEFAULT_CHUNK_OVERLAP,
        "qdrant": {
            "enabled": False,
            "url": None,
            "api_key_env": "QDRANT_API_KEY",
            "path": ".rag/qdrant",
            "collection": "soc_knowledge",
            "vector_size": DEFAULT_VECTOR_SIZE,
            "distance": "COSINE",
            "embedding_model": "all-MiniLM-L6-v2",
            "lexical_weight": 0.70,
            "vector_weight": 0.30,
            "top_k": DEFAULT_MAX_TOP_K,
        },
    }
    if path.exists():
        text = path.read_text(encoding="utf-8")
        for key, default in values.items():
            if key == "qdrant":
                continue
            match = re.search(rf"(?m)^\s*{re.escape(key)}:\s*([^#\s]+)", text)
            if not match:
                continue
            raw = match.group(1)
            try:
                values[key] = float(raw) if "." in raw else int(raw)
            except ValueError:
                values[key] = raw
        qdrant = values["qdrant"]
        for key, pattern in {
            "enabled": r"(?m)^\s+enabled:\s*([^#\s]+)",
            "url": r"(?m)^[ \t]+url:[ \t]*([^#\r\n \t]+)",
            "api_key_env": r"(?m)^[ \t]+api_key_env:[ \t]*([^#\r\n \t]+)",
            "path": r"(?m)^[ \t]+path:[ \t]*([^#\r\n \t]+)",
            "collection": r"(?m)^[ \t]+collection:[ \t]*([^#\r\n \t]+)",
            "vector_size": r"(?m)^[ \t]+vector_size:[ \t]*([^#\r\n \t]+)",
            "distance": r"(?m)^[ \t]+distance:[ \t]*([^#\r\n \t]+)",
            "embedding_model": r"(?m)^[ \t]+embedding_model:[ \t]*([^#\r\n \t]+)",
            "lexical_weight": r"(?m)^[ \t]+lexical_weight:[ \t]*([^#\r\n \t]+)",
            "vector_weight": r"(?m)^[ \t]+vector_weight:[ \t]*([^#\r\n \t]+)",
            "top_k": r"(?m)^[ \t]+top_k:[ \t]*([^#\r\n \t]+)",
        }.items():
            match = re.search(pattern, text)
            if not match:
                continue
            raw = match.group(1)
            if key == "enabled": qdrant[key] = raw.lower() == "true"
            elif key in {"vector_size", "top_k"}: qdrant[key] = int(raw)
            elif key in {"lexical_weight", "vector_weight"}: qdrant[key] = float(raw)
            elif key == "url" and raw.lower() in {"null", "none"}: qdrant[key] = None
            else: qdrant[key] = raw
    _CONFIG_CACHE, _CONFIG_CACHE_MTIME_NS = values, mtime
    return values


def index_path() -> Path:
    configured = str(load_config()["soc_index_path"])
    path = Path(__file__).resolve().parent / configured
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def data_path() -> Path:
    return Path(__file__).resolve().parent / str(load_config()["soc_data_path"])


def detect_intent(query: str) -> dict[str, Any]:
    """Return a deterministic intent guess and confidence.

    Confidence is intentionally conservative. A weak or ambiguous signal is
    represented as GENERAL_SECURITY so retrieval remains useful without
    pretending that an intent was established.
    """
    lowered = query.lower()
    query_terms = set(tokens(query))
    scored: list[tuple[int, int, str, list[str]]] = []
    for order, intent in enumerate(SUPPORTED_INTENTS[:-1]):
        score = 0
        matched: list[str] = []
        for signal in _INTENT_RULES[intent]:
            needle = signal.lower()
            if " " in signal or re.search(r"[^a-z0-9_.-]", signal):
                hit = needle in lowered
            else:
                hit = needle in query_terms
            if hit:
                if intent == "FALSE_POSITIVE" and needle == "false positive":
                    score += 4
                elif intent.startswith("AI_") and needle.startswith("ai "):
                    # Prefer an explicit AI-specific phrase over the
                    # corresponding generic intent when both match.
                    score += 4
                else:
                    score += 2 if " " in signal else 1
                matched.append(signal)
        scored.append((score, -order, intent, sorted(matched)))
    best_score, _, best_intent, matched = max(scored, key=lambda item: (item[0], item[1], item[2]))
    # Two points is the minimum meaningful signal; otherwise use the safe
    # general bucket and make the fallback explicit to callers.
    if best_score < 2:
        return {"intent": "GENERAL_SECURITY", "confidence": 0.2, "matched_terms": [], "fallback": True}
    confidence = min(0.98, round(0.35 + best_score / 10, 3))
    return {"intent": best_intent, "confidence": confidence, "matched_terms": matched, "fallback": False}


def _normalise_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, (list, tuple, set)):
        return [str(item) for item in value if str(item).strip()]
    return []


def normalize_document(document: Any) -> dict[str, Any] | None:
    """Validate one extensible SOC document; skip malformed content safely."""
    if not isinstance(document, dict):
        return None
    content = document.get("content")
    if not isinstance(content, str) or not content.strip():
        return None
    title = str(document.get("title", "")).strip()
    if not title:
        return None
    source = str(document.get("source", "unknown-local-source")).strip() or "unknown-local-source"
    source_url = document.get("source_url")
    if source_url is not None:
        source_url = str(source_url)
    category = str(document.get("category", "general_security")).strip() or "general_security"
    result = dict(document)
    result.update({
        "id": str(document.get("id") or hashlib.sha256(f"{source}:{title}".encode()).hexdigest()[:16]),
        "title": title,
        "category": category,
        "topic": str(document.get("topic", category)).strip() or category,
        "source": source,
        "source_url": source_url,
        # Keep the historical platform-independent contract used by callers;
        # retain a more specific scope separately for retrieval consumers.
        "platform": "any",
        "platform_scope": str(document.get("platform", "any")).strip() or "any",
        "tactic": str(document.get("tactic", "")).strip(),
        "technique": str(document.get("technique", "")).strip(),
        "severity": str(document.get("severity", "")).strip(),
        "tags": _normalise_list(document.get("tags")),
        "intents": [item for item in _normalise_list(document.get("intents")) if item in ALLOWED_INTENTS],
        "event_ids": _normalise_list(document.get("event_ids")),
        "log_source": str(document.get("log_source", "")).strip(),
        "mitre_tactic": str(document.get("mitre_tactic", document.get("tactic", ""))).strip(),
        "mitre_technique": str(document.get("mitre_technique", document.get("technique", ""))).strip(),
        "data_source": _normalise_list(document.get("data_source")),
        "investigation_phase": _normalise_list(document.get("investigation_phase")),
        "keywords": _normalise_list(document.get("keywords")),
        "related_techniques": _normalise_list(document.get("related_techniques")),
        "ai_component": str(document.get("ai_component", "")).strip(),
        "ai_architecture": str(document.get("ai_architecture", "")).strip(),
        "model_type": str(document.get("model_type", "")).strip(),
        "agent_type": str(document.get("agent_type", "")).strip(),
        "attack_surface": _normalise_list(document.get("attack_surface")),
        "attack_type": str(document.get("attack_type", "")).strip(),
        "telemetry_sources": _normalise_list(document.get("telemetry_sources")),
        "attack_status": str(document.get("attack_status", "UNKNOWN")).strip().upper(),
        "related_ai_threat": _normalise_list(document.get("related_ai_threat")),
        "related_mitre_attack": _normalise_list(document.get("related_mitre_attack")),
        "related_framework": _normalise_list(document.get("related_framework")),
        "content": content.strip(),
    })
    return result


def load_documents(path: Path | None = None) -> tuple[list[dict[str, Any]], int]:
    primary_path = path or data_path()
    paths = [primary_path]
    expanded = Path(__file__).resolve().parent / str(load_config().get("soc_expanded_data_path", ""))
    if path is None and expanded.exists():
        paths.append(expanded)
    ai_path = Path(__file__).resolve().parent / str(load_config().get("soc_ai_data_path", ""))
    if path is None and ai_path.exists():
        paths.append(ai_path)
    documents: list[dict[str, Any]] = []
    skipped = 0
    for path_item in paths:
        if not path_item.exists():
            continue
        for line in path_item.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                raw = json.loads(line)
            except json.JSONDecodeError:
                skipped += 1
                continue
            normalized = normalize_document(raw)
            if normalized is None:
                skipped += 1
            else:
                documents.append(normalized)
    return documents, skipped


def _chunks(text: str, size: int, overlap: int) -> Iterable[tuple[str, str]]:
    size = max(200, int(size))
    overlap = max(0, min(int(overlap), size // 2))
    step = max(1, size - overlap)
    for number, start in enumerate(range(0, len(text), step)):
        part = text[start:start + size].strip()
        if part:
            yield str(number), part


def _weighted_terms(document: dict[str, Any], text: str) -> Counter[str]:
    weighted = Counter(tokens(text))
    fields = (
        (document["title"], 4),
        (document["topic"], 3),
        (document["category"], 2),
        (document["tactic"], 4),
        (document["technique"], 5),
        (" ".join(document["tags"]), 2),
        (" ".join(document["intents"]), 2),
        (" ".join(document.get("event_ids", [])), 5),
        (document.get("log_source", ""), 3),
        (document.get("mitre_tactic", ""), 3),
        (document.get("mitre_technique", ""), 5),
        (" ".join(document.get("keywords", [])), 3),
        (" ".join(document.get("related_techniques", [])), 2),
        (document.get("ai_component", ""), 5),
        (document.get("ai_architecture", ""), 3),
        (document.get("model_type", ""), 3),
        (document.get("agent_type", ""), 3),
        (" ".join(document.get("attack_surface", [])), 3),
        (document.get("attack_type", ""), 4),
        (" ".join(document.get("telemetry_sources", [])), 2),
        (document.get("attack_status", ""), 2),
        (" ".join(document.get("related_ai_threat", [])), 4),
        (" ".join(document.get("related_mitre_attack", [])), 3),
        (" ".join(document.get("related_framework", [])), 3),
    )
    for value, multiplier in fields:
        for term in tokens(value):
            weighted[term] += multiplier
    return weighted


def build_index(documents: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Build an in-memory SOC index, skipping malformed records."""
    config = load_config()
    skipped = 0
    if documents is None:
        documents, skipped = load_documents()
    normalized_documents: list[dict[str, Any]] = []
    for item in documents:
        normalized = normalize_document(item)
        if normalized is None:
            skipped += 1
        else:
            normalized_documents.append(normalized)
    indexed: list[dict[str, Any]] = []
    document_frequency: Counter[str] = Counter()
    for document in normalized_documents:
        digest = hashlib.sha256(document["content"].encode("utf-8")).hexdigest()
        for chunk_id, content in _chunks(document["content"], config["soc_chunk_chars"], config["soc_chunk_overlap"]):
            terms = _weighted_terms(document, content)
            indexed.append({
                **document,
                "chunk_id": chunk_id,
                "content_hash": digest,
                "text": content,
                "terms": dict(terms),
            })
            document_frequency.update(terms.keys())
    return {
        "version": 1,
        "kind": "soc_analyst_rag",
        "document_count": len(normalized_documents),
        "chunk_count": len(indexed),
        "skipped_documents": skipped,
        "documents": indexed,
        "document_frequency": dict(document_frequency),
    }


def write_index() -> Path:
    global _INDEX_CACHE, _INDEX_CACHE_MTIME_NS, _LAST_VECTOR_STATUS
    path = index_path()
    index = build_index()
    path.write_text(json.dumps(index, indent=2), encoding="utf-8")
    qdrant_config = load_config().get("qdrant", {})
    if qdrant_config.get("enabled", False):
        _LAST_VECTOR_STATUS = VectorRetriever(qdrant_config).index(index.get("documents", []))
    else:
        _LAST_VECTOR_STATUS = {"status": VECTOR_STATUS_DISABLED}
    _INDEX_CACHE = None
    _INDEX_CACHE_MTIME_NS = None
    return path


def load_index() -> dict[str, Any]:
    global _INDEX_CACHE, _INDEX_CACHE_MTIME_NS
    path = index_path()
    source_paths = [data_path(), Path(__file__).resolve().parent / str(load_config().get("soc_expanded_data_path", "")), Path(__file__).resolve().parent / str(load_config().get("soc_ai_data_path", ""))]
    if path.exists() and any(source.exists() and source.stat().st_mtime_ns > path.stat().st_mtime_ns for source in source_paths):
        write_index()
    if not path.exists():
        write_index()
    mtime = path.stat().st_mtime_ns
    if _INDEX_CACHE is not None and _INDEX_CACHE_MTIME_NS == mtime:
        return _INDEX_CACHE
    index = json.loads(path.read_text(encoding="utf-8"))
    postings: dict[str, list[int]] = {}
    for position, document in enumerate(index.get("documents", [])):
        for term in document.get("terms", {}):
            postings.setdefault(term, []).append(position)
    index["_postings"] = postings
    _INDEX_CACHE, _INDEX_CACHE_MTIME_NS = index, mtime
    return index


def _safe_result(document: dict[str, Any], score: float) -> dict[str, Any]:
    return {
        "id": document["id"],
        "title": document["title"],
        "category": document["category"],
        "topic": document["topic"],
        "source": document["source"],
        "source_url": document.get("source_url"),
        "platform": document["platform"],
        "platform_scope": document.get("platform_scope", document["platform"]),
        "tactic": document["tactic"],
        "technique": document["technique"],
        "severity": document["severity"],
        "tags": document["tags"],
        "intents": document["intents"],
        "event_ids": document.get("event_ids", []),
        "log_source": document.get("log_source", ""),
        "mitre_tactic": document.get("mitre_tactic", ""),
        "mitre_technique": document.get("mitre_technique", ""),
        "data_source": document.get("data_source", []),
        "investigation_phase": document.get("investigation_phase", []),
        "keywords": document.get("keywords", []),
        "related_techniques": document.get("related_techniques", []),
        "ai_component": document.get("ai_component", ""),
        "ai_architecture": document.get("ai_architecture", ""),
        "model_type": document.get("model_type", ""),
        "agent_type": document.get("agent_type", ""),
        "attack_surface": document.get("attack_surface", []),
        "attack_type": document.get("attack_type", ""),
        "telemetry_sources": document.get("telemetry_sources", []),
        "attack_status": document.get("attack_status", "UNKNOWN"),
        "related_ai_threat": document.get("related_ai_threat", []),
        "related_mitre_attack": document.get("related_mitre_attack", []),
        "related_framework": document.get("related_framework", []),
        "document_type": "soc_guidance",
        "chunk_id": document["chunk_id"],
        "content_hash": document["content_hash"],
        "score": round(score, 4),
        "guidance_type": "SOC_ANALYST_RAG",
        "snippet": " ".join(document["text"].split())[:700],
    }


class LexicalRetriever:
    """Adapter exposing the existing lexical retriever as a composable component."""

    def search(self, query: str, top_k: int | None = DEFAULT_TOP_K, *, filters: dict[str, Any] | None = None, index: dict[str, Any] | None = None) -> dict[str, Any]:
        return search(query, top_k=top_k, filters=filters, index=index, mode="lexical")


class EmbeddingProvider:
    """Optional sentence-transformers adapter; absence never breaks lexical search."""

    def __init__(self, model_name: str, expected_size: int):
        self.model_name = model_name
        self.expected_size = int(expected_size)
        self._model: Any | None = None

    def _load(self) -> Any:
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def encode(self, texts: list[str]) -> list[list[float]]:
        model = self._load()
        vectors = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        result = [list(map(float, vector)) for vector in vectors]
        if result and len(result[0]) != self.expected_size:
            raise ValueError(f"embedding dimension {len(result[0])} != configured {self.expected_size}")
        return result


class VectorRetriever:
    """Qdrant-backed retriever. It is intentionally optional and failure-safe."""

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or load_config().get("qdrant", {})
        self.client: Any | None = None
        self.embedder: EmbeddingProvider | None = None
        self.error: str | None = None

    @property
    def enabled(self) -> bool:
        return bool(self.config.get("enabled", False))

    def _connect(self) -> Any:
        if self.client is not None:
            return self.client
        if not self.enabled:
            raise RuntimeError(VECTOR_STATUS_DISABLED)
        from qdrant_client import QdrantClient
        url = self.config.get("url")
        if url:
            api_key_env = str(self.config.get("api_key_env", "QDRANT_API_KEY"))
            self.client = QdrantClient(url=str(url), api_key=os.environ.get(api_key_env))
        else:
            path = Path(__file__).resolve().parent / str(self.config.get("path", ".rag/qdrant"))
            path.parent.mkdir(parents=True, exist_ok=True)
            self.client = QdrantClient(path=str(path))
        return self.client

    def _embedding(self) -> EmbeddingProvider:
        if self.embedder is None:
            self.embedder = EmbeddingProvider(str(self.config.get("embedding_model", "all-MiniLM-L6-v2")), int(self.config.get("vector_size", DEFAULT_VECTOR_SIZE)))
        return self.embedder

    def _collection_exists(self, client: Any, collection: str) -> bool:
        return any(item.name == collection for item in client.get_collections().collections)

    def ensure_collection(self) -> None:
        client = self._connect()
        collection = str(self.config.get("collection", "soc_knowledge"))
        if self._collection_exists(client, collection):
            return
        from qdrant_client.models import Distance, VectorParams
        distance = getattr(Distance, str(self.config.get("distance", "COSINE")).upper(), Distance.COSINE)
        client.create_collection(collection_name=collection, vectors_config=VectorParams(size=int(self.config.get("vector_size", DEFAULT_VECTOR_SIZE)), distance=distance))

    def index(self, indexed_documents: list[dict[str, Any]]) -> dict[str, Any]:
        """Idempotently upsert lexical chunks into Qdrant using stable UUID point IDs."""
        try:
            self.ensure_collection()
            client = self._connect()
            from qdrant_client.models import PointStruct
            texts = [str(item["text"]) for item in indexed_documents]
            vectors = self._embedding().encode(texts)
            points = []
            for item, vector in zip(indexed_documents, vectors):
                stable = f"{item['id']}:{item['chunk_id']}"
                point_id = str(uuid.uuid5(uuid.NAMESPACE_URL, stable))
                payload = {key: value for key, value in item.items() if key not in {"terms"}}
                points.append(PointStruct(id=point_id, vector=vector, payload=payload))
            client.upsert(collection_name=str(self.config.get("collection", "soc_knowledge")), points=points, wait=True)
            self.error = None
            return {"status": "INDEXED", "points": len(points), "collection": str(self.config.get("collection", "soc_knowledge"))}
        except Exception as exc:
            self.error = f"{type(exc).__name__}: {exc}"
            return {"status": "UNAVAILABLE", "points": 0, "error": self.error}

    def search(self, query: str, top_k: int, filters: dict[str, Any] | None = None) -> dict[str, Any]:
        try:
            self.ensure_collection()
            client = self._connect()
            vector = self._embedding().encode([query])[0]
            query_filter = None
            if filters:
                from qdrant_client.models import FieldCondition, Filter, MatchValue
                query_filter = Filter(must=[FieldCondition(key=key, match=MatchValue(value=value)) for key, value in filters.items()])
            collection = str(self.config.get("collection", "soc_knowledge"))
            # qdrant-client 1.x exposes ``search``; newer releases expose
            # ``query_points``. Support both without making Qdrant required.
            if hasattr(client, "query_points"):
                query_response = client.query_points(
                    collection_name=collection,
                    query=vector,
                    query_filter=query_filter,
                    limit=int(top_k),
                    with_payload=True,
                )
                hits = getattr(query_response, "points", query_response)
            else:
                hits = client.search(
                    collection_name=collection,
                    query_vector=vector,
                    query_filter=query_filter,
                    limit=int(top_k),
                    with_payload=True,
                )
            results = []
            for hit in hits:
                payload = dict(hit.payload or {})
                payload.setdefault("id", "")
                payload.setdefault("title", "")
                payload.setdefault("category", "general_security")
                payload.setdefault("topic", payload.get("category", "general_security"))
                payload.setdefault("source", "qdrant")
                payload.setdefault("source_url", None)
                payload.setdefault("platform", "any")
                payload.setdefault("tactic", "")
                payload.setdefault("technique", "")
                payload.setdefault("severity", "")
                payload.setdefault("tags", [])
                payload.setdefault("intents", [])
                payload.setdefault("event_ids", [])
                payload.setdefault("log_source", "")
                payload.setdefault("mitre_tactic", "")
                payload.setdefault("mitre_technique", "")
                payload.setdefault("data_source", [])
                payload.setdefault("investigation_phase", [])
                payload.setdefault("keywords", [])
                payload.setdefault("related_techniques", [])
                payload.setdefault("attack_type", "")
                payload.setdefault("text", "")
                payload["chunk_id"] = str(payload.get("chunk_id", "0"))
                payload["content_hash"] = str(payload.get("content_hash", ""))
                results.append(_safe_result(payload, float(hit.score)))
            self.error = None
            return {"status": "RETRIEVED", "results": results}
        except Exception as exc:
            self.error = f"{type(exc).__name__}: {exc}"
            return {"status": "UNAVAILABLE", "results": [], "error": self.error}


class HybridRetriever:
    """Fuses existing lexical results with optional Qdrant results."""

    def __init__(self, vector_retriever: VectorRetriever | None = None):
        self.vector = vector_retriever or VectorRetriever()

    def fuse(self, lexical: list[dict[str, Any]], vector: list[dict[str, Any]], query: str, top_k: int) -> list[dict[str, Any]]:
        config = load_config().get("qdrant", {})
        lexical_weight = float(config.get("lexical_weight", 0.70))
        vector_weight = float(config.get("vector_weight", 0.30))
        max_lexical = max((float(item.get("score", 0)) for item in lexical), default=1.0)
        max_vector = max((float(item.get("score", 0)) for item in vector), default=1.0)
        merged: dict[tuple[str, str], dict[str, Any]] = {}
        lowered = query.lower()
        for source, items, maximum in (("lexical", lexical, max_lexical), ("vector", vector, max_vector)):
            for item in items:
                key = (str(item.get("id", "")), str(item.get("chunk_id", "0")))
                record = merged.setdefault(key, dict(item))
                if source == "lexical":
                    record["lexical_score"] = float(item.get("score", 0))
                else:
                    record["vector_score"] = float(item.get("score", 0))
                record["score"] = lexical_weight * (float(record.get("lexical_score", 0)) / max_lexical) + vector_weight * (float(record.get("vector_score", 0)) / max_vector)
                record["retrieval_sources"] = sorted(set(record.get("retrieval_sources", [])) | {source})
        for record in merged.values():
            exact = any(value and str(value).lower() in lowered for value in (record.get("technique"), *(record.get("event_ids") or []), *(record.get("keywords") or [])))
            if exact and "lexical" in record.get("retrieval_sources", []):
                record["score"] += 0.25
        return sorted(merged.values(), key=lambda item: (-float(item.get("score", 0)), item.get("title", ""), item.get("id", "")))[:max(1, int(top_k))]


def search(query: str, top_k: int | None = DEFAULT_TOP_K, *, filters: dict[str, Any] | None = None, index: dict[str, Any] | None = None, mode: str = "auto") -> dict[str, Any]:
    """Retrieve concise SOC guidance without applying platform routing."""
    intent = detect_intent(query)
    config = load_config()
    index = index or load_index()
    max_top_k = max(1, int(config["soc_max_top_k"]))
    requested_max = max_top_k if top_k is None else max(1, min(int(top_k), max_top_k))
    filters = filters or {}
    query_terms = Counter(tokens(query))
    if not query_terms:
        return {"status": "NO_RELEVANT_CONTEXT", "intent": intent["intent"], "intent_confidence": intent["confidence"], "results": []}
    count = max(1, len(index.get("documents", [])))
    results: list[dict[str, Any]] = []
    for document in index.get("documents", []):
        if any(str(document.get(key, "")).lower() != str(value).lower() for key, value in filters.items() if value is not None and key in {"category", "topic", "source", "tactic", "technique", "severity", "platform", "ai_component", "attack_type"}):
            continue
        score = 0.0
        for term, query_frequency in query_terms.items():
            weight = float(document.get("terms", {}).get(term, 0))
            if not weight:
                continue
            inverse_frequency = math.log((count + 1) / (1 + index.get("document_frequency", {}).get(term, 0))) + 1
            score += weight * inverse_frequency * query_frequency
        if not score:
            continue
        if intent["intent"] in document.get("intents", []):
            score += 4.0
        if document.get("category") == _INTENT_CATEGORY.get(intent["intent"]):
            score += 2.0
        # Exact technique IDs and phrases are high-value analyst signals.
        lowered = query.lower()
        for field in ("technique", "title", "topic"):
            value = str(document.get(field, "")).lower()
            if value and value in lowered:
                score += 5.0
        results.append(_safe_result(document, score))
    results.sort(key=lambda item: (-item["score"], item["title"], item["source"], item["chunk_id"], item["id"]))
    if results:
        threshold = results[0]["score"] * float(config["soc_min_score_ratio"])
        results = [item for item in results if item["score"] >= threshold]
    unique: list[dict[str, Any]] = []
    used_chars = 0
    for item in results:
        if any(SequenceMatcher(None, item["snippet"], prior["snippet"]).ratio() >= float(config["soc_redundancy_threshold"]) for prior in unique):
            continue
        if unique and used_chars + len(item["snippet"]) > int(config["soc_max_context_chars"]):
            continue
        unique.append(item)
        used_chars += len(item["snippet"])
        if len(unique) >= requested_max:
            break
    response = {
        "status": "RETRIEVED" if unique else "NO_RELEVANT_CONTEXT",
        "intent": intent["intent"],
        "intent_confidence": intent["confidence"],
        "intent_matched_terms": intent["matched_terms"],
        "results": unique,
    }
    qdrant_config = load_config().get("qdrant", {})
    requested_mode = str(mode or "auto").lower()
    if requested_mode not in {"auto", "lexical", "vector", "hybrid"}:
        raise ValueError("mode must be auto, lexical, vector, or hybrid")
    if requested_mode == "vector" and not qdrant_config.get("enabled", False):
        response["results"] = []
        response["status"] = "NO_RELEVANT_CONTEXT"
        response["retrieval_mode"] = "VECTOR_UNAVAILABLE"
        response["vector_status"] = VECTOR_STATUS_DISABLED
        return response
    if requested_mode == "lexical" or not qdrant_config.get("enabled", False):
        response["retrieval_mode"] = "LEXICAL_ONLY"
        return response
    vector_result = VectorRetriever(qdrant_config).search(query, int(qdrant_config.get("top_k", requested_max)), filters=filters)
    if vector_result.get("status") != "RETRIEVED":
        if requested_mode == "vector":
            response["results"] = []
            response["status"] = "NO_RELEVANT_CONTEXT"
            response["retrieval_mode"] = "VECTOR_UNAVAILABLE"
        else:
            response["retrieval_mode"] = "LEXICAL_FALLBACK"
        response["vector_status"] = vector_result.get("status", "UNAVAILABLE")
        return response
    if requested_mode == "vector":
        response["results"] = vector_result.get("results", [])[:requested_max]
        response["status"] = "RETRIEVED" if response["results"] else "NO_RELEVANT_CONTEXT"
        response["retrieval_mode"] = "VECTOR_ONLY"
        response["vector_status"] = "RETRIEVED"
        return response
    fused = HybridRetriever().fuse(unique, vector_result.get("results", []), query, requested_max)
    deduped: list[dict[str, Any]] = []
    for item in fused:
        if any(item.get("id") == prior.get("id") and item.get("chunk_id") == prior.get("chunk_id") for prior in deduped):
            continue
        if any(SequenceMatcher(None, item.get("snippet", ""), prior.get("snippet", "")).ratio() >= float(config["soc_redundancy_threshold"]) for prior in deduped):
            continue
        deduped.append(item)
    response["results"] = deduped
    response["status"] = "RETRIEVED" if deduped else "NO_RELEVANT_CONTEXT"
    response["retrieval_mode"] = "HYBRID"
    response["vector_status"] = "RETRIEVED"
    return response


def recommend(query: str, *, evidence: list[dict[str, Any]] | None = None, top_k: int | None = DEFAULT_TOP_K, filters: dict[str, Any] | None = None) -> dict[str, Any]:
    """Retrieve SOC guidance and return unified advisory recommendations."""
    result = search(query, top_k=top_k, filters=filters)
    from recommendations import build_recommendations
    output = build_recommendations(result, evidence=evidence)
    output["retrieval_status"] = result["status"]
    output["intent"] = result["intent"]
    output["intent_confidence"] = result["intent_confidence"]
    output["retrieved_results"] = result["results"]
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Offline SOC Analyst RAG index and query tool")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("index")
    query_parser = subparsers.add_parser("search")
    query_parser.add_argument("query", nargs="+")
    query_parser.add_argument("--top-k", type=int, default=DEFAULT_TOP_K)
    query_parser.add_argument("--mode", choices=("auto", "lexical", "vector", "hybrid"), default="auto")
    recommend_parser = subparsers.add_parser("recommend")
    recommend_parser.add_argument("query", nargs="+")
    recommend_parser.add_argument("--top-k", type=int, default=DEFAULT_TOP_K)
    args = parser.parse_args()
    if args.command == "index":
        path = write_index()
        index = json.loads(path.read_text(encoding="utf-8"))
        print(json.dumps({"status": "INDEXED", "path": str(path), "documents": index["document_count"], "chunks": index["chunk_count"], "skipped": index["skipped_documents"], "vector": _LAST_VECTOR_STATUS}, indent=2))
    elif args.command == "search":
        print(json.dumps(search(" ".join(args.query), top_k=args.top_k, mode=args.mode), indent=2))
    else:
        print(json.dumps(recommend(" ".join(args.query), top_k=args.top_k), indent=2))


if __name__ == "__main__":
    main()
