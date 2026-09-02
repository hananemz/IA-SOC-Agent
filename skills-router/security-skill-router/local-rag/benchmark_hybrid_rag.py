"""Compare lexical, vector-only, and hybrid SOC retrieval modes.

Vector and hybrid rows report unavailable when Qdrant or the embedding model
is not configured; lexical measurements remain valid in that case.
"""
from __future__ import annotations

import json
import time

import soc_rag


QUERIES = (
    "10.10.10.50",
    "T1059.001 suspicious PowerShell",
    "agent was tricked by malicious instructions hidden inside a document",
    "agent unexpectedly invoked a privileged tool",
    "abnormal token consumption",
)
EXPECTED = {
    "10.10.10.50": ("10.10.10.50",),
    "T1059.001 suspicious PowerShell": ("T1059.001", "PowerShell"),
    "agent was tricked by malicious instructions hidden inside a document": ("prompt", "injection", "RAG"),
    "agent unexpectedly invoked a privileged tool": ("agent", "tool", "agency"),
    "abnormal token consumption": ("token", "API"),
}


def run() -> dict:
    rows = []
    for query in QUERIES:
        row = {"query": query}
        for mode in ("lexical", "vector", "hybrid"):
            started = time.perf_counter()
            try:
                result = soc_rag.search(query, top_k=6, mode=mode)
                row[mode] = {
                    "status": result.get("status"),
                    "retrieval_mode": result.get("retrieval_mode"),
                    "titles": [item.get("title") for item in result.get("results", [])],
                    "latency_ms": round((time.perf_counter() - started) * 1000, 3),
                    "expected_term_hit": any(any(term.lower() in str(item).lower() for term in EXPECTED[query]) for item in [item.get("title", "") + " " + item.get("snippet", "") for item in result.get("results", [])]),
                }
            except Exception as exc:
                row[mode] = {"status": "ERROR", "error": f"{type(exc).__name__}: {exc}"}
        rows.append(row)
    metrics = {}
    for mode in ("lexical", "vector", "hybrid"):
        values = [row[mode] for row in rows if row[mode].get("status") == "RETRIEVED"]
        metrics[mode] = {
            "retrieved_queries": len(values),
            "expected_term_hit_rate": round(sum(bool(item.get("expected_term_hit")) for item in values) / len(values), 3) if values else None,
            "mean_latency_ms": round(sum(item.get("latency_ms", 0) for item in values) / len(values), 3) if values else None,
        }
    return {"queries": rows, "metrics": metrics, "qdrant": soc_rag.load_config().get("qdrant", {})}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
