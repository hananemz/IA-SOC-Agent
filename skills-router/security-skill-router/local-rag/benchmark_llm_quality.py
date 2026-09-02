"""Live Qwen A/B quality and latency check; no MCP calls."""
from __future__ import annotations
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "dashboard"))
import context_handoff
import local_rag
import soc_rag
from services.qwen import QwenProvider

CASES = [
    ("PowerShell", "Investigate suspicious PowerShell execution in Elastic.", {"platform": "elastic", "skill": "security-alert-triage", "query_language": "ES|QL"}, ["PowerShell", "parent", "evidence"]),
    ("BruteForce", "Investigate brute-force authentication activity in Splunk.", {"platform": "splunk", "skill": "splunk-security-alert-triage", "query_language": "SPL"}, ["authentication", "source", "baseline"]),
    ("TelemetryGap", "Troubleshoot missing PowerShell script-block telemetry in Elastic.", {"platform": "elastic", "skill": "security-alert-triage", "query_language": "ES|QL"}, ["missing", "telemetry", "evidence"]),
]

def run():
    provider = QwenProvider()
    output = []
    for name, query, decision, expected in CASES:
        soc = soc_rag.search(query, top_k=5)
        variants = []
        for label, operational in (("without_operational_rag", {"status": "NO_RELEVANT_CONTEXT", "results": []}), ("with_operational_rag", local_rag.search(query, decision=decision))):
            envelope = context_handoff.build_context(query, decision, operational, soc_result=soc)
            response = provider.complete(user_request=query, context=envelope["context_text"])
            answer = response.get("answer", "")
            variants.append({"variant": label, "status": response.get("status"), "model": response.get("model", provider.model), "latency_ms": response.get("latency_ms"), "context_chars": len(envelope["context_text"]), "answer": answer, "quality_proxies": {"platform_present": decision["platform"] in answer.lower(), "expected_terms": {term: term.lower() in answer.lower() for term in expected}, "evidence_boundary_present": any(marker in answer.lower() for marker in ("evidence", "observed", "not available", "telemetry"))}})
        output.append({"case": name, "query": query, "variants": variants, "mcp_calls": 0})
    return {"model": provider.model, "cases": output}

if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
