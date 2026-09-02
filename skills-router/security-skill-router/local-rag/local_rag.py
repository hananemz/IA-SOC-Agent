"""Offline retrieval for complementary operational knowledge.

The Agent/Skills system owns platform selection, skill selection and loading of
SKILL.md. This module only retrieves curated operational context after that
decision; it never discovers or loads skills.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

TOKEN_RE = re.compile(r"[a-z0-9_]{2,}")
DEFAULT_TOP_K = None
DEFAULT_MAX_TOP_K = 8
DEFAULT_MIN_SCORE_RATIO = 0.35
DEFAULT_REDUNDANCY_THRESHOLD = 0.92
DEFAULT_MAX_CONTEXT_CHARS = 6000
DEFAULT_DATA_PATH = "operational-knowledge/documents.jsonl"
DEFAULT_INDEX_PATH = ".rag/operational-index.json"
_INDEX_CACHE: dict[str, Any] | None = None
_INDEX_CACHE_MTIME_NS: int | None = None
_CONFIG_CACHE: dict[str, Any] | None = None
_CONFIG_CACHE_MTIME_NS: int | None = None


def tokens(text: str) -> list[str]:
    return TOKEN_RE.findall(text.lower())


def workspace_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _config_path() -> Path:
    return Path(__file__).resolve().parent / "config.yaml"


def data_path() -> Path:
    configured = str(load_config().get("operational_data_path", DEFAULT_DATA_PATH))
    return Path(__file__).resolve().parent / configured


def index_path() -> Path:
    configured = str(load_config().get("operational_index_path", DEFAULT_INDEX_PATH))
    path = Path(__file__).resolve().parent / configured
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def load_config() -> dict[str, Any]:
    """Read retrieval limits without adding a YAML dependency."""
    global _CONFIG_CACHE, _CONFIG_CACHE_MTIME_NS
    path = _config_path()
    mtime = path.stat().st_mtime_ns if path.exists() else None
    if _CONFIG_CACHE is not None and _CONFIG_CACHE_MTIME_NS == mtime:
        return _CONFIG_CACHE
    values: dict[str, Any] = {
        "operational_enabled": True,
        "operational_max_top_k": DEFAULT_MAX_TOP_K,
        "operational_min_score_ratio": DEFAULT_MIN_SCORE_RATIO,
        "operational_redundancy_threshold": DEFAULT_REDUNDANCY_THRESHOLD,
        "operational_max_context_chars": DEFAULT_MAX_CONTEXT_CHARS,
    }
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    aliases = {"operational_max_top_k": "max_top_k", "operational_min_score_ratio": "min_score_ratio", "operational_redundancy_threshold": "redundancy_threshold", "operational_max_context_chars": "max_context_chars"}
    for key in values:
        match = re.search(rf"(?m)^\s*{re.escape(key)}:\s*([^#\s]+)", text)
        if not match and key in aliases:
            match = re.search(rf"(?m)^\s*{aliases[key]}:\s*([^#\s]+)", text)
        if not match:
            continue
        raw = match.group(1).lower()
        if raw in {"true", "false"}:
            values[key] = raw == "true"
        else:
            try:
                values[key] = float(raw) if "." in raw else int(raw)
            except ValueError:
                pass
    _CONFIG_CACHE, _CONFIG_CACHE_MTIME_NS = values, mtime
    return values


def _list(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value] if value.strip() else []
    return [str(item) for item in value] if isinstance(value, list) else []


def _normalise(raw: Any) -> dict[str, Any] | None:
    if not isinstance(raw, dict) or not isinstance(raw.get("content"), str):
        return None
    title = str(raw.get("title", "")).strip()
    if not title or not raw["content"].strip():
        return None
    result = dict(raw)
    result.update({"id": str(raw.get("id") or hashlib.sha256(title.encode()).hexdigest()[:16]), "title": title, "platform": str(raw.get("platform", "any")).strip() or "any", "topic": str(raw.get("topic", "general")).strip() or "general", "type": str(raw.get("type", "operational_knowledge")).strip() or "operational_knowledge", "related_skills": _list(raw.get("related_skills")), "content": raw["content"].strip(), "source": str(raw.get("source", "local operational knowledge")).strip()})
    return result


def load_documents(path: Path | None = None) -> list[dict[str, Any]]:
    path = path or data_path()
    if not path.exists():
        return []
    documents = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            document = _normalise(json.loads(line))
        except json.JSONDecodeError:
            document = None
        if document:
            documents.append(document)
    return documents


def build_index(documents: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Build exclusively from operational JSONL; SKILL.md is never read."""
    indexed, frequency = [], Counter()
    for document in documents if documents is not None else load_documents():
        document = _normalise(document)
        if not document:
            continue
        searchable = " ".join([document["title"], document["topic"], document["type"], " ".join(document["related_skills"]), document["content"]])
        terms = Counter(tokens(searchable))
        indexed.append({**document, "terms": dict(terms), "content_hash": hashlib.sha256(document["content"].encode()).hexdigest()})
        frequency.update(terms.keys())
    return {"version": 2, "kind": "operational_knowledge_rag", "documents": indexed, "document_frequency": dict(frequency)}


