"""Small API bridge for ia-soc-frontend.

The browser never talks directly to skills, RAG, MCP, or provider secrets.
This service performs lightweight routing and RAG retrieval, then optionally
uses an OpenAI-compatible provider when OPENROUTER_API_KEY is configured.
"""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ROUTER_ROOT = ROOT / "skills-router" / "security-skill-router"
RAG_ROOT = ROUTER_ROOT / "skills-rag"
sys.path.insert(0, str(RAG_ROOT))

try:
    import skills_rag
    import soc_rag
except Exception:  # Keep health endpoint available if optional RAG imports fail.
    skills_rag = None
    soc_rag = None


HOST = os.getenv("SOCMATE_BACKEND_HOST", "127.0.0.1")
PORT = int(os.getenv("SOCMATE_BACKEND_PORT", "8787"))
ALLOWED_ORIGINS = {
    item.strip()
    for item in os.getenv(
        "SOCMATE_ALLOWED_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000",
    ).split(",")
    if item.strip()
}


def route_request(message: str, requested_platform: str | None = None) -> dict[str, Any]:
    text = message.lower()
    splunk_terms = ("splunk", "spl ", "index=", "sourcetype=", "notable event")
    elastic_terms = ("elastic", "elasticsearch", "kibana", "es|ql", "kql")
    if requested_platform in {"splunk", "elastic", "cross-platform"}:
        platform = requested_platform
    elif any(term in text for term in splunk_terms):
        platform = "splunk"
    elif any(term in text for term in elastic_terms):
        platform = "elastic"
    else:
        platform = "unknown"

    task = "search"
    task_terms = {
        "alert": "security_alert_triage",
        "incident": "case_management",
        "ticket": "case_management",
        "case": "case_management",
        "log": "logs_search",
        "audit": "audit",
        "anomal": "anomaly_detection",
        "rule": "detection_rules",
        "detect": "detection_rules",
        "dashboard": "dashboards",
        "auth": "authentication",
    }
    for term, candidate in task_terms.items():
        if term in text:
            task = candidate
            break

    if platform == "splunk":
        splunk_skills = {
            "search": "splunk-search",
            "logs_search": "splunk-logs-search",
            "security_alert_triage": "splunk-security-alert-triage",
            "case_management": "splunk-security-case-management",
            "detection_rules": "splunk-security-detection-rules",
            "anomaly_detection": "splunk-mltk-anomaly-detection",
            "audit": "splunk-audit",
            "authentication": "splunk-authentication",
            "authorization": "splunk-authorization",
            "dashboards": "splunk-dashboards",
        }
        skill = splunk_skills.get(task, "splunk-search")
        query_language = "SPL"
    elif platform == "elastic":
        elastic_skills = {
            "search": "elasticsearch-esql",
            "logs_search": "observability-logs-search",
            "security_alert_triage": "security-alert-triage",
            "case_management": "security-case-management",
            "detection_rules": "security-detection-rule-management",
            "anomaly_detection": "kibana-anomaly-detection",
            "audit": "kibana-audit",
            "authentication": "elasticsearch-authn",
            "authorization": "elasticsearch-authz",
            "dashboards": "kibana-dashboards",
        }
        skill = elastic_skills.get(task, "elasticsearch-esql")
        query_language = "ES|QL/KQL"
    else:
        skill = None
        query_language = None
    return {
        "platform": platform,
        "task": task,
        "skill": skill,
        "query_language": query_language,
        "status": "AMBIGUOUS" if platform == "unknown" else "ROUTED",
    }


