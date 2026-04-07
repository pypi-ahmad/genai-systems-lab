# How to Use GenAI Systems Lab

A practical guide to navigating and using every feature in the portfolio app.

---

## Table of Contents

- [Getting Started](#getting-started)
- [Home Page](#home-page)
- [Browsing Projects](#browsing-projects)
- [Running a Project in the Playground](#running-a-project-in-the-playground)
- [Understanding Execution Output](#understanding-execution-output)
- [Timeline Replay](#timeline-replay)
- [Run Explanation](#run-explanation)
- [Sharing a Run](#sharing-a-run)
- [Metrics Dashboard](#metrics-dashboard)
- [LangGraph vs CrewAI Comparison](#langgraph-vs-crewai-comparison)
- [Architecture Diagram](#architecture-diagram)
- [Authentication & Sessions](#authentication--sessions)
- [Theme Toggle](#theme-toggle)
- [Keyboard & UI Tips](#keyboard--ui-tips)
- [Troubleshooting](#troubleshooting)

---

## Getting Started

### Prerequisites

| Requirement | Details |
| --- | --- |
| **Browser** | Any modern browser (Chrome, Firefox, Edge, Safari) |
| **API key** | A Google Gemini API key (or OpenAI / Anthropic / Ollama) |
| **Backend** | The FastAPI backend running at `http://localhost:8000` (for local use) |

### Running Locally

```bash
# 1. Start the backend
python -m uvicorn shared.api.main:app --reload

# 2. Start the frontend
cd portfolio
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### API Key — Bring Your Own Key (BYOK)

You need your own LLM API key to run any project. The app supports multiple providers:

- **Google Gemini** (default)
- **OpenAI**
- **Anthropic**
- **Ollama** (local models, no key needed)

Your key is stored **only in browser tab memory** — it is never saved to disk, localStorage, or the server. Closing the tab discards it. Each tab maintains its own independent key.

---

## Home Page

**Route:** `/`

The landing page shows:

- A hero section introducing the lab and its 20 AI systems
- Aggregate stats (number of systems, paradigms, and capabilities)
- Quick links to the Playground, Projects, Metrics, and Comparison pages

Click any navigation link in the top bar to move between sections.

---

## Browsing Projects

**Route:** `/projects`

The projects page lists all 20 AI systems organized into three paradigms:

| Paradigm | Color | Examples |
| --- | --- | --- |
| **GenAI** | Emerald | Research System, NL2SQL Agent, Clinical Assistant |
| **LangGraph** | Blue | Debugging Agent, Data Analysis Agent |
| **CrewAI** | Violet | Hiring Crew, Investment Analyst Crew |

### Filtering

Use the category filter tabs at the top to show only a specific paradigm (GenAI / LangGraph / CrewAI) or view all.

### Project Detail Page

**Route:** `/projects/[slug]`

Click any project card to open its detail page, which includes:

- **Architecture description** — how the system is designed
- **Flow diagram** — a visual representation of data flow between agents/nodes
- **Feature list** — key capabilities
- **Example input/output** — sample prompts and expected responses
- **Tags** — technology and pattern labels
- **Live demo panel** — run the project directly from the detail page

---

## Running a Project in the Playground

**Route:** `/playground`

The playground is the core interactive feature. Here you can execute any of the 20 AI systems in real time.

### Step-by-Step

1. **Open the Playground** — click "Playground" in the navigation bar
2. **Select a project** — use the dropdown in the left sidebar to pick a system (e.g., `genai-research-system`)
3. **Enter your API key** — paste your key in the API Key field. Optionally select a different LLM provider and model
4. **Write your input** — type a prompt or paste a JSON request body in the input area. The sidebar shows an example input for the selected project
5. **Click Run** — the system begins executing immediately

### What Happens During a Run

Once you click Run:

- **Token streaming** — output text appears character-by-character in real time via Server-Sent Events (SSE)
- **Animated execution graph** — a directed acyclic graph (DAG) renders in the main panel, showing each agent/node transitioning through states:
  - Gray = idle
  - Yellow = running
  - Green = done
  - Red = error
- **Memory trace panel** — entries appear as the agent thinks and acts:
  - **Thought** (blue) — the agent's reasoning
  - **Action** (orange) — tool calls or decisions taken
  - **Observation** (gray) — results from tools or the environment
- **Latency and confidence** — metrics update as the run progresses and are finalized when execution completes

### Batch Fallback

If SSE streaming is not supported by your browser or network, the playground automatically falls back to a batch execution mode that returns the full response at once.

---

## Understanding Execution Output

After a run completes, you have several panels to inspect:

| Panel | What It Shows |
| --- | --- |
| **Output** | The final generated text, streamed token-by-token |
| **Graph** | The agent execution DAG with final node statuses |
| **Memory** | Expandable entries for every thought, action, and observation |
| **Metrics** | Latency (ms), confidence score, and success/failure status |

Click on any memory entry to expand it and see the full content.

---

## Timeline Replay

After a run finishes, the **Timeline Replay** panel lets you scrub through the execution frame by frame.

### Controls

- **Play / Pause** — auto-advance through timestamped events
- **Frame scrubber** — drag the slider to jump to any point in the execution
- **Speed controls** — adjust playback speed: 0.5×, 1×, 1.5×, 2×, or 4×

Each frame shows the agent graph state, memory entries, and output at that exact moment in the execution. This is useful for understanding multi-step reasoning and debugging agent behavior.

---

## Run Explanation

After a run completes, click **Explain** to generate an AI-powered summary of the execution.

The explanation includes:

- **Steps taken** — a structured list of each execution step
- **What happened** — a plain-language description of each step's action
- **Why it mattered** — the reasoning behind key decisions

This is powered by a separate LLM call to the backend (`POST /explain/{id}`), so it requires a valid API key.

---

## Sharing a Run

After a run completes:

1. Click the **Share** button
2. A public URL is generated at `/run/{shareToken}`
3. Optionally set an **expiry** (in hours) for the link
4. Copy and share the link with anyone

The shared page renders the full output, memory trace, timeline, and metrics — no API key or login required for the viewer.

---

## Metrics Dashboard

**Route:** `/metrics`

View performance data for all 20 systems.

### Charts Available

- **Latency** — response time per run (ms)
- **Confidence** — model confidence score per run
- **Success rate** — percentage of successful vs. failed runs

### Time Ranges

| Range | Granularity |
| --- | --- |
| Last hour | 5-minute buckets |
| Last day | Hourly buckets |
| Last week | Daily buckets |

### Filtering

Select a specific project from the dropdown to view its individual metrics with trend lines and automated summary text.

---

## LangGraph vs CrewAI Comparison

**Route:** `/compare`

A side-by-side technical comparison of the two multi-agent frameworks used in the lab:

| Dimension | LangGraph | CrewAI |
| --- | --- | --- |
| **Control flow** | Explicit graph topology with conditional edges | Task ordering with sequential/hierarchical process modes |
| **Determinism** | Higher — routing is code-defined | Lower — more prompt-shaped behavior |
| **Flexibility** | Branching, loops, human-in-the-loop approval | Best for analyst teams with clear role delegation |
| **State** | TypedDict checkpointed state | Shared memory across agents |

Each comparison point links to concrete implementations in the repository (e.g., the `lg-debugging-agent` for evaluator-driven retry loops).

---

## Architecture Diagram

**Route:** `/architecture`

An interactive diagram of the full system architecture. Hover over boxes to highlight data flow paths. Click a component to see a detail panel with its purpose, inputs, and outputs.

---

## Authentication & Sessions

**Route:** `/auth`

Authentication is **optional** — you can run any project without logging in.

### Why Log In?

Logging in unlocks:

- **Run history** — a list of all your past runs with project name, timestamp, and output preview
- **Persistent sessions** — multi-turn conversation context is preserved across runs (e.g., a chatbot remembers prior messages)
- **Session management** — use "Clear context" to reset the session while keeping history

### How It Works

1. Navigate to `/auth` and sign up or log in
2. The server sets an **HttpOnly cookie** (the JWT is never exposed to JavaScript)
3. A session marker is stored in `sessionStorage` to detect the active session on page load
4. Subsequent API calls automatically include the auth token

### Session Behavior

- **Session ID** is stored in `localStorage` and survives tab/page reloads
- Each run is associated with your session, enabling multi-turn context
- Closing all tabs and reopening retains your session until you explicitly log out or clear context

---

## Theme Toggle

Click the **sun/moon icon** in the top-right corner of the navigation bar to toggle between light and dark mode.

- The app ships with a full design system of 100+ CSS custom properties
- Theme preference is persisted in `localStorage` and respected on reload
- System preference (OS-level light/dark) is detected automatically on first visit

---

## Keyboard & UI Tips

- **Tab navigation** — all interactive elements are keyboard-accessible
- **JSON input** — the playground input field accepts free-text or JSON. Check the example input shown in the sidebar for the expected format
- **Multiple tabs** — each browser tab runs independently with its own API key and session state
- **Auto-scroll** — the output panel auto-scrolls during streaming. Scroll up manually to pause auto-scroll

---

## Troubleshooting

### "API unreachable" or connection errors

- Ensure the FastAPI backend is running on `http://localhost:8000`
- If using a custom backend URL, set the `NEXT_PUBLIC_API_BASE_URL` environment variable before starting the frontend
- Check for CORS issues — the backend must have `GENAI_SYSTEMS_LAB_ALLOWED_ORIGINS` set to allow the frontend origin

### No output after clicking Run

- Verify your API key is correct and has not expired
- Check the browser console (F12 → Console) for error messages
- Try a different project to rule out project-specific issues

### Streaming seems stuck

- The SSE connection may have timed out. Refresh the page and try again
- If streaming consistently fails, the app will fall back to batch mode automatically

### Theme not applying

- Clear `localStorage` for the site and reload
- Ensure your browser supports CSS custom properties (all modern browsers do)

### Shared link not loading

- The share link may have expired if an expiry was set
- The backend must be running and reachable from the viewer's network

### Login not working

- Check that the backend is running and the `/auth/login` endpoint returns a valid response
- Clear cookies for the site and try again
