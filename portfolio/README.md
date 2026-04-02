# GenAI Systems Lab — Portfolio

An interactive portfolio and live execution environment for 20 production-grade AI systems, built with Next.js 16, React 19, and Tailwind CSS v4.

---

## Overview

This is not a static project gallery. The portfolio is a full-featured frontend that connects to a shared FastAPI backend and lets users **run any of the 20 AI systems directly from the browser**. It streams execution output token-by-token via SSE, visualizes agent state as an animated directed graph, records memory traces and timeline events, and displays performance metrics for every system.

Every project belongs to one of three paradigms:

| Paradigm | Count | Pattern |
| --- | --- | --- |
| **GenAI** | 10 | Custom LLM pipelines (RAG, code gen, clinical reasoning) |
| **LangGraph** | 5 | Stateful graph-based orchestration with conditional routing |
| **CrewAI** | 5 | Role-based multi-agent collaboration with staged handoffs |

Users supply their own Google Gemini API key (BYOK). The key stays in in-memory client state for the current tab and is sent per-request via the `X-API-Key` header — the server never persists it.

---

## Features

### Interactive Playground

- **SSE streaming** — tokens arrive in real time via `text/event-stream`; a batch fallback is available when streaming is unsupported
- **Animated execution graph** — a topologically-sorted DAG renders node status (`idle` → `running` → `done` / `error`) and active edges as the system executes
- **Memory trace panel** — displays `thought`, `action`, and `observation` entries emitted by the agent during a run
- **Timeline replay** — frame-by-frame scrubbing through timestamped execution events with play/pause controls
- **Run explanation** — a post-hoc LLM-generated summary of what each step did and why key decisions were made
- **Run sharing** — generate a public link (with optional expiry) that renders the full output, memory, and timeline for any run

### Project Catalog

- 20 project detail pages generated from a shared JSON manifest (`src/data/project-catalog.json`) with a typed TypeScript facade in `src/data/projects.ts`
- Each page renders: architecture description, flow diagram, feature list, example I/O, tags, and a live demo panel
- Category badges with per-paradigm accent theming (GenAI = emerald, LangGraph = blue, CrewAI = violet)

### Performance Metrics

- Time-series charts (Recharts) for latency, confidence, and success rate
- Three time ranges: last hour (5-min buckets), last day (hourly), last week (daily)
- Per-project filtering with trend analysis and automated summary generation backed by persisted execution metrics

### LangGraph vs CrewAI Comparison

- Side-by-side technical comparison across control flow, determinism, flexibility, and use cases
- Linked to concrete implementations from the repository (e.g., `lg-debugging-agent` for evaluator-driven retry loops)

### Authentication & Sessions

- JWT-based API auth with HttpOnly cookie-backed browser sessions
- Persistent run sessions for multi-turn conversations — session context carries across runs
- Run history with per-user filtering

### Design System

- Full light/dark theme via 100+ CSS custom properties with `next-themes`
- Four surface levels: `card`, `panel`, `panel-strong`, `pill`
- Button system: `primary`, `secondary`, `ghost`, `danger` × `sm`, `base`, `lg` × `pill`, `icon`
- Typography: Manrope (headings/body), IBM Plex Mono (code/data)
- Glassmorphic backgrounds: gradient orbs, grid overlay, backdrop blur

---

## Tech Stack

| Layer | Technology | Version |
| --- | --- | --- |
| Framework | Next.js (App Router, Turbopack) | 16.2.1 |
| UI | React | 19.2.4 |
| Language | TypeScript (strict mode) | 5.x |
| Styling | Tailwind CSS v4 + PostCSS | 4.x |
| Charts | Recharts | 3.8.1 |
| Theming | next-themes | 0.4.x |
| Linting | ESLint + eslint-config-next | 9.x |
| Backend | FastAPI (separate process) | — |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Browser (Next.js)                        │
│                                                                 │
│   page.tsx / playground-client.tsx / extracted sidebar + hooks   │
│       ↓                                                         │
│   src/lib/api.ts  ──→  fetch / SSE stream                      │
│       │                    │                                    │
│       │  X-API-Key header  │  Bearer JWT or HttpOnly cookie     │
│       └────────────────────┘                                    │
│                                                                 │
│   src/lib/apikey.ts   (BYOK in tab memory only)                 │
│   src/lib/auth.ts     (session marker only; no raw JWT storage) │
│   src/lib/session.ts  (session ID in localStorage)              │
└──────────────────────┬──────────────────────────────────────────┘
                       │  HTTP / SSE
                       ▼
