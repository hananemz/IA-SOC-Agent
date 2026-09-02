"""Read-only local stage benchmark for the security-agent handoff.

Router, MCP, and Qwen are reported as NOT_MEASURABLE here because this
workspace contains no executable runtime or provider transport for them.
"""
from __future__ import annotations

import json
import statistics
import time
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import context_handoff
import skills_rag

CASES = [
    ("A-Splunk-BruteForce", "Investigate brute-force authentication activity in Splunk.", {"platform": "splunk", "task": "security_alert_triage", "skill": "splunk-security-alert-triage", "query_language": "SPL", "mcp": "splunk-mcp-server", "mcp_status": "VERIFIED"}),
    ("B-Splunk-FailedAuth", "Investigate failed authentication attempts in Splunk.", {"platform": "splunk", "task": "authentication", "skill": "splunk-authentication", "query_language": "SPL", "mcp": "splunk-mcp-server", "mcp_status": "VERIFIED"}),
    ("C-Elastic-Auth", "Investigate authentication activity in Elastic.", {"platform": "elastic", "task": "authentication", "skill": "elasticsearch-authn", "query_language": "ES|QL/KQL", "mcp": "elastic", "mcp_status": "VERIFIED"}),
    ("D-Elastic-SSH", "Investigate SSH authentication failures in Elastic.", {"platform": "elastic", "task": "authentication", "skill": "elasticsearch-authn", "query_language": "ES|QL/KQL", "mcp": "elastic", "mcp_status": "VERIFIED"}),
]


def run_case(name, request, decision, repeats=5):
    samples = []
    for _ in range(repeats):
        start = time.perf_counter_ns()
        rag_start = time.perf_counter_ns()
        rag = skills_rag.search(request, decision=decision)
        rag_ms = (time.perf_counter_ns() - rag_start) / 1e6
        context_start = time.perf_counter_ns()
        envelope = context_handoff.build_context(request, decision, rag)
        context_ms = (time.perf_counter_ns() - context_start) / 1e6
        samples.append({"rag_ms": rag_ms, "context_ms": context_ms, "total_local_ms": (time.perf_counter_ns() - start) / 1e6, "chunks": len(rag["results"]), "context_chars": len(envelope["context_text"]), "mcp_calls": "NOT_MEASURABLE", "qwen_ttft": "NOT_MEASURABLE", "qwen_generation": "NOT_MEASURABLE"})
    return {"case": name, "repeats": repeats, "measurements": samples, "averages": {key: statistics.mean(item[key] for item in samples) for key in ("rag_ms", "context_ms", "total_local_ms", "chunks", "context_chars")}}


if __name__ == "__main__":
    print(json.dumps({"status": "READ_ONLY", "cases": [run_case(*case) for case in CASES]}, indent=2))