def write_index() -> Path:
    global _INDEX_CACHE, _INDEX_CACHE_MTIME_NS
    path = index_path()
    path.write_text(json.dumps(build_index(), indent=2, ensure_ascii=False), encoding="utf-8")
    _INDEX_CACHE = None
    _INDEX_CACHE_MTIME_NS = None
    return path


def load_index() -> dict[str, Any]:
    global _INDEX_CACHE, _INDEX_CACHE_MTIME_NS
    path = index_path()
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


def search(query: str, top_k: int | None = DEFAULT_TOP_K, decision: dict[str, Any] | None = None, *, skill_context: str = "") -> dict[str, Any]:
    """Retrieve advisory context using the already-selected router decision."""
    decision = decision or {"platform": "unknown"}
    platform = decision.get("platform", "unknown")
    if not load_config()["operational_enabled"] or platform in {"unknown", None} or decision.get("status") == "AMBIGUOUS":
        return {"status": "AMBIGUOUS", "platform": "unknown", "skill": decision.get("skill"), "results": []}
    index, config = load_index(), load_config()
    maximum = max(1, int(config["operational_max_top_k"]))
    requested = maximum if top_k is None else max(1, min(int(top_k), maximum))
    selected_skill = decision.get("skill")
    query_terms = Counter(tokens(query))
    allowed = {"elastic", "splunk"} if platform == "cross-platform" else {platform}
    candidates = []
    for position, document in enumerate(index.get("documents", [])):
        if document.get("platform") not in allowed | {"any"}:
            continue
        related = set(document.get("related_skills", []))
        if selected_skill and related and selected_skill not in related:
            continue
        candidates.append(position)
    matching = {position for term in query_terms for position in index.get("_postings", {}).get(term, [])}
    count = max(1, len(index.get("documents", [])))
    results = []
    for position in candidates:
        if position not in matching:
            continue
        document = index["documents"][position]
        score = 0.0
        for term, frequency in query_terms.items():
            if term in document.get("terms", {}):
                inverse = math.log((count + 1) / (1 + index["document_frequency"].get(term, 0))) + 1
                score += (1 + math.log(document["terms"][term])) * inverse * frequency
        if score:
            safe = {key: document.get(key) for key in ("id", "title", "platform", "topic", "type", "related_skills", "source", "content_hash")}
            results.append({**safe, "score": round(score, 4), "snippet": " ".join(document["content"].split())[:500]})
    results.sort(key=lambda item: (-item["score"], item["platform"], item["id"]))
    if results:
        threshold = results[0]["score"] * float(config["operational_min_score_ratio"])
        results = [item for item in results if item["score"] >= threshold]
    unique, used = [], 0
    redundancy = float(config["operational_redundancy_threshold"])
    skill_text = " ".join(skill_context.split())
    for result in results:
        snippet = result["snippet"]
        if skill_text and (snippet.lower() in skill_text.lower() or SequenceMatcher(None, snippet, skill_text).ratio() >= redundancy):
            continue
        if any(SequenceMatcher(None, snippet, prior["snippet"]).ratio() >= redundancy for prior in unique):
            continue
        if unique and used + len(snippet) > int(config["operational_max_context_chars"]):
            continue
        unique.append(result)
        used += len(snippet)
        if len(unique) >= requested:
            break
    return {"status": "RETRIEVED" if unique else "NO_RELEVANT_CONTEXT", "platform": platform, "skill": selected_skill, "role": "advisory operational context", "results": unique}


def main() -> None:
    parser = argparse.ArgumentParser(description="Offline Operational Knowledge RAG")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("index")
    search_parser = subparsers.add_parser("search")
    search_parser.add_argument("query", nargs="+")
    search_parser.add_argument("--top-k", type=int, default=DEFAULT_TOP_K)
    search_parser.add_argument("--platform", choices=["elastic", "splunk", "cross-platform"], default="unknown")
    search_parser.add_argument("--skill", default=None)
    args = parser.parse_args()
    if args.command == "index":
        print(json.dumps({"status": "INDEXED", "kind": "operational_knowledge_rag", "path": str(write_index())}))
    else:
        decision = {"platform": args.platform}
        if args.skill:
            decision["skill"] = args.skill
        print(json.dumps({"status": "OK", "query": " ".join(args.query), "results": search(" ".join(args.query), args.top_k, decision)}, indent=2))


if __name__ == "__main__":
    main()