┌──────────────────────────────────────────────────────────────────┐
│                     FastAPI Backend (:8000)                       │
│                                                                  │
│  POST /{project}/run          — batch execution                  │
│  GET  /stream/{project}       — SSE token streaming              │
│  GET  /metrics, /metrics/time — aggregate + time-series metrics  │
│  POST /auth/signup, /login    — authentication                   │
│  GET  /history                — per-user run history             │
│  POST /run/{id}/share         — shareable link generation        │
│  GET  /shared/{token}         — public run viewer                │
│  POST /explain/{id}           — post-hoc run explanation         │
│  GET  /session/{id}           — session state                    │
└──────────────────────────────────────────────────────────────────┘
```

**Data flow for a playground run:**

1. User selects a project and enters input in the playground
2. `streamProject()` opens an SSE connection to `GET /stream/{project}?input=...`
3. The server emits `step` events (node entering/exiting), `message` events (tokens), and a final `done` event with latency/confidence/session metadata
4. `dispatchStreamEvent()` routes each SSE frame to the appropriate callback: `onStep` updates the animated graph, `onToken` appends to the output buffer, `onDone` finalizes the run
5. Memory and timeline data from the response populate the debug panels
6. Optionally, the user can request an AI-generated explanation or share the run via a public link

---

## Project Structure

```
portfolio/
├── src/
│   ├── app/
│   │   ├── layout.tsx              # Root layout: nav, footer, theme provider
│   │   ├── page.tsx                # Home: hero, stats, capabilities
│   │   ├── globals.css             # Design system: 100+ CSS variables, surfaces, buttons
│   │   ├── theme-provider.tsx      # next-themes wrapper
│   │   ├── playground/
│   │   │   ├── page.tsx                   # Playground route (metadata)
│   │   │   ├── playground-client.tsx      # Main playground orchestrator
│   │   │   ├── playground-sidebar.tsx     # Input, account, and history sidebar
│   │   │   ├── playground-widgets.tsx     # Extracted presentational components
│   │   │   ├── playground-utils.ts        # Pure replay/status/memory helpers
│   │   │   ├── playground-utils.test.ts   # Unit tests for playground utilities
│   │   │   ├── use-playground-run.ts      # Run execution and SSE streaming hook
│   │   │   └── use-playground-account.ts  # Auth, session, and history hook
│   │   ├── projects/
│   │   │   ├── page.tsx            # Project listing with category filter
│   │   │   └── [slug]/
│   │   │       ├── page.tsx        # Project detail (SSG with generateStaticParams)
│   │   │       ├── project-demo.tsx  # Inline live demo widget
│   │   ├── metrics/page.tsx        # Time-series performance charts
│   │   ├── compare/page.tsx        # LangGraph vs CrewAI comparison
│   │   ├── architecture/           # Interactive architecture diagram
│   │   ├── auth/page.tsx           # Signup / login forms
│   │   ├── about/page.tsx          # Bio, skills, approach
│   │   └── run/[id]/page.tsx       # Shared run viewer
│   ├── components/
│   │   ├── animated-graph.tsx      # Live DAG with topo layout + node status
│   │   ├── agent-graph.tsx         # Static agent lifecycle visualization
│   │   ├── flow-diagram.tsx        # Topologically-sorted component flow
│   │   ├── confidence-indicator.tsx # Visual confidence score
│   │   ├── memory-panel.tsx        # thought / action / observation trace
│   │   ├── TimelineReplay.tsx      # Frame-by-frame replay controls
│   │   ├── RunExplanation.tsx      # LLM-generated run explanation
│   │   ├── card.tsx                # Reusable surface card
│   │   └── theme-toggle.tsx        # Dark/light toggle
│   ├── data/
│   │   ├── project-catalog.json    # Shared project manifest consumed by frontend + backend
│   │   └── projects.ts             # Typed frontend facade over the shared manifest
│   └── lib/
│       ├── api.ts                 # API client: fetch, stream, auth, sharing
│       ├── apikey.ts              # BYOK key state for the active tab only
│       ├── auth.ts                # Browser auth-session marker only
│       └── session.ts             # Session ID persistence
├── public/                        # Static assets (SVG icons)
├── package.json
├── next.config.ts                 # Turbopack configuration
├── tailwind.config.js             # Dark mode: class strategy
├── tsconfig.json                  # Strict mode, path aliases (@/*)
├── eslint.config.mjs              # ESLint 9 flat config + next/core-web-vitals
└── postcss.config.mjs             # @tailwindcss/postcss plugin
```

---

## Setup & Installation

### Prerequisites

- **Node.js** ≥ 18
- **npm** (or pnpm / yarn)
- A running instance of the GenAI Systems Lab FastAPI backend on `http://localhost:8000` (required for live features)

