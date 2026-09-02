# IA SOC backend

Small API-only bridge for `ia-soc-frontend`. It does not contain a dashboard.

## Start

```powershell
cd C:\Users\lenovo\.agents\ia-soc-backend
.\start.ps1
```

The frontend already targets `http://127.0.0.1:8787` through
`NEXT_PUBLIC_API_BASE_URL`.

The backend provides `/api/assistant`, `/api/health`, `/api/rag/status`, and
compatible data routes. It uses the local operational and SOC RAG modules.
Set `OPENROUTER_API_KEY` to enable an OpenAI-compatible Qwen response; without
it, the API remains usable with deterministic routing and RAG fallback.

Live Elastic/Splunk MCP evidence is deliberately not fabricated. MCP adapters
can be added behind this API later without exposing credentials to the browser.
