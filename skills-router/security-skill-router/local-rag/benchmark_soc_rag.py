"""Read-only local SOC RAG benchmark; Qwen and MCP remain unmeasured."""
from __future__ import annotations

import json
import statistics
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import context_handoff
import local_rag
import soc_rag

CASES = [
    ("suspicious PowerShell", "Investigate suspicious PowerShell execution and map it to ATT&CK.", {"platform": "elastic", "skill": "security-alert-triage", "query_language": "ES|QL", "mcp": "elastic", "mcp_status": "VERIFIED"}),
    ("Kerberoasting", "What should the analyst do after detecting Kerberoasting T1558.003?", {"platform": "elastic", "skill": "security-alert-triage", "query_language": "ES|QL", "mcp": "elastic", "mcp_status": "VERIFIED"}),
    ("authentication brute force", "Is this authentication alert likely brute force?", {"platform": "splunk", "skill": "splunk-security-alert-triage", "query_language": "SPL", "mcp": "splunk-mcp-server", "mcp_status": "VERIFIED"}),
    ("suspicious network connection", "Investigate a suspicious network connection and assess possible C2.", {"platform": "elastic", "skill": "security-alert-triage", "query_language": "ES|QL", "mcp": "elastic", "mcp_status": "VERIFIED"}),
]


def stats(values):
    return {"average": round(statistics.mean(values), 4), "minimum": round(min(values), 4), "maximum": round(max(values), 4)}


def run(repeats=5):
    indexing = []
    for _ in range(repeats):
        start = time.perf_counter_ns()
        index = soc_rag.build_index()
        indexing.append((time.perf_counter_ns() - start) / 1e6)
    cases = []
    for name, request, decision in CASES:
        samples = []
        for _ in range(repeats):
            start = time.perf_counter_ns()
            retrieval_start = time.perf_counter_ns()
            soc = soc_rag.search(request, index=index)
            retrieval_ms = (time.perf_counter_ns() - retrieval_start) / 1e6
            operational = local_rag.search(request, decision=decision)
            context_start = time.perf_counter_ns()
            envelope = context_handoff.build_context(request, decision, operational, soc_result=soc)
            context_ms = (time.perf_counter_ns() - context_start) / 1e6
            samples.append({"retrieval_ms": retrieval_ms, "context_ms": context_ms, "local_pipeline_ms": (time.perf_counter_ns() - start) / 1e6, "retrieved_documents": len(soc["results"]), "context_chars": len(envelope["context_text"]), "intent": soc["intent"]})
        cases.append({"case": name, "repeats": repeats, "measurements": samples, "summary": {key: stats([item[key] for item in samples]) for key in ("retrieval_ms", "context_ms", "local_pipeline_ms", "retrieved_documents", "context_chars")}})
    return {"status": "READ_ONLY", "repeats": repeats, "index": {"summary_ms": stats(indexing), "documents": index["document_count"], "chunks": index["chunk_count"]}, "cases": cases, "qwen_ttft": "NOT_MEASURABLE", "qwen_generation": "NOT_MEASURABLE", "mcp_cold_start": "NOT_MEASURABLE"}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