### Install

```bash
cd portfolio
npm install
```

### Development

```bash
npm run dev
```

Opens at [http://localhost:3000](http://localhost:3000). Hot-reloads via Turbopack.

### Production Build

```bash
npm run build
npm start
```

### Lint

```bash
npm run lint
```

### Environment

No `.env` file is required. The BYOK API key is kept in memory for the active tab, the browser auth marker lives in `sessionStorage`, the raw JWT stays server-managed via an HttpOnly cookie, and the backend URL defaults to `http://localhost:8000` unless `NEXT_PUBLIC_API_BASE_URL` is set.

---

## Usage

### Running a Project

1. Navigate to **Playground** (`/playground`)
2. Select a project from the sidebar dropdown (e.g., `genai-research-system`)
3. Enter your Google Gemini API key — it stays in memory for the current tab and is sent as `X-API-Key`
4. Type an input prompt and press **Run**
5. Watch tokens stream in, the agent graph animate node-by-node, and memory entries accumulate

### Viewing Project Details

Navigate to **Projects** → click any card → view architecture, flow diagram, features, example I/O, and run the live demo.

### Sharing a Run

After a run completes in the playground, click **Share** → a public URL is generated at `/run/{shareToken}`. Optionally set an expiry (in hours).

### Metrics Dashboard

Navigate to **Metrics** → select a project and time range → view latency, confidence, and success rate time-series charts with trend summaries.

---

## The 20 Systems

### GenAI Pipelines (10)

| System | Core Pattern |
| --- | --- |
| Multi-Agent Research | Planner → Researcher → Critic → Writer → Editor → Formatter |
| NL2SQL Agent | Schema Loader → SQL Generator → Validator → Executor → Summarizer |
| Clinical Decision Support | Extractor → Retriever → Reasoner → Formatter |
| Browser Agent | Observe → Plan → Act → Memory loop |
| Financial Analyst | Metric Engine → Trend Analyzer → Forecaster → Report Writer |
| Codebase Copilot | Indexer → Vector Store → Retriever → Generator |
| Document Intelligence | Chunker → Embedder → Retriever → QA / Extractor |
| Knowledge OS | Ingestor → Vector Store → Retriever → Summarizer / Insight Generator |
| AI Interviewer | Question Generator → Evaluator → Difficulty Adjuster → Feedback Compiler |
| Generative UI Builder | Spec Generator → Validator → Code Generator → Repair |

### LangGraph State Machines (5)

| System | Core Pattern |
| --- | --- |
| Data Analysis Agent | Planner → Executor → Interpreter → Evaluator (loop) |
| Debugging Agent | Analyzer → Fixer → Tester → Evaluator (bounded retry) |
| Research Agent | Planner → Retriever → Reporter (extensible scaffold) |
| Support Agent | Classifier → Retriever → Responder → Escalation Router |
| Workflow Agent | Planner → Executor → Validator → Checkpoint Manager |

### CrewAI Teams (5)

| System | Core Pattern |
| --- | --- |
| Content Pipeline | Researcher → Writer → Editor → SEO Optimizer |
| Hiring Decision Crew | Screener → Technical → Behavioral → Manager → Bias Auditor |
| Investment Analyst | Market → Financial → Risk → Strategist → Red Team |
| Product Launch | Market Researcher → Positioning → Messaging → Channel → Coordinator |
| Startup Simulator | CEO → CTO → CMO → CFO → Advisor (refinement loop) |

---

## Limitations & Future Work

- **No Next.js route middleware auth** — browser auth relies on the backend's HttpOnly session cookie and API keys live only in client memory; Next.js routes themselves do not independently enforce auth
- **No SSR for dynamic pages** — the playground and metrics pages are fully client-rendered; initial paint shows loading states
- **Minimal test suite** — focused unit tests exist for pure playground utility logic (`npm run test`); no component or integration tests yet
- **No mobile navigation** — the nav bar renders all links in a horizontal row without a responsive hamburger menu
- **Build-time catalog sync** — the frontend ships a static project manifest for reliability; changes to project definitions still require updating `src/data/project-catalog.json`

### Planned

- Responsive mobile navigation
- Component-level tests for key interactive surfaces
- Client-side route guards based on auth state
- End-to-end tests with Playwright
- Dynamic project discovery from the backend API
