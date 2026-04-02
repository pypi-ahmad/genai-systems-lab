<div align="center">

# GenAI Systems Lab

**A shared execution platform for 20 AI systems — Generative AI pipelines, LangGraph state machines, and CrewAI multi-agent teams — unified behind a single API, frontend, and runtime.**

[![CI](https://github.com/pypi-ahmad/genai-systems-lab/actions/workflows/ci.yml/badge.svg)](https://github.com/pypi-ahmad/genai-systems-lab/actions/workflows/ci.yml)
[![Python 3.13](https://img.shields.io/badge/python-3.13-3776ab.svg)](https://www.python.org/downloads/)
[![Next.js 16](https://img.shields.io/badge/Next.js-16-000000.svg)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Google Gemini](https://img.shields.io/badge/Google%20Gemini-8E75B2.svg?logo=googlegemini&logoColor=white)](https://ai.google.dev/)
[![OpenAI](https://img.shields.io/badge/OpenAI-412991.svg?logo=openai&logoColor=white)](https://platform.openai.com/)
[![Anthropic](https://img.shields.io/badge/Anthropic%20Claude-191919.svg?logo=anthropic&logoColor=white)](https://www.anthropic.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-1C3C3C.svg?logo=langchain&logoColor=white)](https://langchain-ai.github.io/langgraph/)
[![CrewAI](https://img.shields.io/badge/CrewAI-FF5A50.svg)](https://www.crewai.com/)
[![React 19](https://img.shields.io/badge/React-19-61dafb.svg?logo=react&logoColor=white)](https://react.dev/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind%20CSS-v4-06b6d4.svg?logo=tailwindcss&logoColor=white)](https://tailwindcss.com/)
[![TypeScript](https://img.shields.io/badge/TypeScript-3178c6.svg?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![SQLite](https://img.shields.io/badge/SQLite-003B57.svg?logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![Docker](https://img.shields.io/badge/Docker-2496ed.svg?logo=docker&logoColor=white)](https://www.docker.com/)

[Overview](#overview) · [Features](#core-features) · [Architecture](#architecture) · [Projects](#project-catalog) · [Setup](#setup-and-installation) · [Usage](#usage) · [API](#api-reference) · [Limitations](#limitations-and-future-improvements)

</div>

---

## Overview

Most AI agent repositories demonstrate one orchestration pattern in isolation. This repository takes a different approach: it provides **one shared runtime** for three distinct agent paradigms, so they can be built, evaluated, and compared through the same operational surfaces.

The three paradigms:

| Paradigm | Execution model | Suited for |
|---|---|---|
| **Generative AI** | Sequential prompt pipeline with `emit_step()` hooks | Research, Q&A, code analysis, document intelligence |
| **LangGraph** | Typed state machine with `graph.invoke()` and conditional edges | Iterative debugging, workflow planning, support routing |
| **CrewAI** | Role-based agent team with `crew.kickoff()` and sequential handoff | Content pipelines, hiring evaluation, investment analysis |

All 20 project modules implement a single contract: `run(input: str, api_key: str) -> dict`. The platform handles everything outside that domain boundary: JWT plus HttpOnly-cookie authentication, request validation and sanitization, per-request API key binding via `ContextVar`, multi-provider LLM dispatch (Gemini, OpenAI, Anthropic, Ollama), synchronous and SSE streaming execution, configurable persistence, cross-run session memory, confidence scoring, LLM-backed explainability, public share links, in-memory metrics, and benchmark evaluation.

### Why this design

Without a shared runtime, every new AI project rebuilds the same infrastructure: auth, request handling, evaluation scaffolding, history, and UI. This repository centralizes that platform work so new projects implement only `run()` in `app/main.py` and immediately inherit the full stack.

---

## Core Features

### Multi-provider BYOK execution

The platform is **stateless with respect to API keys**. Every LLM-calling route requires an `X-API-Key` header. Two optional companion headers select the provider and model:

| Header | Purpose | Required |
|---|---|---|
| `X-API-Key` | Provider API key (not needed for Ollama) | Yes (except Ollama) |
| `X-LLM-Provider` | Force a provider (`gemini`, `openai`, `anthropic`, `ollama`) | No — inferred from model |
| `X-LLM-Model` | Override the default model | No — falls back to config |

`BYOKMiddleware` (pure ASGI) binds all three values to `ContextVar` instances for the duration of each request. `get_effective_api_key()` retrieves the key anywhere in the call stack without argument threading. Keys are never logged, stored, or echoed in responses. Routes that don't invoke an LLM (`/`, `/health`, `/projects`, `/auth/*`, `/metrics`, `/history`, `/session/*`, `/shared/*`, `/run/*`, `/llm/catalog`) are exempt.

**Supported providers and models:**

| Provider | Models | API key format |
|---|---|---|
| **Google Gemini** (default) | `gemini-3-flash-preview`, `gemini-3.1-pro-preview` | `AIza...` |
| **OpenAI** | `gpt-5.4`, `gpt-5.4-mini` | `sk-...` |
| **Anthropic Claude** | `claude-sonnet-4-6`, `claude-opus-4-6` | `sk-ant-...` |
| **Ollama** (local) | Any model available on the local Ollama server | None required |

`GET /llm/catalog` returns the full provider catalog at runtime, including dynamically discovered Ollama models. If the provider is not specified, `infer_provider()` resolves it from the model name — any unknown model ID routes to Ollama.

### Authentication

- **JWT**: Custom HS256 implementation (no third-party JWT library). Tokens carry `{sub, email, iat, exp}` with a 7-day TTL. `GENAI_SYSTEMS_LAB_JWT_SECRET` is required in production (`APP_ENV=prod`) and must be at least 16 characters; local development falls back to an ephemeral per-process secret with a clear startup warning.
- **Browser sessions**: `/auth/signup` and `/auth/login` also set an HttpOnly session cookie so the Next.js frontend no longer persists raw JWTs in browser storage.
- **Password hashing**: PBKDF2-HMAC-SHA256 with 310,000 iterations and a 16-byte random salt. Verification uses `hmac.compare_digest()` to prevent timing attacks.
- **Signup posture**: Public signup remains enabled in local development and defaults off when `APP_ENV=prod` unless `GENAI_SYSTEMS_LAB_ENABLE_PUBLIC_SIGNUP=true` is set explicitly.
- Execution, history, session, sharing, and explainability routes accept `Authorization: Bearer <token>` for API clients and the HttpOnly session cookie for browser clients.

### Origin policy and abuse control

- **CORS**: Defaults to explicit local frontend origins instead of `*`. Set `GENAI_SYSTEMS_LAB_ALLOWED_ORIGINS` for deployed frontends.
- **Rate limiting**: Lightweight in-memory throttling applies to signup/login and expensive endpoints such as `/eval/*`, `/stream/*`, and `/explain/*`.

### Observability and operational reporting

- **Tracing**: OpenTelemetry is bootstrapped automatically at API startup when `OTEL_ENABLED=true`. If the optional packages are unavailable, startup logs a warning instead of failing silently.
- **Durable metrics**: Project execution metrics are persisted to the `operational_metrics` table, so `/metrics` and `/metrics/time` survive process restarts and include guest as well as authenticated runs.

### Input validation and sanitization

`InputValidationMiddleware` processes every `POST`/`PUT`/`PATCH` body before any route handler runs:

- Rejects empty `input` or inputs exceeding 10,000 characters.
- Rejects payloads matching XSS, SQL injection, JS protocol, and null-byte patterns.
- Sanitizes all string values: strips control characters (`\x00–\x08`, `\x0b`, `\x0c`, `\x0e–\x1f`, `\x7f`) and HTML-escapes remaining content.

### Project auto-discovery and alias resolution

`shared/api/runner.py` scans the repository root at startup for any directory containing `app/main.py`. No registration is needed. The runner resolves 29 aliases — 20 from the project catalog and 9 legacy names (e.g., `nl2sql-agent` → `genai-nl2sql-agent`, `hiring-crew` → `crew-hiring-system`) — and supports prefix-stripped lookups so projects are addressable by short or full name.

Every discovered project is dynamically imported with `importlib`. The runner clears cached `app.*` imports between loads to prevent cross-project module leakage.

### Streaming execution (SSE)

`GET /stream/{project}` launches the project in a background thread and emits Server-Sent Events:

1. `event: step` — `{"step": "<node>", "status": "running|done|error"}` as pipeline nodes execute.
2. `data: {"token": "..."}` — output text in 80-character chunks.
3. `event: done` — full response payload (latency, confidence, session metadata).
4. `event: error` — error string on failure.

Projects that call `emit_step()` natively stream their own step events. When a project emits no step events, the backend falls back to pipeline nodes from the shared project catalog in `portfolio/src/data/project-catalog.json`, which it compiles into `PIPELINE_NODES` at startup.

### Confidence scoring

Each run receives a composite confidence score:

$$\text{confidence} = 0.4 \times \text{evaluator} + 0.3 \times \text{execution} + 0.2 \times \text{consistency} + 0.1 \times \text{latency}$$

| Component | Weight | Derivation |
|---|---|---|
| Evaluator score | 0.4 | Extracted from output fields matching known score keys (`confidence`, `accuracy`, `score`, `quality_score`, etc.) or inferred from output structure |
| Execution success | 0.3 | `1.0` if run succeeded, `0.0` otherwise |
| Consistency score | 0.2 | `1 / (1 + retries)`, inferred from `retry_count`/`retries` in output or timeline entries |
| Latency score | 0.1 | `5000 / (5000 + latency_ms)` |

### Session memory

Conversation state is tracked per user in the `sessions` table:

- After each run, a memory entry is appended: `"User: <input_preview> | Agent: <output_preview>"` (max 620 chars per entry).
- The window is capped at **12 entries** with deduplication against the last 2 entries by normalized content.
- On subsequent runs in the same session, the **last 4 entries** are injected as a `Previous context:` prefix to the input before dispatch.

### Run persistence and replay

Every execution is written to SQLite (`.data/genai_systems_lab.db`) with: project, input, output, latency, confidence, success flag, session memory snapshot, timeline entries, and optional public share metadata. The portfolio replays these timelines, renders step-by-step execution logs, and can request LLM-generated explanations for any saved run.

### Explainability

`POST /explain/{run_id}` generates a structured narrative using Gemini 3.1-pro-preview with JSON schema-mode output. The schema enforces `steps_taken`, `key_decisions`, `final_reasoning`, and `final_outcome` — derived only from stored run artifacts (input, output, memory, timeline). The system prompt explicitly prohibits the model from inventing reasoning not present in the artifacts.

### Evaluation

- Benchmark datasets are registered per project in `shared/eval/benchmarks.py` (all 20 projects).
- `POST /eval/{project}` runs the benchmark suite and returns per-case pass/fail, accuracy, and latency percentiles (mean, p50, p95, p99). Requires `X-API-Key`.

### In-memory metrics

A thread-safe `_MetricsStore` accumulates per-project request count, total latency, and success count for the lifetime of the process. `GET /metrics` returns live aggregate counters. `GET /metrics/time` queries SQLite for historical time-series data bucketed by hour, day, or week.

---

## Tech Stack

| Layer | Technology | Version |
|---|---|---|
| LLM (default) | Google Gemini via `google-genai` | 1.69.0 |
| LLM providers | OpenAI (HTTP), Anthropic Claude (HTTP), Ollama (local HTTP) | — |
| LLM models | Gemini 3 Flash / 3.1 Pro, GPT-5.4 / 5.4 mini, Claude Sonnet 4.6 / Opus 4.6, any Ollama model | — |
| Backend | Python, FastAPI, Uvicorn | 3.13 |
| ORM / DB | SQLAlchemy + SQLite | 2.0.48 |
| Validation | Pydantic | 2.11.10 |
| Agent frameworks | LangGraph, CrewAI | — |
| Data | DuckDB, Pandas, NumPy | 1.5.1, 3.0.1, 2.3.3 |
| Frontend | Next.js, React, TypeScript | 16.2.1, 19.2.4 |
| UI styling | Tailwind CSS | v4 |
| Charts | Recharts | 3.8.1 |
| Observability | `rich` structured logging, OpenTelemetry spans | 14.3.3 |
| Infra | Docker, Docker Compose, GitHub Actions | — |

### LLM dispatch architecture (`shared/llm/`)

All LLM calls pass through a unified dispatch layer (`dispatch.py`) that routes to the correct provider based on request-scoped `ContextVar` values:

```
Project calls generate_text() / generate_structured() / embed()
  │
  └─ dispatch.py → infer_provider(model) → route to:
       ├─ gemini_provider.py — google-genai SDK (text, structured, vision, embeddings)
       ├─ providers.py       — OpenAI HTTP (text, structured, vision, embeddings)
       ├─ providers.py       — Anthropic HTTP (text, structured, vision)
       └─ providers.py       — Ollama HTTP (text, structured, vision, embeddings)
```

**Shared behavior across all providers:**

- **Retry**: 3 attempts with exponential backoff (1 s → 2 s → 4 s).
- **Timeout**: 120 seconds per attempt.
- **Key resolution**: every call goes through `get_effective_api_key()`, which reads the per-request `ContextVar`. API keys from `.env` are **not** used at runtime.

**Gemini-specific:**

- **Client caching**: `genai.Client` instances are cached per API key in a thread-safe dict, preventing httpx connection-pool exhaustion.
- **Model fallback**: `gemini-3.1-pro-preview` → `gemini-3-flash-preview` on generation or timeout failure.
- **Structured output**: `application/json` MIME type with Pydantic-derived JSON schema.
- **Vision**: `generate_text_from_image()` wraps image bytes as a multipart `Part`.

**OpenAI / Anthropic / Ollama:**

- Implemented via raw `urllib.request` — zero SDK dependencies.
- OpenAI and Ollama support text embeddings; Anthropic does not.
- Ollama models are discovered dynamically from the local server.

---

## Architecture

### System overview

```
┌────────────────────────────────────────────────────────────────────────┐
│  Clients                                                               │
│  ┌───────────────┐  ┌──────────────┐  ┌─────────────────┐            │
│  │ Next.js 16    │  │ Direct HTTP  │  │ Consumers       │            │
│  │ Portfolio     │  │ Clients      │  │                 │            │
│  └──────┬────────┘  └──────┬───────┘  └────────┬────────┘            │
└─────────┼──────────────────┼───────────────────┼──────────────────────┘
          │ JWT + X-API-Key  │                   │
          ▼                  ▼                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│  FastAPI  (shared/api/app.py)                                          │
│                                                                        │
│  Middleware (outermost → innermost):                                   │
│    CORSMiddleware                                                       │
│    RequestRateLimitMiddleware — in-memory abuse throttling             │
│    BYOKMiddleware             — X-API-Key / X-LLM-Provider / X-LLM-Model → ContextVars │
│    InputValidationMiddleware  — length, injection, sanitize            │
│    RequestLoggingMiddleware   — request_id, project_name, status log   │
│    RequestTimingMiddleware    — X-Process-Time-Ms header + OTel span   │
│    ErrorHandlingMiddleware    — structured JSON on unhandled exceptions│
│                                                                        │
│  Routes: auth · run · stream · history · session · metrics            │
│          eval · sharing · explain · health · llm/catalog              │
└───────────────────────────────┬────────────────────────────────────────┘
                                │
                                ▼
┌────────────────────────────────────────────────────────────────────────┐
│  Shared Runner  (shared/api/runner.py)                                 │
│                                                                        │
│  1. Auto-discover: scan repo root for <dir>/app/main.py               │
│  2. Resolve name: alias map (29 entries: 20 catalog + 9 legacy) + prefix stripping           │
│  3. Dynamic import: importlib + sys.path injection + cache clearing   │
│  4. Invoke run(input, api_key) → dict                                 │
│  5. Bind StepEmitter ContextVar for streaming step events             │
│  6. Serialize structured output for API responses                     │
└───────────────────────────────┬────────────────────────────────────────┘
                                │
         ┌──────────────────────┼──────────────────────┐
         ▼                      ▼                       ▼
┌─────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│ 9 Sequential    │  │ 6 LangGraph      │  │ 5 CrewAI         │
│ Pipelines       │  │ Workflows        │  │ Agent Teams      │
│                 │  │                  │  │                  │
│ emit_step()     │  │ graph.invoke()   │  │ crew.kickoff()   │
│ native SSE      │  │ native SSE via   │  │ fallback steps   │
│                 │  │ instrument_node  │  │                  │
└────────┬────────┘  └────────┬─────────┘  └────────┬─────────┘
         └──────────────────────┼──────────────────────┘
                                ▼
┌────────────────────────────────────────────────────────────────────────┐
│  Shared Runtime  (shared/)                                             │
│                                                                        │
│  llm/         Multi-provider dispatch (Gemini SDK, OpenAI/Anthropic/   │
│               Ollama HTTP), retry, fallback, structured, vision        │
│  api/auth     JWT lifecycle, PBKDF2 hashing, run serialization        │
│  api/models   SQLAlchemy: User, RunSession, Run, OperationalMetric    │
│  api/db       SQLite engine + backward-compat column migrations        │
│  api/session_memory  12-entry window, 4-entry injection, dedup        │
│  api/confidence      4-component weighted formula                     │
│  api/run_explainer   LLM explain from stored artifacts                │
│  api/eval_runner     Benchmark execution                              │
│  api/step_events     ContextVar StepEmitter for streaming             │
│  eval/        Benchmark datasets (20 projects) + latency metrics      │
│  cache/       In-memory TTL caches (prompt-keyed)                     │
│  logging/     Structured logs + OpenTelemetry spans                   │
│  config.py    BYOK ContextVar, Settings, model resolution             │
└────────────────────────────────────────────────────────────────────────┘
```

### Batch request lifecycle

```
POST /{project}/run  (Authorization: Bearer <jwt>  +  X-API-Key  +  X-LLM-Provider?  +  X-LLM-Model?)
  │
  ├─ InputValidationMiddleware:  reject/sanitize body
  ├─ RequestLoggingMiddleware:   assign request_id, log method + path
  ├─ RequestTimingMiddleware:    start timer, open OTel span
  ├─ BYOKMiddleware:             bind X-API-Key, X-LLM-Provider, X-LLM-Model to ContextVars
  │
  └─ Route handler:
      ├─ Decode JWT → load User from SQLite
      ├─ Resolve or create RunSession
      ├─ Deserialize session memory; inject last 4 entries as context prefix
      ├─ runner.run_project() → importlib load → call run(input, api_key)
      ├─ compute_run_confidence(output, success, latency, timeline)
      ├─ Persist Run to SQLite (input, output, memory, timeline, confidence)
      ├─ update_session_memory_entries() — dedup + cap at 12
      ├─ metrics_store.record(project, latency, success)
      └─ Return:
           { output, latency, confidence, session_id, session_memory,
             used_session_context, success, memory, timeline }
```

### Streaming request lifecycle

```
GET /stream/{project}?token=<jwt>&input=<text>  (X-API-Key  +  X-LLM-Provider?  +  X-LLM-Model?)
  │
  ├─ Middleware chain (same as batch)
  └─ Route handler:
      ├─ Launch project in background thread with StepEmitter callback
      ├─ Native projects: emit_step() pushes real {"step", "status"} events
      ├─ Others: catalog-derived PIPELINE_NODES provide synthetic step IDs
      └─ SSE generator yields:
          ├─ event: step  →  {"step": "planner", "status": "running"}
          ├─ event: step  →  {"step": "planner", "status": "done"}
          ├─ data: {"token": "<80-char chunk>"}  (repeated)
          ├─ event: done  →  full response payload
          └─ event: error →  {"error": "..."}
```

### Persistence schema

```
┌──────────────┐     ┌──────────────────┐     ┌──────────────────────────────┐
│ users        │────<│ sessions         │────<│ runs                         │
│              │     │                  │     │                              │
│ id           │     │ id               │     │ id                           │
│ email        │     │ user_id (FK)     │     │ user_id (FK)                 │
│ password_hash│     │ memory  (JSON[]) │     │ session_id (FK, nullable)    │
│ created_at   │     │ created_at       │     │ project                      │
└──────────────┘     │ updated_at       │     │ input, output                │
                     └──────────────────┘     │ memory, timeline (JSON[])    │
                                              │ latency_ms, confidence       │
                                              │ success, timestamp           │
                                              │ share_token, is_public       │
                                              │ expires_at                   │
                                              └──────────────────────────────┘

┌──────────────────────────┐
│ operational_metrics      │
│                          │
│ id, project, latency_ms  │
│ confidence, success      │
│ timestamp                │
└──────────────────────────┘
```

### Key modules

| Module | Responsibility |
|---|---|
| `shared/api/app.py` | FastAPI factory: 7 middleware classes, 22 route handlers, SSE generator, metrics store |
| `shared/api/runner.py` | Project discovery, 29-alias resolution (20 catalog + 9 legacy), `run(input, api_key)` dispatch, step emitter binding |
| `shared/api/auth.py` | JWT encode/decode (pure HMAC-SHA256), PBKDF2 hashing, run serialization helpers |
| `shared/api/models.py` | SQLAlchemy ORM: `User`, `RunSession`, `Run` (15 mapped columns), `OperationalMetric` |
| `shared/api/db.py` | SQLite engine init, `create_all()`, backward-compatible column migrations via `PRAGMA table_info` |
| `shared/api/session_memory.py` | 12-entry persisted window, 4-entry context injection, content deduplication |
| `shared/api/confidence.py` | 4-component weighted confidence score; evaluator field extraction from arbitrary output shape |
| `shared/api/run_explainer.py` | Gemini 3.1-pro-preview structured explanation from stored run artifacts |
| `shared/api/eval_runner.py` | Per-case benchmark execution, rule evaluation |
| `shared/api/step_events.py` | `ContextVar`-based `StepEmitter` for decoupled step emission during streaming |
| `shared/api/langgraph_events.py` | `instrument_node` wrapper — emits step events from LangGraph node functions |
| `shared/llm/dispatch.py` | Unified provider dispatch: routes calls to Gemini, OpenAI, Anthropic, or Ollama |
| `shared/llm/catalog.py` | Provider catalog: static definitions for Gemini/OpenAI/Anthropic, dynamic Ollama discovery |
| `shared/llm/gemini.py` | Backward-compatible facade delegating to the dispatch layer |
| `shared/llm/gemini_provider.py` | Gemini-specific client: `google-genai` SDK, retry/backoff/fallback, client caching |
| `shared/llm/providers.py` | HTTP-based implementations for OpenAI, Anthropic, and Ollama (zero SDK deps) |
| `shared/project_catalog.py` | Loads `project-catalog.json` manifest; Pydantic models for graph nodes/edges |
| `shared/config.py` | BYOK `ContextVar`, request-scoped model/provider overrides, `Settings` (Pydantic), model resolution |
| `shared/eval/benchmarks.py` | Rule-based benchmark datasets for all 20 projects; `BenchmarkSuite` latency harness |
| `shared/eval/stress.py` | Asyncio-based stress testing for throughput and error-rate analysis |
| `portfolio/src/lib/api.ts` | TypeScript API client: batch run, SSE streaming, auth, history, metrics, sharing, BYOK headers |

---

## Project Structure

```
genai-systems-lab/
├── shared/
│   ├── api/              FastAPI platform (app, runner, auth, models, db,
│   │                     session_memory, confidence, run_explainer,
│   │                     eval_runner, step_events, langgraph_events)
│   ├── llm/              Multi-provider dispatch (dispatch, catalog, gemini_provider,
│   │                     gemini facade, providers, exceptions)
│   ├── eval/             Benchmark datasets + latency metrics + stress testing
│   ├── cache/            In-memory TTL caches (prompt-keyed)
│   ├── logging/          Structured logging + OpenTelemetry spans
│   ├── schemas/          Pydantic request/response models
│   ├── utils/            Generic helpers (text chunking, timing)
│   ├── config.py         BYOK ContextVar, request-scoped model/provider, Settings
│   └── project_catalog.py  Portfolio manifest loader + graph node models
│
├── genai-*/              10 project directories with the `genai-` prefix
│   └── app/main.py       Most are sequential pipelines; `genai-research-system` is LangGraph-based
├── lg-*/                 5 additional LangGraph state machine projects
│   └── app/main.py       Implements run(input, api_key) → dict
├── crew-*/               5 CrewAI multi-agent team projects
│   └── app/main.py       Implements run(input, api_key) → dict
│
├── portfolio/            Next.js 16 frontend
│   └── src/
│       ├── app/          App Router pages (playground, metrics, compare,
│       │                 projects, projects/[slug], auth, run/[id], about, architecture)
│       ├── lib/          API client, auth helpers, apikey storage, session
│       ├── components/   AnimatedGraph, AgentGraph, MemoryPanel,
│       │                 TimelineReplay, RunExplanation, ConfidenceIndicator
│       └── data/         Shared project catalog manifest + typed frontend facade
│
├── langgraph-data-analyst/  Standalone reference project (own deps;
│                            deliberately outside the platform runner)
├── ARCHITECTURE.md       Platform design principles
├── docker-compose.yml    api (8000) service for the shared backend
├── Dockerfile            python:3.13-slim; installs deps; runs uvicorn
├── pyproject.toml        Primary dependency manifest (slim, for serverless deployment)
├── requirements.txt      Full Python deps (local development and Docker builds)
└── .env.example          Model/config examples only; BYOK required at runtime
```

---

## Project Catalog

### Sequential / prompt-pipeline projects (9 projects)

All emit native SSE step events via `emit_step()`.

| Project folder | Pipeline nodes | Description |
|---|---|---|
| `genai-nl2sql-agent` | planner → schema → generator → validator → executor → summarizer | Natural language → validated DuckDB SQL → execution → plain-language result summary. |
| `genai-clinical-assistant` | extractor → retriever → reasoner → formatter | Extracts patient data, retrieves matching conditions, reasons over differential, outputs structured clinical report with confidence. |
| `genai-browser-agent` | perception → planner → executor → memory | Observe-plan-act loop using Playwright for browser automation tasks. |
| `genai-financial-analyst` | metrics → trends → forecaster → writer | Loads CSV data, computes financial KPIs, optional time-series forecast, trend analysis, narrative report. |
| `genai-code-copilot` | indexer → retriever → store → generator | Indexes a codebase, retrieves relevant chunks for a question, builds context, and generates a grounded answer. |
| `genai-doc-intelligence` | retriever → qa → extractor | Queries the local vector store, generates cited answers, and returns referenced sources. The module also includes separate ingestion and file-extraction helpers. |
| `genai-knowledge-os` | store → retriever → summarizer → insights | Opens the persisted vector and memory stores, retrieves matching chunks, summarizes the context, and optionally saves generated insights. |
| `genai-interviewer` | generator → evaluator → adjuster → compiler | Generates 5 interview questions for a topic/role with difficulty calibration and scoring. |
| `genai-ui-builder` | spec → validator → codegen → repair | Generates a UI spec from a prompt, produces React files (`App.jsx`), validates structure, and retries a repair pass on failure. |

### LangGraph workflows (6 projects)

Use `graph.invoke()` with typed state objects. All workflows emit native step events via `instrument_node()` or equivalent wrappers.

| Project folder | Pipeline nodes | Description |
|---|---|---|
| `genai-research-system` | planner → researcher → critic → writer → editor → originality_checker → formatter | LangGraph research workflow with conditional revision loops, editorial/originality checks, and report-oriented output with quality metrics. |
| `lg-data-agent` | planner → executor / duckdb_executor → analyzer → evaluator | Plans tabular analysis, routes to pandas or DuckDB execution, analyzes results, evaluates output quality with bounded retries. |
| `lg-debugging-agent` | analyzer → fixer → test_generator → tester → evaluator | Analyzes buggy code, generates a patch, produces test cases, runs them, evaluates resolution with bounded retries. |
| `lg-research-agent` | planner → researcher → critic → writer | Plans research sub-tasks, gathers findings per task, critiques the results, and produces a synthesized report. |
| `lg-support-agent` | classifier → retriever → responder → evaluator → escalation | Classifies customer intent, retrieves context, drafts a response, evaluates quality, and conditionally escalates. |
| `lg-workflow-agent` | planner → executor → validator → checkpoint → finalizer | Decomposes tasks into step plans, executes them, validates results, checkpoints progress, and produces a final summary. |

### CrewAI multi-agent teams (5 projects)

Use `crew.kickoff()` with role-based agents. Synthetic step events during streaming.

| Project folder | Pipeline nodes | Description |
|---|---|---|
| `crew-content-pipeline` | researcher → writer → editor → seo | Research, article drafting, editing, and SEO optimization through sequential agent handoff. |
| `crew-hiring-system` | screener → tech → behavioral → manager → auditor | 5-stage resume evaluation: screening, technical, behavioral, final decision, and bias audit. |
| `crew-investment-analyst` | market → financial → risk → strategist → redteam | Market, financial, risk, recommendation, and adversarial red-team analysis for investment decisions. |
| `crew-product-launch` | researcher → positioning → messaging → channel → coordinator | Market insights, personas, positioning, messaging, and go-to-market strategy. |
| `crew-startup-simulator` | ceo → cto → cmo → cfo → advisor | Leadership team simulation generating proposals, idea selection, tech specs, and financial review. |

---

## Setup and Installation

### Prerequisites

- Python 3.13+
- Node.js 20+ (portfolio frontend only)
- A Google, OpenAI, or Anthropic API key (supplied per request — never stored server-side), or a local Ollama server

### 1. Clone

```bash
git clone https://github.com/pypi-ahmad/genai-systems-lab.git
cd genai-systems-lab
```

### 2. Python environment

```bash
python -m venv .venv

# macOS / Linux
source .venv/bin/activate

# Windows PowerShell
.venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

> **Note:** `requirements.txt` includes the full set of framework packages for local development and Docker builds. `pyproject.toml` is the primary dependency manifest for deployed environments (e.g., Vercel) and excludes heavyweight packages like `crewai` and `playwright` that exceed serverless bundle limits. Browser binaries for Playwright may still need `playwright install` in environments that execute the browser agent.

### 3. Environment file

```bash
cp .env.example .env
```

`.env` is loaded by `python-dotenv` at startup and is used for application configuration such as model selection. The LLM dispatch layer resolves credentials through `get_effective_api_key()`, so API keys from `.env` are **not** consumed at runtime; they must be bound explicitly via request headers.

### 4. Configuration

All variables below are optional. The defaults shown are suitable for local development.

| Variable | Default | Purpose |
|---|---|---|
| `APP_ENV` | `dev` | Controls the default model (`dev` → flash, `prod` → pro) |
| `GENAI_SYSTEMS_LAB_JWT_SECRET` | — | Required in production for JWT signing; local dev falls back to an ephemeral secret |
| `GENAI_SYSTEMS_LAB_JWT_TTL_SECONDS` | `604800` (7 days) | JWT token lifetime |
| `GENAI_SYSTEMS_LAB_ALLOWED_ORIGINS` | `http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001,http://127.0.0.1:3001` | Explicit CORS allowlist for browser clients |
| `GENAI_SYSTEMS_LAB_ENABLE_PUBLIC_SIGNUP` | `true` in dev, `false` in prod | Controls whether `/auth/signup` is exposed publicly |
| `GENAI_SYSTEMS_LAB_DATABASE_URL` | local SQLite file | Override the default local SQLite database for deployed environments |
| `DATABASE_URL` | — | Fallback if `GENAI_SYSTEMS_LAB_DATABASE_URL` is not set |
| `GENAI_SYSTEMS_LAB_AUTH_COOKIE_SAMESITE` | `lax` | SameSite policy for the HttpOnly browser session cookie |
| `GENAI_SYSTEMS_LAB_AUTH_COOKIE_SECURE` | `true` in prod | Secure flag for the HttpOnly browser session cookie |
| `GENAI_SYSTEMS_LAB_AUTH_COOKIE_NAME` | `genai_systems_lab_session` | Cookie name for the HttpOnly browser session cookie |
| `GENAI_SYSTEMS_LAB_DISABLE_RATE_LIMITS` | `false` | Bypass rate limiting entirely (useful for testing) |
| `OLLAMA_BASE_URL` | `http://127.0.0.1:11434` | Ollama server URL for local model discovery and inference |
| `OPENAI_EMBEDDING_MODEL` | `text-embedding-3-small` | OpenAI embedding model name |
| `GEMINI_EMBEDDING_MODEL` | `gemini-embedding-2-preview` | Gemini embedding model name |
| `OLLAMA_EMBEDDING_MODEL` | `embeddinggemma` | Ollama embedding model name |
| `OTEL_ENABLED` | `false` | Enable OpenTelemetry startup wiring for the API |
| `OTEL_CONSOLE_EXPORT` | `false` | Mirror spans to the console exporter |
| `OTEL_SERVICE_NAME` | `genai-systems-lab` | Service name reported to the tracing backend |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `http://localhost:4317` | OTLP collector endpoint |
| `MODEL_DEFAULT_DEV` | `gemini-3-flash-preview` | Default model in dev |
| `MODEL_DEFAULT_PROD` | `gemini-3.1-pro-preview` | Default model in prod |
| `PROJECT_MODELS_JSON` | `{}` | JSON object mapping project names to model overrides |

### 5. Start services

```bash
# Terminal 1: FastAPI backend (auto-reloads on code changes)
uvicorn shared.api.app:app --reload

# Terminal 2: Next.js portfolio
cd portfolio && npm install && npm run dev
```

| Service | Default URL |
|---|---|
| FastAPI API | `http://localhost:8000` |
| Next.js portfolio | `http://localhost:3000` |

### Docker

```bash
docker compose up --build
```

Starts the API on port 8000. The Next.js portfolio is the supported frontend and can be run separately with `npm run dev` inside `portfolio/`.

### Vercel

The repository supports deployment as two separate Vercel projects — one for the Python backend, one for the Next.js frontend.

#### Backend (Python serverless function)

Vercel auto-detects `pyproject.toml` and uses it as the dependency manifest. The slim dependency list in `pyproject.toml` intentionally excludes `crewai` and `playwright` to stay under the 500 MB uncompressed bundle limit. Projects that depend on these packages return a graceful `503 Service Unavailable` with an explanatory message instead of crashing.

Required environment variables on the backend Vercel project:

| Variable | Value |
|---|---|
| `APP_ENV` | `prod` |
| `GENAI_SYSTEMS_LAB_JWT_SECRET` | A random string ≥ 16 characters |
| `GENAI_SYSTEMS_LAB_ALLOWED_ORIGINS` | The frontend Vercel URL (e.g., `https://your-frontend.vercel.app`) |
| `GENAI_SYSTEMS_LAB_ENABLE_PUBLIC_SIGNUP` | `true` if you want open registration |

The Python runtime is pinned to 3.13 via `requires-python` in `pyproject.toml`. On Vercel's read-only filesystem, the SQLite database falls back to `/tmp/.data/` automatically — this means **data is ephemeral** and does not persist across cold starts or redeployments.

#### Frontend (Next.js)

Set the root directory to `portfolio/` in the Vercel project settings. `next.config.ts` sets `outputFileTracingRoot` to the parent directory so the monorepo structure is traced correctly.

Required environment variable on the frontend Vercel project:

| Variable | Value |
|---|---|
| `NEXT_PUBLIC_API_BASE_URL` | The backend Vercel URL (e.g., `https://your-backend.vercel.app`) |

#### Deployment notes

- The entry point `shared.api.app:app` is declared in `pyproject.toml` under `[project.scripts]`.
- Ollama is backend-scoped: a Vercel-hosted backend cannot reach an end user's local Ollama instance, so the `/llm/catalog` endpoint will report Ollama as unavailable.
- If `GENAI_SYSTEMS_LAB_JWT_SECRET` is missing in production, the backend will fail on every request — including `/health`.

### langgraph-data-analyst (standalone example)

`langgraph-data-analyst` is deliberately kept outside the shared platform runner. It serves as a reference implementation showing how a LangGraph application can be built independently — with its own dependency set, data directory, and test suite — while still benefiting from the same agent design patterns used in the platform projects. It is not auto-discovered by the runner and will not appear in `/projects`.

```bash
pip install -r langgraph-data-analyst/requirements.txt
```

---

## Usage

### API

#### Authentication

```bash
# Create an account
curl -X POST http://localhost:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"StrongPass123"}'

# Login — returns a 7-day JWT for API clients and sets an HttpOnly cookie for browsers
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"StrongPass123"}'
```

#### Batch execution

Execution routes require `X-API-Key` (provider-appropriate). Authentication is optional — guest users can run projects without signing in (history and session memory are skipped for guests):

```bash
# Default (Gemini)
curl -X POST http://localhost:8000/genai-nl2sql-agent/run \
  -H "Authorization: Bearer <jwt>" \
  -H "X-API-Key: <google_api_key>" \
  -H "Content-Type: application/json" \
  -d '{"input":"top customers by revenue"}'

# OpenAI
curl -X POST http://localhost:8000/genai-nl2sql-agent/run \
  -H "Authorization: Bearer <jwt>" \
  -H "X-API-Key: <openai_api_key>" \
  -H "X-LLM-Provider: openai" \
  -H "X-LLM-Model: gpt-5.4" \
  -H "Content-Type: application/json" \
  -d '{"input":"top customers by revenue"}'

# Ollama (local, no API key)
curl -X POST http://localhost:8000/genai-nl2sql-agent/run \
  -H "Authorization: Bearer <jwt>" \
  -H "X-LLM-Provider: ollama" \
  -H "X-LLM-Model: llama3" \
  -H "Content-Type: application/json" \
  -d '{"input":"top customers by revenue"}'
```

Response:

```json
{
  "output": "{\"sql\": \"SELECT customer_name, SUM(amount) AS total_spend ...\", \"result\": [...], \"summary\": \"...\"}",
  "latency": 842.37,
  "confidence": 0.83,
  "session_id": 12,
  "session_memory": ["User: top customers by revenue | Agent: SELECT customer_name..."],
  "used_session_context": false,
  "success": true,
  "memory": [{"step": "Planner", "type": "thought", "content": "..."}],
  "timeline": [{"timestamp": 0.04, "step": "planner", "event": "running", "data": "..."}]
}
```

#### Streaming (SSE)

```bash
curl -N -G "http://localhost:8000/stream/genai-research-system" \
  -H "X-API-Key: <api_key>" \
  --data-urlencode "token=<jwt>" \
  --data-urlencode "input=Compare transformer architectures for code generation"
```

Event stream:

```
event: step
data: {"step": "planner", "status": "running"}

event: step
data: {"step": "planner", "status": "done"}

data: {"token": "Transformer architecture..."}

event: done
data: {"output": "...", "latency": 4210.5, "confidence": 0.91, ...}
```

#### Session continuity

Pass a `session_id` from a prior response to inject the last 4 memory entries as context:

```bash
curl -X POST http://localhost:8000/genai-research-system/run \
  -H "Authorization: Bearer <jwt>" \
  -H "X-API-Key: <api_key>" \
  -H "Content-Type: application/json" \
  -d '{"input":"Now focus only on evaluation benchmarks","session_id":12}'
```

#### Explain and share a run

```bash
# Generate a structured explanation from stored artifacts
curl -X POST http://localhost:8000/explain/42 \
  -H "Authorization: Bearer <jwt>" \
  -H "X-API-Key: <api_key>" \
  -H "Content-Type: application/json" \
  -d '{}'

# Create a 24-hour public share link
curl -X POST http://localhost:8000/run/42/share \
  -H "Authorization: Bearer <jwt>" \
  -H "Content-Type: application/json" \
  -d '{"expires_in_hours":24}'

# Public access (no auth required)
curl http://localhost:8000/shared/<share_token>
```

#### Metrics

```bash
# Live aggregate counters (resets on process restart)
curl http://localhost:8000/metrics

# Historical time-series from SQLite (per-project, bucketed)
curl "http://localhost:8000/metrics/time?project=genai-research-system&range=week"
```

### Portfolio

The Next.js frontend at `http://localhost:3000` provides:

| Route | Feature |
|---|---|
| `/playground` | Live execution: streaming pipeline graphs, real-time memory panel, timeline replay, session continuity, run history, public sharing, explainability |
| `/projects` | Project gallery: browse all 20 systems with metadata, architecture info, and demo links |
| `/projects/[slug]` | Per-project details: architecture, pipeline graph, example input/output, interactive demo |
| `/metrics` | Time-series charts for latency, confidence, and success rate (hour/day/week) |
| `/compare` | Side-by-side comparison of two project runs |
| `/auth` | Sign up and sign in |
| `/run/[id]` | Public shared run view |
| `/about` | Platform overview |
| `/architecture` | Architecture walkthrough |

---

## Developer Workflow

### Adding a new project

1. Create `<project-name>/app/main.py`.
2. Implement `run(input: str, api_key: str) -> dict`.
3. Call `set_byok_api_key(api_key)` at entry and `reset_byok_api_key(token)` in a `finally` block.
4. Optionally import `emit_step` from `shared.api.step_events` and call it at pipeline boundaries for native SSE.
5. Add benchmark cases to `shared/eval/benchmarks.py` for evaluation coverage.
6. Add the project entry to `portfolio/src/data/project-catalog.json` — the backend derives `PIPELINE_NODES` from this manifest automatically.

The runner discovers the project automatically on next startup — no registration required.

### CI/CD

GitHub Actions (`.github/workflows/ci.yml`) runs on pushes to `main` and on pull requests. The pipeline uses four jobs with dependency caching and concurrency grouping (in-flight runs for the same ref are cancelled automatically).

| Job | What it does |
|---|---|
| **backend-platform** | installs the root Python environment, runs `compileall` on `shared/` + `tests/`, runs the platform suite (`tests/`), runs the `crew-startup-simulator` and `lg-research-agent` project suites, and optionally runs Gemini-backed evaluation when `GOOGLE_API_KEY` is set |
| **backend-standalone-analyst** | installs `langgraph-data-analyst/requirements.txt` in its own isolated environment and runs that standalone project suite separately to avoid dependency conflicts with the shared platform runtime |
| **frontend** | `npm run lint`, `npm run test` (playground utility tests), `npm run build` (Next.js production build) |
| **docker** | Builds the backend Docker image to verify the `Dockerfile` stays valid (runs after both backend jobs pass) |

```text
push / PR → ┬─ backend-platform          ─── install root env → compile → tests → eval
             ├─ backend-standalone-analyst ─ install analyst env → analyst tests
             ├─ frontend                  ─── lint → test → build
             └─ docker                    ─── (waits for backend jobs) → docker build
```

Backend platform tests cover: API contracts (guest execution, streaming, BYOK, session memory, metrics, sharing), auth hardening (secret length/ephemeral fallback/prod enforcement), and catalog integrity (alias coverage, legacy compat, duplicate detection). Frontend tests cover the extracted playground utility logic via `tsx` + `node:test`.

---

## API Reference

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/` | — | Root endpoint returning service metadata |
| `GET` | `/health` | — | Health check |
| `GET` | `/llm/catalog` | — | Available LLM providers, models, and connection status |
| `GET` | `/projects` | — | List all auto-discovered projects |
| `GET` | `/auth/config` | — | Expose frontend auth capabilities such as public signup availability |
| `POST` | `/auth/signup` | — | Create account when public signup is enabled; returns JWT + user and sets browser session cookie |
| `POST` | `/auth/login` | — | Authenticate; returns JWT + user and sets browser session cookie |
| `POST` | `/auth/logout` | Session cookie optional | Clear the browser session cookie |
| `GET` | `/auth/me` | JWT or session cookie | Return the current authenticated user |
| `POST` | `/{project}/run` | API key (JWT optional) | Batch execution with full response |
| `GET` | `/stream/{project}` | API key (JWT optional) | SSE streaming execution |
| `GET` | `/metrics` | — | Durable aggregate execution metrics |
| `GET` | `/metrics/time` | — | Durable time-series execution metrics (`?project=&range=hour\|day\|week`) |
| `GET` | `/history` | JWT or session cookie | Authenticated user's run history |
| `GET` | `/run/{run_id}` | JWT or session cookie | Single run detail |
| `GET` | `/session/{id}` | JWT or session cookie | Session memory preview (last 5 entries) |
| `POST` | `/session/{id}/clear` | JWT or session cookie | Clear session memory |
| `POST` | `/explain/{run_id}` | JWT or session cookie + API key | Generate structured run explanation |
| `POST` | `/run/{run_id}/share` | JWT or session cookie | Create public share token |
| `DELETE` | `/run/{run_id}/share` | JWT or session cookie | Revoke share token |
| `GET` | `/shared/{token}` | — | View a public shared run |
| `POST` | `/eval/{project}` | API key | Run benchmark suite for a project |

Execution routes (`run`, `stream`, `explain`, `eval`) require `X-API-Key` (except Ollama). Authentication via JWT is optional for `run` and `stream` — unauthenticated (guest) requests skip history and session memory.

---

## Limitations and Future Improvements

### Current limitations

| Area | Limitation |
|---|---|
| `requirements.txt` | Includes the full framework set for local/Docker use; `pyproject.toml` is the slim manifest for serverless deployment |
| API base URL | Defaults to `http://localhost:8000`; override with `NEXT_PUBLIC_API_BASE_URL` for deployed frontends |
| Rate limiting | Abuse control is in-memory and process-local; use an upstream proxy or WAF for multi-instance enforcement |
| CI coverage | CI still validates only a subset of runnable projects directly |
| Persistence | SQLite remains the default for local and demo use; deployed environments should set `GENAI_SYSTEMS_LAB_DATABASE_URL`. Schema changes are applied via idempotent `ALTER TABLE` guards in `db.py`; adopt Alembic if the schema grows beyond single-column additions. |
| BYOK | All LLM calls require per-request API key headers; Ollama is the exception (local, no key). No server-side key storage. |

### Planned improvements

- ~~Generate the public project catalog from a shared source.~~ Done — `portfolio/src/data/project-catalog.json` is the single source of truth, read by both the Python backend and the Next.js frontend.
- ~~Multi-provider BYOK support.~~ Done — Gemini, OpenAI, Anthropic, and Ollama are all supported via `X-API-Key` / `X-LLM-Provider` / `X-LLM-Model` headers.
- Expand CI to cover all project modules and shared platform paths.
- Adopt Alembic for schema migrations if the data model expands beyond the current column-level additions.

---

## Design Philosophy

GenAI Systems Lab is a **portfolio-optimized showcase** — it prioritizes demo reliability, clear architecture narratives, and end-to-end skill display over multi-tenant operability. Every design choice reflects this:

| Concern | Approach |
|---|---|
| **Runtime** | Single shared FastAPI process discovers all 20 projects automatically; no per-project deployment overhead |
| **Auth** | HS256 JWT + HttpOnly cookies — simple, auditable, sufficient for single-operator use |
| **BYOK** | All LLM calls require a per-request API key via headers; multi-provider dispatch routes to Gemini, OpenAI, Anthropic, or Ollama |
| **Persistence** | SQLite by default for zero-config local demos; `GENAI_SYSTEMS_LAB_DATABASE_URL` for deployed environments |
| **Frontend** | One Next.js app with playground, metrics, compare, and per-project pages |
| **Testing** | Contract-level API tests plus per-project smoke tests; catalog integrity tests guard the shared manifest |

If this evolves toward a reusable platform, the next priorities would be: Alembic migrations, per-user quotas, external identity provider integration, structured observability (the OTel hooks are already wired), and container-per-project isolation.

---

## Further Reading

- [ARCHITECTURE.md](ARCHITECTURE.md) — Platform design principles: separation of concerns, deterministic + LLM hybrid, evaluation-first.
- [docs/comparison.md](docs/comparison.md) — LangGraph vs. CrewAI framework comparison.
- [portfolio/README.md](portfolio/README.md) — Frontend-specific documentation.