def retrieve_context(message: str, decision: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if not skills_rag or not soc_rag:
        return [], []
    try:
        operational = skills_rag.search(message, top_k=4, decision=decision)
    except Exception:
        operational = {"results": []}
    try:
        soc = soc_rag.search(message, top_k=4)
    except Exception:
        soc = {"results": []}
    return operational.get("results", []), soc.get("results", [])


def provider_answer(message: str, decision: dict[str, Any], operational: list[dict[str, Any]], soc: list[dict[str, Any]]) -> str | None:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        return None
    base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1").rstrip("/")
    model = os.getenv("OPENROUTER_MODEL", "qwen/qwen3.6-27b")
    context = "\n\n".join(item.get("snippet", item.get("content", "")) for item in operational + soc)
    prompt = (
        "You are a SOC analyst assistant. Use the retrieved material as guidance only. "
        "Do not claim live provider evidence unless it is supplied. Be concise and state gaps.\n\n"
        f"Route: {json.dumps(decision)}\nRequest: {message}\nGuidance:\n{context[:9000]}"
    )
    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
    }).encode("utf-8")
    request = urllib.request.Request(
        f"{base_url}/chat/completions",
        data=payload,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            body = json.loads(response.read().decode("utf-8"))
        return body["choices"][0]["message"]["content"]
    except Exception:
        return None


def assistant_response(body: dict[str, Any]) -> dict[str, Any]:
    message = str(body.get("message", "")).strip()
    if not message:
        return {"answer": "Le message est obligatoire.", "mcp_status": "NOT_RUN"}
    decision = route_request(message, body.get("platform"))
    operational, soc = retrieve_context(message, decision)
    answer = provider_answer(message, decision, operational, soc)
    if answer is None:
        if decision["status"] == "AMBIGUOUS":
            answer = "Quelle plateforme veux-tu utiliser : Elastic ou Splunk ?"
        else:
            answer = (
                f"Requête routée vers {decision['skill']} ({decision['platform']}). "
                f"Le RAG a fourni {len(operational) + len(soc)} élément(s) de guidance. "
                "Aucune preuve live MCP n'est disponible dans ce backend."
            )
    return {
        "answer": answer,
        "intent": decision["task"],
        "platform": decision["platform"],
        "task": decision["task"],
        "skill": decision["skill"],
        "query_language": decision["query_language"],
        "mcp": None,
        "mcp_status": "NOT_CONFIGURED",
        "agent_provider": "openrouter" if os.getenv("OPENROUTER_API_KEY") else "skills-rag-fallback",
        "evidence": [],
        "sources": ["operational-rag", "soc-analyst-rag"] if operational or soc else [],
        "activities": [
            {"id": "route", "type": "routing", "text": f"Route: {decision['skill'] or 'clarification'}", "status": "success"},
            {"id": "rag", "type": "rag", "text": "RAG consulté", "status": "success"},
        ],
    }


class Handler(BaseHTTPRequestHandler):
    def _headers(self) -> None:
        origin = self.headers.get("Origin", "")
        self.send_header("Access-Control-Allow-Origin", origin if origin in ALLOWED_ORIGINS else "http://localhost:3000")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Content-Type", "application/json; charset=utf-8")

    def respond(self, status: int, payload: dict[str, Any]) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self._headers()
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self._headers()
        self.end_headers()

    def do_GET(self) -> None:
        if self.path == "/api/health":
            self.respond(200, {"status": "ok", "overall_label": "SOC backend online", "systems": {"rag": {"status": "available" if skills_rag and soc_rag else "unavailable"}}})
        elif self.path == "/api/rag/status":
            self.respond(200, {"status": "available" if skills_rag and soc_rag else "unavailable", "documents": 0})
        elif self.path == "/api/dashboard/overview":
            self.respond(200, {"alerts": 0, "investigations": 0, "threats": 0, "status": "connected"})
        elif self.path in {"/api/alerts", "/api/investigations", "/api/incidents", "/api/threat-feed", "/api/improvement-proposals", "/api/feedback/history"}:
            self.respond(200, {"items": [], "results": [], "events": []})
        elif self.path == "/api/platform-health":
            self.respond(200, {"systems": {"elastic": {"status": "not_configured"}, "splunk": {"status": "not_configured"}}})
        else:
            self.respond(404, {"error": "Not found"})

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        try:
            body = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            self.respond(400, {"error": "Invalid JSON"})
            return
        if self.path == "/api/assistant":
            self.respond(200, assistant_response(body))
        elif self.path == "/api/feedback":
            self.respond(200, {"ok": True})
        else:
            self.respond(404, {"error": "Not found"})

    def log_message(self, format: str, *args: Any) -> None:
        print(f"[{self.log_date_time_string()}] {format % args}")


if __name__ == "__main__":
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"IA SOC backend listening on http://{HOST}:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
