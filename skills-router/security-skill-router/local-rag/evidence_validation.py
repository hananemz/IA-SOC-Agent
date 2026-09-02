"""Deterministic validation of provider evidence before LLM reasoning.

This module never queries a provider and never creates an event.  Claims are
derived only from fields present in the supplied records, or evaluated against
those records when explicitly supplied by the caller.
"""
from __future__ import annotations

import re
from typing import Any

PROVEN, SUPPORTED, INFERRED, UNKNOWN, MISSING_EVIDENCE = (
    "PROVEN", "SUPPORTED", "INFERRED", "UNKNOWN", "MISSING_EVIDENCE"
)
STATUSES = (PROVEN, SUPPORTED, INFERRED, UNKNOWN, MISSING_EVIDENCE)

_FIELD_ALIASES = {
    "host": ("host.name", "host", "host_name", "dest_host"),
    "user": ("user.name", "user", "user_name", "src_user", "account.name"),
    "process": ("process.name", "process", "process_name", "Image"),
    "command_line": ("process.command_line", "command_line", "cmdline", "CommandLine"),
    "timestamp": ("@timestamp", "timestamp", "_time", "event.created"),
}
_CAPABILITIES = {
    "process": {"process execution", "user", "host", "command line", "timestamp"},
    "alert": {"alert occurrence", "alert metadata", "timestamp"},
    "network": {"network connection", "source/destination", "timestamp"},
    "authentication": {"authentication activity", "user", "host", "timestamp"},
}
_MISSING_FOR = {
    "network": ["network telemetry", "proxy/firewall logs"],
    "exfiltration": ["network telemetry", "proxy/firewall logs", "DLP telemetry"],
    "persistence": ["startup/persistence telemetry", "endpoint configuration evidence"],
    "endpoint impact": ["endpoint telemetry", "file/process impact evidence"],
    "malicious intent": ["user/business context", "threat intelligence or corroborating telemetry"],
}


def _value(record: dict[str, Any], names: tuple[str, ...]) -> Any:
    for name in names:
        # Elastic commonly returns ECS fields as flat keys (for example
        # ``process.name``), while other callers provide nested dictionaries.
        # Preserve support for both representations without inventing values.
        if name in record and record[name] is not None and record[name] != "":
            return record[name]
        current: Any = record
        for part in name.split("."):
            if not isinstance(current, dict):
                current = None
                break
            current = current.get(part)
        if current is not None and current != "":
            return current
    return None


def _ref(index: int, record: dict[str, Any]) -> str:
    supplied = record.get("evidence_ref") or record.get("id") or record.get("_id")
    return str(supplied) if supplied else f"EVIDENCE-{index}"


def _claim(claim: str, status: str, refs: list[str], reason: str, missing: list[str] | None = None) -> dict[str, Any]:
    return {"claim": claim, "status": status, "evidence_refs": refs, "reason": reason, "missing_evidence": list(missing or [])}


def _kind(record: dict[str, Any]) -> str:
    text = " ".join(str(record.get(key, "")) for key in ("kind", "event.kind", "type", "category", "process", "process.name")).lower()
    if any(word in text for word in ("network", "connection", "dns", "flow")) or _value(record, ("destination.ip", "dest_ip", "network.direction")) is not None:
        return "network"
    if any(word in text for word in ("auth", "logon", "login")):
        return "authentication"
    if any(word in text for word in ("alert", "detection", "rule")):
        return "alert"
    if _value(record, _FIELD_ALIASES["process"]) is not None or _value(record, _FIELD_ALIASES["command_line"]) is not None:
        return "process"
    return "unknown"


def source_capabilities(evidence: list[dict[str, Any]], platform: str | None = None) -> dict[str, Any]:
    """Describe observed source capability, without claiming absent telemetry."""
    kinds = sorted({_kind(item) for item in evidence if isinstance(item, dict) and _kind(item) != "unknown"})
    capabilities = sorted({cap for kind in kinds for cap in _CAPABILITIES[kind]})
    limitations = ["network connection", "data exfiltration", "complete endpoint impact", "malicious intent"]
    return {"platform": platform or "unknown", "observed_event_types": kinds, "can_establish": capabilities, "cannot_establish_automatically": limitations}


