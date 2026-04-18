# GenAI Systems Lab — Usage Guide

> A practical, step-by-step reference for using the GenAI Systems Lab portfolio app.  
> Every claim in this document has been verified against the source code.

---

## Table of Contents

1. [What This App Is](#what-this-app-is)
2. [Who This Is For](#who-this-is-for)
3. [Before You Start](#before-you-start)
4. [Setup & Local Development](#setup--local-development)
5. [Navigation](#navigation)
6. [Home Page](#home-page)
7. [About Page](#about-page)
8. [Browsing Projects](#browsing-projects)
9. [Project Detail Page](#project-detail-page)
10. [Playground — Running a Project](#playground--running-a-project)
    - [Onboarding & Quick-Start Guide](#onboarding--quick-start-guide)
    - [Selecting a Project](#selecting-a-project)
    - [API Key & Model Selection](#api-key--model-selection)
    - [Writing Input](#writing-input)
    - [Streaming vs Standard Execution](#streaming-vs-standard-execution)
    - [Execution Output](#execution-output)
    - [Memory Trace Panel](#memory-trace-panel)
    - [Execution Graph](#execution-graph)
11. [Timeline Replay](#timeline-replay)
12. [Run Explanation](#run-explanation)
13. [Run History](#run-history)
14. [Sharing a Run](#sharing-a-run)
15. [Multi-Turn Sessions](#multi-turn-sessions)
16. [Metrics Dashboard](#metrics-dashboard)
17. [Framework Comparison](#framework-comparison)
18. [Architecture Diagram](#architecture-diagram)
19. [Authentication](#authentication)
20. [Theme Toggle](#theme-toggle)
21. [Accessibility & Keyboard Navigation](#accessibility--keyboard-navigation)
22. [Environment Variables](#environment-variables)
23. [Docker Deployment](#docker-deployment)
24. [Troubleshooting](#troubleshooting)
25. [Limitations & Important Notes](#limitations--important-notes)

---

## What This App Is

GenAI Systems Lab is a full-stack portfolio application that showcases **20 production-grade AI systems** built across three paradigms: **GenAI** (custom agents), **LangGraph** (stateful graph orchestration), and **CrewAI** (role-based multi-agent collaboration).

The frontend is a Next.js 16 application built with React 19, TypeScript, and Tailwind CSS. The backend is a FastAPI server that orchestrates project execution, authentication, metrics collection, and run history.

Users can browse all 20 systems, inspect their architectures, and **run any system live in the browser** via a BYOK (Bring Your Own Key) model.

---

## Who This Is For

- **Hiring managers and technical reviewers** evaluating the portfolio
- **Engineers** interested in multi-agent architecture patterns
- **Anyone** wanting to run the AI systems hands-on with their own API key

---

## Before You Start

| Requirement | Details |
| --- | --- |
| **Browser** | Any modern browser (Chrome, Firefox, Edge, Safari) |
| **API key** | An LLM provider key — Google Gemini, OpenAI, Anthropic, or no key for Ollama (local) |
| **Backend** | The FastAPI backend running locally or at a configured URL |
| **Node.js** | Required to build/run the frontend (`npm` available) |
| **Python 3.13+** | Required to run the backend |

---

## Setup & Local Development

### 1. Start the backend

From the repository root:

```bash
uvicorn shared.api.app:app --reload
```

This starts the FastAPI server on `http://localhost:8000`.

### 2. Start the frontend

```bash
cd portfolio
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Available npm scripts

| Script | Command | Purpose |
| --- | --- | --- |
| `npm run dev` | `next dev` | Development server with hot reload (Turbopack) |
| `npm run build` | `next build` | Production build |
| `npm start` | `next start` | Serve production build |
| `npm run lint` | `eslint` | Run ESLint checks |
| `npm test` | `tsx --test src/app/playground/playground-utils.test.ts src/lib/apikey.test.ts` | Run playground utility and BYOK API-key tests |

---

## Navigation

The top navigation bar is divided into three groups:

**Primary links** (always visible):

| Label | Route | Description |
| --- | --- | --- |
| Home | `/` | Landing page |
| Projects | `/projects` | All 20 systems |
| Playground | `/playground` | Interactive execution |

**"More" dropdown** (secondary links hidden behind a disclosure menu):

| Label | Route | Description |
| --- | --- | --- |
| About | `/about` | Skills and approach |
| Metrics | `/metrics` | Performance dashboard |
| Compare frameworks | `/compare` | LangGraph vs CrewAI comparison |
| Architecture | `/architecture` | System diagram |

**Auth link** (right side):

| Label | Route | Description |
| --- | --- | --- |
| Sign in | `/auth` | Login / create account |

The active page is highlighted with a soft background. On mobile, the navigation collapses into a `<details>` disclosure menu.

---

## Home Page

**Route:** `/`

The landing page displays:

- A hero section introducing the lab and its 20 AI systems
- Aggregate stats (number of systems, paradigms, capabilities)
- Highlighted project cards
- A "Built With" section listing the tech stack (Next.js, FastAPI, LangGraph, CrewAI, etc.)
- A link to the GitHub repository
- Quick CTAs to browse Projects or open the Playground

---

## About Page

**Route:** `/about`

Displays the author's professional profile:

- **Core skills** grouped by category: Languages (Python, TypeScript, SQL), Frameworks (LangGraph, CrewAI, FastAPI, Next.js), AI/ML (LLM Integration, Multi-Agent Systems, RAG Pipelines, Prompt Engineering), Infra (Docker, OpenTelemetry, DuckDB, ChromaDB)
- **Approach cards** — three cards describing working style: Primary focus, Delivery style, and Front-end stack
- **Working approach** principles: Ship, Observe, Keep legible

---

## Browsing Projects

**Route:** `/projects`

Lists all 20 AI systems organized into **static sections by paradigm** — there are no client-side filter tabs. The three sections are:

| Paradigm | Accent color | Example systems |
| --- | --- | --- |
| **GenAI** | Emerald | Research System, NL2SQL Agent, Clinical Assistant, Financial Analyst |
| **LangGraph** | Blue | Debugging Agent, Data Analysis Agent, Support Agent |
| **CrewAI** | Violet | Hiring Crew, Investment Analyst Crew, Content Pipeline |

### Features on this page

- **Hover preview** — hovering a project card for 400 ms reveals a tooltip with the project name, a two-line description, and quick links ("Try it" → Playground, "Details" → detail page)
- **Run badges** — each card shows a live metrics badge (e.g., "87% success · 2.4s avg") fetched from the `/metrics` endpoint, when data is available

---

## Project Detail Page

**Route:** `/projects/[slug]`

Each project's detail page includes:

- **Breadcrumb navigation** — Home › Projects › {Project Name}
- **Category badge** and a **Project ID** label showing the project's slug
- **Architecture description** — how the system is designed internally
- **Interactive flow diagram** — a topologically sorted DAG of agents/nodes with:
  - Zoom in/out/reset controls
  - Drag-to-pan (grab cursor)
  - Hover highlighting of connected nodes and edges
  - Accent color per paradigm (blue, emerald, violet)
- **Feature list** — capabilities as bullet points
- **Example input/output** — formatted JSON with a **Copy** button
- **Tags** — technology and pattern labels
- **API endpoint** — the FastAPI route the system uses
- **Live demo panel** — run the project directly from the detail page

---

## Playground — Running a Project

**Route:** `/playground`

The playground is the primary interactive surface. It uses a three-column layout:

1. **Left sidebar** — project selector, input, model/key configuration, account, history
2. **Center panel** — conversation output
3. **Right panel** — execution graph, memory traces, timeline replay, explanation

### Onboarding & Quick-Start Guide

**Welcome modal** — on the first visit to the Playground, a modal appears with three numbered steps: Browse systems, Bring your API key, Run live. Click **"Get Started"** to dismiss. Tracked via `localStorage` (key: `onboarding-dismissed`); does not reappear after dismissal.

**Quick-start guide** — a collapsible "Quick start" card is shown in the sidebar on first use, listing three steps: ① Pick a project, ② Enter your API key, ③ Press Run. Dismiss it via the X button. Tracked via `localStorage` (key: `playground-guide-dismissed`).

**Recovery** — if you have dismissed the guide, a **"Show quick-start guide"** link appears in the sidebar to restore it. To reset the welcome modal, quick-start guide, and all "Don't ask again" confirmations simultaneously, click **"Help & tips"** in the page footer.

### Selecting a Project

- Use the **project dropdown** in the sidebar — the recommended project (`genai-research-system`) is pinned to the top with a "Recommended" badge
- Use the **search field** above the dropdown to filter by name
- Each project shows its category badge (GenAI / LangGraph / CrewAI)

### API Key & Model Selection

The **Model** section of the sidebar is collapsible (open by default).

- **Provider and model dropdown** — loaded from the backend's `/llm/catalog` endpoint. Models are grouped by provider (Google Gemini, OpenAI, Anthropic, Ollama). Unavailable providers show an amber warning
- **API key input** — paste your key into the field for the selected provider. The field is masked when not focused (shows only the last 3 characters). A validation error appears only **after** you interact with the field (deferred validation)
- **BYOK model** — your key is held in **browser memory only**, in a module-level variable. It is never written to `localStorage`, `sessionStorage`, or the server. The key is lost when you reload or close the page
- A **"Get API key"** link is shown for providers that expose one

### Writing Input

The **"Your input"** section of the sidebar contains:

- A resizable textarea for entering your prompt or JSON input
- **Text / JSON pill toggle** — shown for projects whose example input is a single `{"input": "string"}` field. When **Text** mode is active, you type plain text; the frontend wraps it in `{"input": "..."}` before sending. When **JSON** mode is active (default for all other projects), the textarea accepts raw JSON
- **Live JSON validation** — in JSON mode, if the input looks like JSON but is malformed, a yellow warning appears immediately. In Text mode, no JSON validation is performed
- The example input for the selected project is shown below the textarea for reference

### Streaming vs Standard Execution

Toggle **"Live streaming"** in the sidebar to control the execution mode:

| Mode | Protocol | Endpoint | Behavior |
| --- | --- | --- | --- |
| **Streaming** (default) | SSE | `GET /stream/{project}?input=...` | Per-node `step` frames update the graph in real time. Once the project finishes, a single `output` frame delivers the full completed output, followed by a `done` frame with final metrics |
| **Standard** | REST | `POST /{project}/run` | A spinner shows while the full response is assembled. Output appears all at once when complete |

The conversation panel header shows a badge — **"Streaming on"** or **"Standard"** — reflecting the active mode.

> **Note on streaming semantics.** The backend does not emit synthetic per-token chunks. Project runtimes (LangGraph, CrewAI, and the GenAI systems) complete end-to-end before the output is serialized, so streaming gives you live node-level progress plus a single honest output payload — not a token-by-token typewriter effect.

#### SSE event protocol

| Event type | Payload | Frontend effect |
| --- | --- | --- |
| `step` | `{"step": "researcher", "status": "running\|done\|error"}` | Graph node changes color |
| `output` | `{"output": "..."}` | Full completed output rendered in the conversation panel |
| `done` | `{"latency", "confidence", "success", "session_id", ...}` | Metrics finalized, graph settles |
| `error` | `{"detail": "..."}` | Friendly error message displayed |

### Execution Output

The center panel renders the conversation:

- **System message** — project description + tags (light card)
- **User message** — your input preview (dark card, max 240 characters)
- **AI message** — streamed output with a blinking cursor during streaming, or full output in standard mode
- **Key metrics pills** — extracted from the response JSON (numeric values, scores, etc.)
- **Error state** — a friendly human-readable message with an optional "Show details" toggle that reveals the raw HTTP status and technical detail

Header stats update in real time: latency (ms), confidence (%), chunk count, and a workspace state badge (Idle / Thinking / Streaming / Completed / Error).

### Memory Trace Panel

As the agent runs, memory entries appear:

| Type | Color | Icon | Label Shown |
| --- | --- | --- | --- |
| Thought | Blue | Star | Reasoning |
| Action | Orange | Arrow | Action Taken |
| Observation | Gray | Eye | Result Received |

- Entries are expandable — the last entry is expanded by default
- A timeline line on the left connects entries visually
- The panel shows the total entry count

### Execution Graph

The right panel contains collapsible sections. Two graph views are available:

1. **Run Lifecycle** — a simplified 4-step view: Planner → Executor → Evaluator → Final, showing which lifecycle phase is active
2. **Execution Flow** — the full DAG from the project's `graph` definition, with live node status transitions:
   - Gray = idle
   - Yellow = running
   - Green = done
   - Red = error

Additional collapsible cards below the graph show **Step Status**, **Parsed Steps**, and **Run Stats** (mode, session state, timing).

---

## Timeline Replay

After a run finishes (or when replaying a saved run), the **Timeline Replay** panel lets you scrub through execution events frame by frame.

### Controls

| Control | Action |
| --- | --- |
| **Play / Pause** | Auto-advance through timestamped events |
| **Previous / Next** | Step one frame backward or forward |
| **Range slider** | Drag to jump to any point in the execution (keyboard-accessible) |
| **Speed selector** | 0.5×, 1×, 1.5×, 2×, 4× |

Each frame shows the step name, event type, timestamp, and data. The execution graph and memory panel update in sync with the scrubber position.

A **dismissible tip** appears on first use explaining the controls.

---

## Run Explanation

After a run completes, click **Explain** in the history panel to generate an AI-powered summary.

The explanation request goes to `POST /explain/{runId}` and uses your current LLM settings. A loading indicator shows "Generating… this usually takes 15–30 seconds."

The explanation includes:

| Section | Content |
| --- | --- |
| **Final Outcome** | Highlighted summary of what the system produced |
| **Steps Taken** | Numbered cards — each with "what happened" and "why it mattered" |
| **Key Decisions** | Decision + reasoning pairs |
| **Final Reasoning** | The chain of thought behind the overall result |

A **dismissible tip** appears on first use.

---

## Run History

Requires [authentication](#authentication).

The sidebar's **Account** section (collapsible; opens automatically when logged in) lists up to 6 recent saved runs, each showing:

- Project name and timestamp
- Event count
- Confidence indicator (color-coded: green ≥ 75%, orange 50–75%, red < 50%)

Per-run actions:

| Button | Action |
| --- | --- |
| **Replay** | Loads the timeline and drives the graph + memory panel in sync |
| **Explain** | Generates an AI explanation (see above) |
| **Re-run** | Re-hydrates the original input and re-executes. A confirmation dialog appears; includes a "Don't ask again" option |
| **Share** | Creates or revokes a public link (see below) |

---

## Sharing a Run

Requires [authentication](#authentication).

1. Click **Share** on a saved run
2. The backend creates a public token via `POST /run/{runId}/share`
3. Optionally set an **expiry** (in hours) — the response includes an `expires_at` timestamp
4. A shareable URL is generated at `/run/{shareToken}`
5. To revoke, click the share button again — it calls `DELETE /run/{runId}/share`

**Shared run page** (`/run/[id]`):

- Displays project name, timestamp, latency, and confidence score
- Three tabs: **Output**, **Reasoning** (count of memory entries), **Execution log** (count of timeline events)
- No API key or login required for the viewer
- Handles expired links (HTTP 410) and not-found tokens (HTTP 404)

---

## Multi-Turn Sessions

Requires [authentication](#authentication).

When logged in, runs are associated with a **session**. This enables multi-turn context — the backend preserves conversation memory across runs for the same project.

- The sidebar shows session state: "Conversation active" or "No active conversation"
- A preview of up to 5 recent session memory entries is shown
- **"Start new conversation"** clears the session memory via `POST /session/{sessionId}/clear`. A confirmation dialog appears; includes a "Don't ask again" option
- The session ID is stored in `localStorage` (key: `portfolio.active-session-id`) and survives page reloads
- The stream request includes `session_id` as a query parameter to maintain context

---

## Metrics Dashboard

**Route:** `/metrics`

Track performance across all 20 systems over time.

### Stat Cards (top)

| Card | Value |
| --- | --- |
| Runs Analyzed | Total count within selected window |
| Average Latency | Formatted as ms |
| Average Confidence | Formatted as % |
| Success Rate | Formatted as % |

### Charts

Three line charts powered by Recharts:

1. **Latency Over Time** — response time in ms (downward = improving)
2. **Confidence Over Time** — 0–100% (upward = improving)
3. **Success Rate Over Time** — spans two columns, shows reliability drift

### Filters

- **Project dropdown** — "All projects" or a specific project slug
- **Time range buttons**:

| Range | Granularity |
| --- | --- |
| Last hour | 5-minute intervals |
| Last day | Hourly intervals |
| Last week | Daily intervals |

### Trend Summary

An automated directional indicator based on start-vs-end comparison:

- **Improving** (green) — latency dropped ≥ 40 ms, confidence or success rose ≥ 3%
- **Degrading** (red) — opposite movement
- **Stable** (gray) — within threshold

### Export

Two buttons at the top of the chart section:

- **Export JSON** — downloads `metrics.json` with the full `TimeSeriesMetricPoint[]` array
- **Export CSV** — downloads `metrics.csv` with a header row and one row per data point

---

## Framework Comparison

**Route:** `/compare`

A structured side-by-side comparison of the two multi-agent frameworks (linked from the nav as **"Compare frameworks"**):

| Section | Content |
| --- | --- |
| **Overview cards** | LangGraph: "Stateful orchestration" — CrewAI: "Role-based collaboration" |
| **Comparison table** | Rows for control flow, determinism, flexibility, use cases |
| **Repo examples** | Real implementations from this repo (e.g., `lg-debugging-agent` for evaluator-driven retry loops, `crew-hiring-system` for composable crew review) — each links to `/projects/{slug}` |
| **Decision guidance** | When to use LangGraph vs CrewAI, with a practical rule of thumb |

---

## Architecture Diagram

**Route:** `/architecture`

An interactive four-step diagram showing how requests flow through the system:

1. **UI** — Next.js frontend
2. **API** — FastAPI gateway
3. **Project** — per-project runtime (LangGraph, CrewAI, or GenAI)
4. **Shared Layer** — schemas, logging, LLM clients, eval, metrics

**Interactions:**

- **Hover** a box to highlight it and its immediate neighbors, with connecting arrows accented
- **Click** a box to pin its detailed description in the panel below
- The detail panel shows the box's title, subtitle, and a prose description of its role

---

## Authentication

**Route:** `/auth`

Authentication is **optional**. You can browse all pages and run projects without logging in. Authentication unlocks:

- Run history
- Multi-turn session memory
- Run sharing

### How It Works

1. Navigate to `/auth` — toggle between **Log in** and **Create account**
2. Enter email and password (minimum 8 characters — a live ✓/○ indicator shows below the field)
3. The backend sets an **HttpOnly session cookie** (never exposed to JavaScript)
4. A session marker is stored in `sessionStorage` (key: `portfolio.authenticated`) to detect the session on page load. This marker is cleared when the browser tab or window is closed
5. The session ID is stored in `localStorage` (key: `portfolio.active-session-id`) and survives tab reloads and restarts
6. Subsequent API calls include the cookie automatically via `credentials: "include"`

**Public signup** is controlled by the backend's `/auth/config` endpoint (`public_signup` flag). When disabled, only login is available.

**Logout** clears the `sessionStorage` marker, removes the `localStorage` session ID, and calls `POST /auth/logout`.

---

## Theme Toggle

Click the **sun/moon icon** in the top-right corner of the navigation bar to switch between light and dark mode.

- Theme is managed by `next-themes` and persisted in `localStorage`
- On first visit, the OS-level preference (`prefers-color-scheme`) is detected automatically
- The app uses CSS custom properties that adapt to the active theme
- A `prefers-reduced-motion: reduce` media query disables all CSS animations and transitions

---

## Accessibility & Keyboard Navigation

- All interactive elements are keyboard-accessible via Tab
- The timeline replay slider is an `<input type="range">` with an `aria-label`
- Workspace state badges use `role="status"` and `aria-live="polite"` (or `"assertive"` for errors)
- The run explanation loading region uses `aria-live="polite"`
- The architecture diagram boxes are focusable `<button>` elements
- The onboarding modal uses `role="dialog"` with `aria-modal="true"` and an `aria-label`
- Confidence tooltip uses both a `title` attribute and an `aria-label`

---

## Environment Variables

| Variable | Scope | Default | Purpose |
| --- | --- | --- | --- |
| `NEXT_PUBLIC_API_BASE_URL` | Frontend | `http://localhost:8000` | Backend API URL. When unset, the frontend tries `localhost:8000` then falls back to `127.0.0.1:8001` |
| `GENAI_SYSTEMS_LAB_ALLOWED_ORIGINS` | Backend | `localhost:3000, localhost:3001` variants | Comma-separated CORS origins. Defaults to localhost ports 3000 and 3001 |
| `APP_ENV` | Backend | `dev` | When set to `prod`, logs a warning if `GENAI_SYSTEMS_LAB_ALLOWED_ORIGINS` is not explicitly configured |

---

## Docker Deployment

The repository includes a `Dockerfile` and `docker-compose.yml` for the **backend only**.

### Dockerfile

```dockerfile
FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY shared/ shared/
COPY crew-*/ ./
COPY genai-*/ ./
COPY lg-*/ ./
COPY .env* ./
EXPOSE 8000
CMD ["uvicorn", "shared.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

### docker-compose.yml

```yaml
services:
  api:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    command: ["uvicorn", "shared.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

Start with:

```bash
docker compose up --build
```

The frontend is not included in the Docker image — run it separately with `npm run dev` or `npm run build && npm start` from the `portfolio/` directory.

---

## Troubleshooting

### "API unreachable" or connection errors

- Confirm the FastAPI backend is running on `http://localhost:8000`
- If using a custom URL, set `NEXT_PUBLIC_API_BASE_URL` before starting the frontend
- On CORS errors, ensure `GENAI_SYSTEMS_LAB_ALLOWED_ORIGINS` includes the frontend origin (defaults cover `localhost:3000` and `localhost:3001`)

### No output after clicking Run

- Verify your API key is valid and not expired
- Check the browser console (F12 → Console) for network errors
- The friendly error message in the UI includes a "Show details" toggle — expand it to see the raw HTTP status and error detail
- Try a different project to rule out project-specific issues

### Streaming seems stuck

- The SSE connection may have timed out. Refresh the page and try again
- If streaming consistently fails, uncheck "Live streaming" in the sidebar to switch to standard mode

### Rate limit errors

- The backend enforces per-endpoint rate limits. When a rate limit is hit, the UI displays a "Rate limit reached. Wait a moment and try again." message
- Wait a moment, then retry

### Shared link not loading

- The share link may have expired if an expiry was set
- The backend must be running and reachable from the viewer's network
- Expired links show "This shared link has expired" (HTTP 410)

### Theme not applying

- Clear `localStorage` for the site and reload

### Login not working

- Ensure the backend is running and the `/auth/login` endpoint is reachable
- If public signup is disabled by the backend configuration, only existing accounts can log in
- Clear cookies for the site and try again

### Dismissed tips or modals not resetting

- Click **"Help & tips"** in the page footer to reset the welcome modal, the quick-start guide, and all "Don't ask again" confirmations in one step

---

## Limitations & Important Notes

- **API key is per-session** — your key is held in a module-level browser variable. It is lost when you reload or close the page. There is no cross-tab key sharing
- **Session cookie is HttpOnly** — the auth token is never accessible to JavaScript. The frontend uses a `sessionStorage` marker to track login state; this marker clears when the tab is closed
- **Session ID persists in localStorage** — closing all tabs does not clear the session. Log out explicitly or use "Start new conversation" to reset
- **Backend required** — all execution, metrics, history, sharing, and auth features require the FastAPI backend to be running. The frontend alone only serves static project information
- **No offline mode** — the app does not cache runs or support offline execution
- **Metrics are backend-persisted** — chart data comes from the backend database. If the backend has no recorded runs, charts will be empty
