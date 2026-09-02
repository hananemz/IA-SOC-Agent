"""Evidence-first, retrieval-aware SOC recommendation synthesis.

This module only produces advisory structured output. It never executes
containment, remediation, credential changes, or provider mutations.
"""
from __future__ import annotations

from typing import Any

PRIORITIES = ("CRITICAL", "HIGH", "MEDIUM", "LOW", "INFORMATIONAL")
TYPES = ("INVESTIGATION", "EVIDENCE_COLLECTION", "CORRELATION", "MONITORING", "CONTAINMENT", "REMEDIATION", "ESCALATION", "PREVENTION", "NEXT_ACTION")


def _rec(priority: str, kind: str, action: str, reason: str) -> dict[str, str]:
    return {"priority": priority, "type": kind, "action": action, "reason": reason}


def _knowledge(soc_result: dict[str, Any]) -> tuple[str, str, str]:
    items = soc_result.get("results", []) if isinstance(soc_result, dict) else []
    category = str(items[0].get("category", "")) if items else ""
    topic = " ".join(str(item.get("topic", "")) for item in items[:4]).lower()
    text = " ".join(str(item.get("snippet", "")) for item in items[:4]).lower()
    return category, topic, text


def build_recommendations(
    soc_result: dict[str, Any] | None,
    *,
    evidence: list[dict[str, Any]] | None = None,
    alert_category: str | None = None,
) -> dict[str, Any]:
    """Create conservative recommendations from retrieved SOC guidance.

    Retrieved knowledge selects the recommendation family; evidence controls
    confidence and gaps. No recommendation is represented as an observed fact.
    """
    soc_result = soc_result or {}
    evidence = list(evidence or [])
    category, topic, text = _knowledge(soc_result)
    category = (alert_category or category).lower()
    has_knowledge = bool(soc_result.get("results"))
    confidence = "MEDIUM" if evidence and has_knowledge else ("LOW" if has_knowledge else "UNKNOWN")
    verdict = "SUSPICIOUS" if has_knowledge else "UNKNOWN"
    attack_status = "UNKNOWN"
    for item in soc_result.get("results", []):
        if item.get("category") == "ai_security" and item.get("attack_status"):
            attack_status = str(item["attack_status"])
            break

    evidence_gaps = [] if evidence else [
        "Alert payload and raw event fields are not available from current evidence.",
        "Affected asset, identity, timestamp, and scope require confirmation.",
    ]
    facts = [f"{len(evidence)} evidence item(s) were supplied for analysis."] if evidence else []
    recommendations: list[dict[str, str]] = []
    if not has_knowledge:
        recommendations = [
            _rec("MEDIUM", "EVIDENCE_COLLECTION", "Clarify the alert, affected system, source, timestamp, identity, and initial scope.", "No sufficiently relevant SOC guidance was retrieved."),
            _rec("LOW", "CORRELATION", "Retrieve the relevant endpoint, identity, network, cloud, application, or AI telemetry before classifying the event.", "The category and impact are not established from current evidence."),
            _rec("INFORMATIONAL", "NEXT_ACTION", "Reclassify the alert after additional evidence and relevant knowledge are available.", "Unknown alerts should not receive unsupported remediation claims."),
        ]
    elif category in {"false_positive"}:
        recommendations = [
            _rec("MEDIUM", "INVESTIGATION", "Validate the alert semantics, triggering fields, asset/user ownership, and approved business context.", "A false-positive disposition requires evidence of benign cause."),
            _rec("LOW", "CORRELATION", "Compare the activity with historical baseline and related alerts before tuning or suppressing it.", "Rarity alone is not enough to suppress a detection."),
            _rec("LOW", "PREVENTION", "Document any narrowly scoped tuning with an owner, expiry, and validation criteria.", "Broad suppression can hide real activity."),
        ]
    elif category in {"detection_engineering", "siem_workflow"}:
        recommendations = [
            _rec("MEDIUM", "INVESTIGATION", "Verify the rule logic, field semantics, time window, data coverage, and triggering event.", "Detection behavior must be reproducible before it is changed."),
            _rec("MEDIUM", "MONITORING", "Compare precision, volume, baseline, and suppression behavior across representative benign and suspicious cases.", "Validation reduces both missed detections and noisy alerts."),
            _rec("LOW", "PREVENTION", "Apply narrowly scoped tuning or exceptions only with documented ownership, expiry, and rollback.", "Detection changes are consequential and require change control."),
        ]
    elif category in {"ioc_analysis"}:
        recommendations = [
            _rec("MEDIUM", "INVESTIGATION", "Validate the indicator type, source, first/last-seen time, reputation context, and confidence.", "An IOC hit is a lead, not proof of compromise."),
            _rec("MEDIUM", "CORRELATION", "Search endpoint, DNS, proxy, authentication, email, and cloud telemetry for related activity and affected scope.", "Independent observations determine whether the indicator is relevant."),
            _rec("LOW", "MONITORING", "Monitor future sightings with an expiry and provenance for the indicator.", "Stale or shared indicators can create false positives."),
        ]
    elif category in {"incident_response", "risk_assessment"}:
        recommendations = [
            _rec("HIGH", "INVESTIGATION", "Summarize facts, impact, privilege, asset criticality, data sensitivity, timeline, and explicit evidence gaps.", "Response priority should reflect verified impact and scope."),
            _rec("HIGH", "CORRELATION", "Search for persistence, lateral movement, additional identities/assets, and related alerts across the incident window.", "Incident scope must be established before containment decisions."),
            _rec("HIGH", "ESCALATION", "Escalate when unauthorized success, active impact, persistence, lateral movement, sensitive-data exposure, or expanding scope is confirmed.", "Suspicion without impact does not automatically establish critical severity."),
        ]
    elif category in {"windows_analysis", "endpoint", "windows", "sysmon", "investigation", "execution"} or any(x in topic + text for x in ("process", "sysmon", "powershell", "endpoint")):
        recommendations = [
            _rec("HIGH", "INVESTIGATION", "Review the parent/child process tree, command line, user context, signer, and file hash.", "The retrieved endpoint guidance treats suspicious execution as requiring corroboration."),
            _rec("MEDIUM", "CORRELATION", "Correlate process creation with network connections, persistence, authentication, and similar execution on other endpoints.", "Related telemetry tests execution, spread, and baseline hypotheses."),
            _rec("MEDIUM", "EVIDENCE_COLLECTION", "Collect the relevant endpoint and security events with their time window and query coverage.", "Missing or zero-row telemetry is an evidence gap, not proof of absence."),
            _rec("HIGH", "CONTAINMENT", "Consider host isolation only if malicious execution, lateral movement, or active impact is corroborated and an authorized response workflow approves it.", "Suspicious execution alone does not confirm compromise."),
        ]
    elif category in {"malware", "malware_analysis"} or "malware" in topic + text:
        recommendations = [
            _rec("HIGH", "INVESTIGATION", "Verify the detection source, affected file, execution status, process tree, hash, signer, and persistence.", "A malware detection does not by itself prove successful execution."),
            _rec("MEDIUM", "CORRELATION", "Search for related network communications, authentication activity, lateral movement, and the same hash or behavior elsewhere.", "Scope and impact require independent corroboration."),
            _rec("HIGH", "EVIDENCE_COLLECTION", "Preserve the alert, file metadata, endpoint timeline, and forensic evidence before cleanup where policy permits.", "Evidence may be lost after remediation."),
            _rec("HIGH", "CONTAINMENT", "Consider containing the affected host when execution or active spread is confirmed through an authorized workflow.", "Containment is a recommendation, not an automatic action."),
        ]
    elif category in {"network_analysis", "network", "command_and_control"} or any(x in topic + text for x in ("network", "destination", "dns", "proxy", "beacon")):
        recommendations = [
            _rec("MEDIUM", "INVESTIGATION", "Validate destination reputation, DNS resolution, protocol, port, TLS context, owning process, timing, and transfer direction.", "An unusual destination or one connection is not proof of malicious activity."),
            _rec("MEDIUM", "CORRELATION", "Correlate firewall, proxy, DNS, flow, endpoint, and historical baseline data; search for other hosts contacting the destination.", "Independent signals improve confidence and scope."),
            _rec("LOW", "MONITORING", "Monitor repeated connections, periodicity, volume changes, and related process or staging activity.", "Behavior over time helps distinguish business traffic from abuse or C2 hypotheses."),
            _rec("HIGH", "CONTAINMENT", "Consider blocking or isolating only when destination, process, and impact evidence converge and authorization is present.", "Reputation or rarity alone does not justify destructive action."),
        ]
    elif category in {"authentication", "identity", "authentication_analysis"} or any(x in topic + text for x in ("logon", "login", "authentication", "credential", "account")):
        recommendations = [
            _rec("HIGH", "INVESTIGATION", "Review successful and failed logins, source IP/geography, MFA events, logon type, device, and user baseline.", "A failed burst or unusual login is not automatically account compromise."),
            _rec("MEDIUM", "CORRELATION", "Search for privilege changes, session activity, password resets, other affected accounts, and successful follow-on access.", "Corroboration distinguishes user error, automation, and abuse."),
            _rec("MEDIUM", "EVIDENCE_COLLECTION", "Preserve identity-provider, authentication, VPN, endpoint, and authorization decisions for the full time window.", "The full session context is required to assess impact."),
            _rec("HIGH", "CONTAINMENT", "Consider revoking credentials or sessions only when unauthorized access is confirmed and an authorized identity workflow approves it.", "Credential reset is not justified by failed attempts alone."),
        ]
    elif category in {"cloud", "cloud_security", "cloud_analysis"} or any(x in topic + text for x in ("cloud", "iam", "api call", "access key", "region")):
        recommendations = [
            _rec("HIGH", "INVESTIGATION", "Review cloud audit logs, IAM activity, privilege changes, access keys, source context, region, and resource ownership.", "Unexpected cloud activity needs authorization and change-context verification."),
            _rec("MEDIUM", "CORRELATION", "Correlate resource creation, policy changes, authentication, key use, and related accounts or workloads.", "Scope and persistence may span multiple cloud services."),
            _rec("HIGH", "CONTAINMENT", "Consider restricting permissions or revoking a credential only after unauthorized use is confirmed through an authorized workflow.", "Do not disrupt legitimate production activity based on rarity alone."),
        ]
    elif category in {"phishing", "email_security"} or any(x in topic + text for x in ("phishing", "email", "attachment", "sender")):
        recommendations = [
            _rec("MEDIUM", "INVESTIGATION", "Inspect sender authentication, message headers, URLs, attachments, recipients, clicks, and execution telemetry in a safe analysis path.", "Message appearance alone does not prove delivery or compromise."),
            _rec("MEDIUM", "CORRELATION", "Search for other recipients, related messages, clicks, downloads, process execution, and authentication changes.", "Campaign scope and impact require recipient and endpoint correlation."),
            _rec("HIGH", "CONTAINMENT", "Consider blocking confirmed malicious indicators and resetting credentials only if credential compromise is confirmed through authorized workflows.", "Avoid broad blocking or resets on unverified indicators."),
        ]
    elif category in {"web_api", "api_security", "web", "api"} or any(x in topic + text for x in ("api", "http", "web request", "endpoint access")):
        recommendations = [
            _rec("MEDIUM", "INVESTIGATION", "Review request patterns, authentication context, source IP, endpoint, status/error rates, and request volume against baseline.", "An unusual request does not establish abuse without context."),
            _rec("MEDIUM", "CORRELATION", "Correlate identity, session, API key, WAF/proxy, application errors, and downstream changes.", "Correlation tests credential misuse and application impact."),
            _rec("MEDIUM", "CONTAINMENT", "Consider rate limiting or restricting a credential only when active abuse is corroborated and an authorized workflow approves it.", "Mitigation should be proportionate to verified impact."),
        ]
    elif category == "ai_security" or any(x in topic + text for x in ("prompt", "rag", "agent", "token", "model", "vector")):
        recommendations = [
            _rec("MEDIUM", "INVESTIGATION", "Review prompt/session metadata, model and policy decisions, RAG retrieval/provenance, tool authorization, and agent behavior.", "AI signals require context; suspicious text or a tool call alone is not proof of compromise."),
            _rec("MEDIUM", "CORRELATION", "Correlate user/tenant identity, request and retrieval IDs, document changes, tool results, authorization, DLP, and token baseline.", "Correlation distinguishes attempted attacks from successful impact."),
            _rec("HIGH", "CONTAINMENT", "Consider restricting an agent tool, quarantining a suspicious knowledge document, or disabling an abused key only when impact is corroborated and approved.", "AI containment remains advisory and must not be automated silently."),
        ]
    else:
        recommendations = [
            _rec("MEDIUM", "INVESTIGATION", "Confirm the alert semantics, affected asset, identity, timestamp, source, and expected baseline behavior.", "Retrieved guidance is relevant but the category-specific impact is not fully established."),
            _rec("LOW", "CORRELATION", "Retrieve adjacent authentication, endpoint, network, application, and audit telemetry appropriate to the alert.", "Cross-source evidence can reduce uncertainty without assuming compromise."),
        ]

    return {
        "verdict": verdict,
        "confidence": confidence,
        "attack_status": attack_status,
        "facts": facts,
        "evidence": evidence,
        "evidence_gaps": evidence_gaps,
        "benign_hypotheses": ["Legitimate administrative, automated, testing, or business activity remains possible until corroborated."],
        "malicious_hypotheses": ["Unauthorized, abusive, or compromised activity is a hypothesis requiring supporting evidence."],
        "investigation_steps": [item["action"] for item in recommendations if item["type"] in {"INVESTIGATION", "EVIDENCE_COLLECTION"}],
        "correlation_opportunities": [item["action"] for item in recommendations if item["type"] == "CORRELATION"],
        "recommended_containment": [item["action"] for item in recommendations if item["type"] == "CONTAINMENT"],
        "recommendations": recommendations,
        "next_actions": [item["action"] for item in recommendations if item["type"] in {"NEXT_ACTION", "INVESTIGATION", "EVIDENCE_COLLECTION"}],
        "escalation_criteria": ["Escalate on confirmed unauthorized access, successful impact, sensitive-data exposure, persistence, lateral movement, material service impact, or expanding scope."],
        "retrieval_aware": has_knowledge,
        "knowledge_sources": [str(item.get("title", "")) for item in soc_result.get("results", [])[:4] if item.get("title")],
    }
