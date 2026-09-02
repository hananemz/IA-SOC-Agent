# Sekera Services Frontend (SOC IA Agent Platform)

Sekera Services is a next-generation Security Operations Center (SOC) frontend interface powered by the SOC backend (RAG + Model Context Protocol, with Qwen/OpenRouter by default or Codex CLI as an optional provider).

## Tech Stack

- **Framework**: Next.js 16 (App Router)
- **Language**: TypeScript
- **Styling**: TailwindCSS (Dark theme, neon purple accents, glassmorphic cards)
- **Icons**: Lucide React
- **Charts**: Recharts

---

## Project Structure

```tree
sekera-frontend/
├── app/
│   ├── admin/             # User management & MCP connectors config
│   ├── ai-gym/            # Skills router sandbox & evaluation (supports negative feedback filter)
│   ├── ai-performance/    # Agent accuracy, latency metrics & Feedback Summary block
│   ├── alerts/            # Ingested alerts table & raw payloads
│   ├── clients/           # Multi-tenant SOC tenant list
│   ├── correlations/      # Multi-vector correlation chains
│   ├── iocs/              # Indicators of compromise table
│   ├── notifications/     # Notification center
│   ├── playbooks/         # Playbook templates CRUD
│   ├── review-queue/      # Human validation queue for agent actions
│   ├── tickets/           # Ticket management, investigation workspace & timeline feedback
│   ├── globals.css        # Global dark theme styling & custom scrollbars
│   ├── layout.tsx         # Root layout & global Agent Chat floating widget
│   └── page.tsx           # Overview Dashboard
├── components/
│   ├── AgentChatPanel.tsx # Interactive real-time chat with Codex CLI agent
│   ├── Header.tsx         # Top navigation bar with dynamic user profile & initials
│   └── Sidebar.tsx        # Collapsible neon sidebar navigation
└── lib/
    ├── api.ts             # Centralized API client with JSDoc backend endpoints
    └── auth.ts            # Dynamic session & initials calculation helpers
```

---

## Getting Started

### Prerequisites
- Node.js (v18+ recommended)
- npm or yarn

### Installation & Running

1. Clone or navigate to the project directory:
   ```bash
   cd socmate-frontend
   ```

2. Install dependencies:
   ```bash
   npm.cmd install
   ```

3. Run the development server:
   ```bash
   npm.cmd run dev
   ```

4. Open [http://localhost:3000](http://localhost:3000) in your browser.

For the focused question-and-answer interface, open
[http://localhost:3000/chat](http://localhost:3000/chat). The chat page is only
an interface: it sends the text to the backend and renders the returned agent
answer. MCP access and Codex execution remain server-side.

---

## Backend Integration & REST/WebSocket Endpoints

The frontend is intentionally only a client. It sends the question to the SOC
API and renders the returned answer; it must not contain MCP credentials,
OpenRouter keys, or Codex configuration.

Start the local backend first:

```powershell
cd C:\Users\lenovo\.agents\skills-router\security-skill-router\dashboard
    .\start-backend.ps1
```

The checked-in `.env.example` points the frontend to this API. Keep provider
credentials in the backend terminal only. The API accepts the frontend origins
`http://localhost:3000` and `http://127.0.0.1:3000` by default; override them
with `SOC_DASHBOARD_ALLOWED_ORIGINS` when needed.

To make `/api/assistant` use a separate, ephemeral local Codex CLI process
instead of the default Qwen/OpenRouter provider, start the backend with:

```powershell
$env:CODEX_HOME = 'C:\Users\lenovo\.codex'
$env:SOC_AGENT_PROVIDER = 'codex'
.\start-backend.ps1
```

This creates a new `codex exec` process per request, not a connection to the
already-open chat conversation. It loads the Codex configuration from
`CODEX_HOME` and runs with read-only shell access.

All data flows through `lib/api.ts`. The current local backend exposes these
routes:

- `GET /api/health`, `/api/dashboard/overview`, `/api/alerts`,
  `/api/investigations`, `/api/threat-feed`, `/api/platform-health`, and
  `/api/rag/status`.
- `POST /api/assistant` with `{ message, investigation_id?, platform? }`.
  The response contains the answer, routing metadata, verified evidence, and
  redacted Codex execution events when available.
- `POST /api/feedback` and `GET /api/feedback/history` for analyst feedback.
- `GET /api/improvement-proposals` and the approval route documented by the
  backend README.

The current login screen is only a local UI guard; it is not a production
authentication system. Add a real identity layer before exposing the service
outside the local machine.