def _requested_claim(claim: str, records: list[tuple[str, dict[str, Any]]]) -> dict[str, Any]:
    lowered = claim.lower()
    if any(word in lowered for word in ("exfiltrat", "outbound data", "data theft")):
        refs = [ref for ref, item in records if _kind(item) == "network"]
        if refs:
            return _claim(claim, SUPPORTED, refs, "Network evidence is present, but transfer of data is not directly established.", _MISSING_FOR["exfiltration"])
        return _claim(claim, UNKNOWN, [], "Current evidence shows no network telemetry establishing an outbound connection.", _MISSING_FOR["exfiltration"])
    if "network" in lowered or "connection" in lowered:
        refs = [ref for ref, item in records if _kind(item) == "network"]
        return _claim(claim, PROVEN if refs else UNKNOWN, refs, "A network event is directly represented in the returned evidence." if refs else "No network event is represented in the returned evidence.", [] if refs else _MISSING_FOR["network"])
    if any(word in lowered for word in ("persistence", "startup")):
        refs = [ref for ref, item in records if any(word in str(item).lower() for word in ("persistence", "startup", "run key", "scheduled task"))]
        return _claim(claim, PROVEN if refs else UNKNOWN, refs, "Persistence telemetry is present." if refs else "Process evidence alone does not establish persistence.", [] if refs else _MISSING_FOR["persistence"])
    if "endpoint" in lowered and "impact" in lowered:
        refs = [ref for ref, item in records if any(word in str(item).lower() for word in ("impact", "file.delete", "isolation", "quarantine"))]
        return _claim(claim, PROVEN if refs else UNKNOWN, refs, "Endpoint impact telemetry is present." if refs else "The returned process evidence does not establish endpoint impact.", [] if refs else _MISSING_FOR["endpoint impact"])
    if "malicious intent" in lowered or "malicious" in lowered or "suspicious" in lowered:
        refs = [ref for ref, _ in records]
        return _claim(claim, INFERRED if refs else UNKNOWN, refs, "The behavior may be suspicious, but intent is not directly observed.", _MISSING_FOR["malicious intent"])
    return _claim(claim, UNKNOWN, [], "The requested claim cannot be validated from the available evidence.", ["telemetry specific to this claim"])


def validate_evidence(evidence: list[dict[str, Any]] | None = None, claims: list[str] | None = None, platform: str | None = None) -> dict[str, Any]:
    """Return claims, provenance, capabilities, and conservative confidence."""
    raw = list(evidence or [])
    malformed = sum(1 for item in raw if not isinstance(item, dict) or not item)
    records = [(_ref(index, item), item) for index, item in enumerate(raw, 1) if isinstance(item, dict) and item]
    output: list[dict[str, Any]] = []
    fields = ("host", "user", "process", "command_line", "timestamp")
    labels = {"host": "Host", "user": "User", "process": "Process", "command_line": "Command line", "timestamp": "Timestamp"}
    for field in fields:
        found = [(ref, _value(item, _FIELD_ALIASES[field])) for ref, item in records]
        found = [(ref, value) for ref, value in found if value is not None]
        if not found:
            continue
        values = {str(value) for _, value in found}
        if len(values) > 1:
            output.append(_claim(f"{labels[field]} was observed", UNKNOWN, [ref for ref, _ in found], "Conflicting values were returned for this field; the value cannot be resolved from current evidence."))
        else:
            output.append(_claim(f"{labels[field]} was {next(iter(values))}", PROVEN, [ref for ref, _ in found], "The field is directly present in provider output."))
    process_refs = [ref for ref, item in records if _kind(item) == "process"]
    if process_refs:
        output.insert(0, _claim("Process execution was observed", PROVEN, process_refs, "A process name or command line is directly present in provider output."))
        if len(process_refs) > 1:
            output.append(_claim("Process execution is corroborated by multiple evidence items", SUPPORTED, process_refs, "Multiple returned provider records independently describe process activity."))
        output.append(_claim("The activity may be suspicious", INFERRED, process_refs, "Suspicion is an interpretation of observed execution, not a directly observed fact.", _MISSING_FOR["malicious intent"]))
    requested = [_requested_claim(str(claim), records) for claim in (claims or []) if str(claim).strip()]
    output.extend(requested)
    if not output:
        output.append(_claim("The requested security conclusions are not established", UNKNOWN, [], "No valid evidence records were returned.", ["relevant provider telemetry"]))
    statuses = {item["status"] for item in output}
    confidence = "HIGH" if statuses <= {PROVEN} else "MEDIUM" if PROVEN in statuses or SUPPORTED in statuses else "LOW" if INFERRED in statuses else "UNKNOWN"
    if malformed and confidence == "HIGH":
        confidence = "MEDIUM"
    return {"claims": output, "capabilities": source_capabilities([item for _, item in records], platform), "evidence_confidence": confidence, "malformed_evidence_count": malformed, "evidence_count": len(records)}


def format_summary(result: dict[str, Any]) -> str:
    """Compact, explicit handoff text for the final reasoning model."""
    grouped = {status: [] for status in STATUSES}
    for item in result.get("claims", []):
        grouped.setdefault(item.get("status", UNKNOWN), []).append(item)
    lines = ["EVIDENCE SUMMARY"]
    for status in STATUSES:
        lines.append(f"{status}:")
        for item in grouped[status]:
            refs = ", ".join(item.get("evidence_refs", [])) or "none"
            lines.append(f"- {item.get('claim', '')} [refs: {refs}] — {item.get('reason', '')}")
            if item.get("missing_evidence"):
                lines.append(f"  missing: {', '.join(item['missing_evidence'])}")
    lines.extend([f"EVIDENCE CONFIDENCE: {result.get('evidence_confidence', 'UNKNOWN')}", "IMPORTANT: Do not make claims stronger than the evidence supports."])
    return "\n".join(lines)
