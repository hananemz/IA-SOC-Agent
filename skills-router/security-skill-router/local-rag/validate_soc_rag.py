"""Offline quality checks for the SOC Analyst corpus and generated index."""
from __future__ import annotations
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import soc_rag
import recommendations

REQUIRED = {"id", "title", "category", "topic", "source", "source_url", "platform", "tactic", "technique", "severity", "tags", "intents", "content", "event_ids", "log_source", "mitre_tactic", "mitre_technique", "data_source", "investigation_phase", "keywords", "related_techniques"}
AI_REQUIRED = {"ai_component", "ai_architecture", "model_type", "agent_type", "attack_surface", "telemetry_sources", "attack_status", "related_ai_threat", "related_mitre_attack", "related_framework"}
AI_STATUS = {"NOT_CONFIRMED", "ATTEMPTED", "BLOCKED", "PARTIALLY_SUCCESSFUL", "SUCCESSFUL", "UNKNOWN"}
AI_FRAMEWORK_PREFIXES = ("OWASP LLM", "OWASP Top 10 for LLM Applications", "MITRE ATLAS")
MITRE = re.compile(r"^T\d{4}(?:\.\d{3})?$")

def main() -> int:
    index = soc_rag.build_index()
    docs = index["documents"]
    errors = []
    qdrant = soc_rag.load_config().get("qdrant", {})
    for key in ("enabled", "collection", "vector_size", "distance", "embedding_model", "lexical_weight", "vector_weight", "top_k"):
        if key not in qdrant: errors.append(f"qdrant config missing {key}")
    if abs(float(qdrant.get("lexical_weight", 0)) + float(qdrant.get("vector_weight", 0)) - 1.0) > 0.001: errors.append("qdrant score weights must sum to 1")
    if int(qdrant.get("vector_size", 0)) <= 0: errors.append("qdrant vector_size must be positive")
    ids = [d["id"] for d in docs]
    if len(set(ids)) != index["document_count"]: errors.append("duplicate document IDs")
    keys = [(d["id"], d["chunk_id"]) for d in docs]
    if len(keys) != len(set(keys)): errors.append("duplicate document/chunk keys")
    for d in docs:
        missing = REQUIRED - set(d)
        if missing: errors.append(f"{d.get('id')}: missing {sorted(missing)}")
        if any(x not in soc_rag.ALLOWED_INTENTS for x in d["intents"]): errors.append(f"{d['id']}: invalid intent")
        for value in [d["technique"], d["mitre_technique"], *d["related_techniques"]]:
            if value and not MITRE.fullmatch(value): errors.append(f"{d['id']}: invalid ATT&CK ID {value}")
        if d["category"] == "ai_security":
            missing_ai = AI_REQUIRED - set(d)
            if missing_ai: errors.append(f"{d['id']}: missing AI metadata {sorted(missing_ai)}")
            if d.get("attack_status") not in AI_STATUS: errors.append(f"{d['id']}: invalid attack_status")
            for value in d.get("related_mitre_attack", []):
                if not MITRE.fullmatch(value): errors.append(f"{d['id']}: invalid AI ATT&CK ID {value}")
            for value in d.get("related_framework", []):
                if not value.startswith(AI_FRAMEWORK_PREFIXES): errors.append(f"{d['id']}: unrecognized AI framework {value}")
    if index["document_count"] != len(set(ids)): errors.append("document_count mismatch")
    if index["chunk_count"] != len(docs): errors.append("chunk_count mismatch")
    for path in (soc_rag.data_path(), HERE / str(soc_rag.load_config()["soc_expanded_data_path"]), HERE / str(soc_rag.load_config()["soc_ai_data_path"])):
        if path.exists():
            for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if line.strip():
                    try: json.loads(line)
                    except json.JSONDecodeError as exc: errors.append(f"{path.name}:{n}: {exc}")
    for item in recommendations.build_recommendations({"status": "NO_RELEVANT_CONTEXT", "results": []})["recommendations"]:
        if item.get("priority") not in recommendations.PRIORITIES: errors.append("invalid recommendation priority")
        if item.get("type") not in recommendations.TYPES: errors.append("invalid recommendation type")
    if not isinstance(recommendations.build_recommendations({"status": "NO_RELEVANT_CONTEXT", "results": []})["recommendations"], list): errors.append("recommendations must be a list")
    for category in ("windows_analysis", "malware_analysis", "network_analysis", "authentication", "cloud_security", "phishing", "web_api", "ai_security", "false_positive", "detection_engineering"):
        sample = {"status": "RETRIEVED", "results": [{"category": category, "topic": category, "snippet": category}]}
        output = recommendations.build_recommendations(sample)
        if not isinstance(output.get("recommendations"), list) or not output["recommendations"]:
            errors.append(f"no recommendations for {category}")
    print(json.dumps({"status": "PASS" if not errors else "FAIL", "documents": index["document_count"], "chunks": index["chunk_count"], "errors": errors}, indent=2))
    return 0 if not errors else 1

if __name__ == "__main__": raise SystemExit(main())
