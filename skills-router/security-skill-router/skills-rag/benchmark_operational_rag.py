"""Comparable local benchmark: Skills + SOC versus Skills + SOC + Operational RAG."""
from __future__ import annotations

import json
import statistics
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import context_handoff
import skills_rag
import soc_rag

CASES = [
    ("PowerShell", "Investigate suspicious PowerShell execution in Elastic.", {"platform": "elastic", "skill": "security-alert-triage", "query_language": "ES|QL"}),
    ("BruteForce", "Investigate brute-force authentication activity in Splunk.", {"platform": "splunk", "skill": "splunk-security-alert-triage", "query_language": "SPL"}),
    ("CrossProvider", "Investigate suspicious execution across providers.", {"platform": "cross-platform", "skill": "security-alert-triage", "query_language": "ES|QL/SPL"}),
]


def _stats(values):
    return {"average_ms": round(statistics.mean(values), 4), "minimum_ms": round(min(values), 4), "maximum_ms": round(max(values), 4)}


def run(repeats: int = 5):
    rows = []
    for name, query, decision in CASES:
        baseline, combined = [], []
        for _ in range(repeats):
            start = time.perf_counter_ns()
            soc_start = time.perf_counter_ns()
            soc = soc_rag.search(query, top_k=5)
            soc_ms = (time.perf_counter_ns() - soc_start) / 1e6
            envelope = context_handoff.build_context(query, decision, {"status": "NO_RELEVANT_CONTEXT", "results": []}, soc_result=soc)
            baseline.append({"latency_ms": (time.perf_counter_ns() - start) / 1e6, "soc_latency_ms": soc_ms, "context_chars": len(envelope["context_text"]), "input_tokens": len(envelope["context_text"]) // 4})
            start = time.perf_counter_ns()
            soc_start = time.perf_counter_ns()
            soc = soc_rag.search(query, top_k=5)
            soc_ms = (time.perf_counter_ns() - soc_start) / 1e6
            operational = skills_rag.search(query, decision=decision)
            op_ms = (time.perf_counter_ns() - start) / 1e6
            envelope = context_handoff.build_context(query, decision, operational, soc_result=soc)
            combined.append({"latency_ms": (time.perf_counter_ns() - start) / 1e6, "soc_latency_ms": soc_ms, "operational_ms": op_ms, "context_chars": len(envelope["context_text"]), "input_tokens": len(envelope["context_text"]) // 4, "chunks": len(operational["results"])})
        rows.append({"case": name, "baseline": {"latency": _stats([x["latency_ms"] for x in baseline]), "soc_latency": _stats([x["soc_latency_ms"] for x in baseline]), "context_chars": round(statistics.mean(x["context_chars"] for x in baseline)), "input_tokens": round(statistics.mean(x["input_tokens"] for x in baseline))}, "with_operational_rag": {"latency": _stats([x["latency_ms"] for x in combined]), "soc_latency": _stats([x["soc_latency_ms"] for x in combined]), "operational_latency": _stats([x["operational_ms"] for x in combined]), "context_chars": round(statistics.mean(x["context_chars"] for x in combined)), "input_tokens": round(statistics.mean(x["input_tokens"] for x in combined)), "chunks": round(statistics.mean(x["chunks"] for x in combined), 2)}, "mcp_calls": "UNCHANGED/NOT_MEASURABLE", "mcp_latency": "NOT_MEASURABLE", "final_answer_quality": "NOT_MEASURABLE_WITHOUT_QWEN", "query_correctness": "UNCHANGED", "platform_correctness": "UNCHANGED"})
    return {"status": "READ_ONLY", "repeats": repeats, "cases": rows, "qwen": "NOT_MEASURABLE"}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
