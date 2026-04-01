# System Architecture

This repository is organized as a platform: a shared UI and API surface routes work into project modules, while common runtime services live in a reusable shared layer.

## High-Level Flow

```text
+-------------+      +-------------+      +-------------------+      +-------------------+
| UI          | ---> | API         | ---> | Project Modules   | ---> | Shared Layer      |
| Streamlit   |      | FastAPI     |      | GenAI / LangGraph |      | LLM / Eval /      |
| Operator UX |      | Routing     |      | / CrewAI systems  |      | Cache / Logging   |
+-------------+      +-------------+      +-------------------+      +-------------------+
```

## System Structure

- UI: The browser-facing entrypoint is the shared Streamlit application, which provides an operator interface for selecting projects, submitting input, and inspecting results.
- API: The FastAPI layer exposes health, discovery, execution, and evaluation endpoints. Middleware handles input validation, structured request logging, timing, and error normalization.
- Project Modules: Each runnable project exposes a standardized `run(input: str) -> dict` entrypoint. Projects implement domain logic independently while conforming to the same execution contract.
- Shared Layer: Common infrastructure under `shared/` provides LLM access, evaluation helpers, caching, configuration, schemas, logging, and dynamic project loading.

## Shared Components

### LLM Wrapper

The Gemini wrapper centralizes model access, timeout handling, retry logic, fallback behavior, and structured JSON generation. This keeps model invocation policy out of project code and makes LLM behavior consistent across all systems.

### Evaluation

The evaluation layer provides reusable task execution metrics, including success rate, latency, retries, and case-level results. It supports evaluation-first development by making project behavior measurable through a shared interface.

### Caching

The cache layer provides deterministic, in-memory TTL caches for LLM responses and embeddings. Caching is prompt-keyed and shared centrally so repeated work is reduced without coupling projects to storage-specific logic.

### Logging

The logging layer provides structured logs with request and project context. Request IDs, project names, latency, and error fields are injected consistently, making API traffic and project execution traceable across the platform.

## Agent Paradigms

### LangGraph

LangGraph projects are modeled as state machines. They are a fit for workflows that need explicit state transitions, retries, conditional routing, and iterative refinement loops.

### CrewAI

CrewAI projects are modeled as role-based agent teams. They are a fit for workflows where specialized agents collaborate sequentially or cooperatively to produce a final output.

## Design Principles

### Separation of Concerns

The platform isolates transport, orchestration, domain logic, and shared runtime services. UI concerns stay in the UI layer, HTTP concerns stay in the API layer, and project logic stays inside each project module.

### Deterministic + LLM Hybrid

Projects combine deterministic code paths with LLM-driven reasoning. Validation, routing, parsing, retries, and execution remain explicit in Python, while language generation and judgment tasks are delegated to models.

### Evaluation-First Design

The platform is designed so agent behavior can be measured, compared, and improved. Shared evaluation utilities, structured outputs, and standardized execution contracts make quality a first-class engineering concern rather than a post-hoc check.

## Implementation Notes

- Project discovery and execution are handled dynamically by the shared runner.
- Environment and model routing are centralized in shared configuration.
- API middleware enforces a baseline operational contract for every project.
- New projects can be added without changing the platform architecture as long as they implement the standard run interface.

## Persistence Strategy

The platform stores runs, metrics, sessions, and shared links in a relational database powered by SQLAlchemy.

| Aspect | Current approach |
|---|---|
| **Default engine** | SQLite (``.data/genai_systems_lab.db``) for zero-config local use |
| **Production override** | Set ``GENAI_SYSTEMS_LAB_DATABASE_URL`` to any SQLAlchemy-compatible URL |
| **Schema evolution** | Idempotent ``ALTER TABLE`` guards in ``shared/api/db.py`` — each column addition checks ``PRAGMA table_info`` / ``sqlite_master`` before executing |
| **When to graduate** | If the schema grows beyond single-column additions (e.g. new tables, foreign keys, data transforms), adopt Alembic with an ``alembic/`` directory at the repo root |

Current managed columns added via migration guards: ``confidence``, ``success``, ``session_id``, ``memory``, ``timeline``, ``share_token``, ``is_public``, ``expires_at``.