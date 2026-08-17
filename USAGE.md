# Usage Guide — GenAI Systems Lab

**v1.2.0** · [GitHub](https://github.com/pypi-ahmad/genai-systems-lab) · [Technical Reference](TECHNICAL.md) · [Frontend Guide](portfolio/USAGE.md)

How-to guide for launching the platform, using the HTTP API, and operating key features.

> [!NOTE]
> This guide covers the **backend API**. For the frontend playground — streaming graphs, metrics charts, run sharing UI — see [portfolio/USAGE.md](portfolio/USAGE.md).

---

## Table of Contents

- [Quick Start](#quick-start)
- [Running via API](#running-via-api)
- [Authentication](#authentication)
- [Providing Your API Key (BYOK)](#providing-your-api-key-byok)
- [Running a Project (Synchronous)](#running-a-project-synchronous)
- [Streaming Execution (SSE)](#streaming-execution-sse)
- [Queued Execution (Async Jobs)](#queued-execution-async-jobs)
- [Session Memory (Multi-Turn)](#session-memory-multi-turn)
- [Run History](#run-history)
- [Sharing a Run](#sharing-a-run)
- [Run Explanation](#run-explanation)
- [Evaluation](#evaluation)
- [Metrics](#metrics)
- [Adding a New AI Project](#adding-a-new-ai-project)
- [Model Configuration](#model-configuration)
- [Environment Variables Quick Reference](#environment-variables-quick-reference)
- [Deploying with Docker Compose](#deploying-with-docker-compose)
- [Troubleshooting](#troubleshooting)

---

## Quick Start

### Windows (one-click)

```bat
launch.cmd
```

Or double-click `launch.cmd` in Explorer. The launcher (default mode — no Docker required):
- Installs `uv` if missing (via pip or winget)
- Creates `.venv` in the project root with `uv venv` and installs all deps via `uv sync --all-extras`
- Generates a persistent Fernet encryption key in `.data/launcher.env`
- Copies `.env.example` → `.env` if not present
- Starts FastAPI on port 8514 and waits for the health check
- Installs Node deps and starts Next.js on port 8513
- Opens `http://localhost:8513`

Pass `--docker` to use Docker Compose instead (`launch.cmd --docker`), which also auto-installs Docker Desktop and Node.js via winget if missing.

### Linux (one-click)

```bash
bash launch.sh
```

The Linux launcher uses `uv` (installed automatically if missing) to create a `.venv` in the project root, installs all dependencies, and starts the backend and frontend processes.

### Manual setup

```bash
# 1. Install Python dependencies (creates .venv automatically with uv)
uv sync --all-extras

# 2. Copy and configure env
cp .env.example .env
# Edit .env: set GENAI_SYSTEMS_LAB_JWT_SECRET, GENAI_SYSTEMS_LAB_BYOK_ENCRYPTION_KEY

# 3. Start the API
uv run uvicorn shared.api.app:app --host 0.0.0.0 --port 8514 --reload

# 4. Start the frontend (separate terminal)
cd portfolio && npm install && npm run dev
```

| Service | URL |
|---|---|
| FastAPI backend | `http://localhost:8514` |
| Next.js frontend | `http://localhost:8513` |
| OpenAPI docs | `http://localhost:8514/docs` |

---

## Running via API

```bash
# Health check
curl http://localhost:8514/health

# List available projects
curl http://localhost:8514/projects

# LLM provider catalog (models, pricing, effort options)
curl http://localhost:8514/llm/catalog
```

---

## Authentication

Auth is optional for `/run` and `/stream` (guest runs skip history and session memory). All other user-specific routes require it.

### Sign up

```bash
curl -X POST http://localhost:8514/auth/signup \
  -H "Content-Type: application/json" \
  -c cookies.txt \
  -d '{"email": "you@example.com", "password": "yourpassword"}'
```

Response:
```json
{"token": "<jwt>", "user": {"id": 1, "email": "you@example.com"}}
```

The response also sets an HttpOnly `genai_session` cookie (`-c cookies.txt` saves it for subsequent requests).

### Log in

```bash
curl -X POST http://localhost:8514/auth/login \
  -H "Content-Type: application/json" \
  -c cookies.txt \
  -d '{"email": "you@example.com", "password": "yourpassword"}'
```

### Using the token

Two options — either works:

```bash
# Option A: Bearer token in Authorization header
curl -H "Authorization: Bearer <jwt>" http://localhost:8514/auth/me

# Option B: session cookie saved by login/signup
curl -b cookies.txt http://localhost:8514/auth/me
```

> [!NOTE]
> Query-string JWTs (`?token=...`) are not accepted on any route, including the SSE stream.

### Check signup availability

```bash
curl http://localhost:8514/auth/config
# {"public_signup": true}
```

In production (`APP_ENV=prod`), signup is off by default unless `GENAI_SYSTEMS_LAB_ENABLE_PUBLIC_SIGNUP=true`.

---

## Providing Your API Key (BYOK)

All routes that invoke an LLM require an `X-API-Key` header. Ollama is the only exception — it runs locally and needs no key.

```bash
# Gemini
curl -H "X-API-Key: AIza..." ...

# OpenAI
curl -H "X-API-Key: sk-..." ...

# Anthropic
curl -H "X-API-Key: sk-ant-..." ...

# xAI
curl -H "X-API-Key: xai-..." ...
```

Optional override headers:

```bash
# Force a specific provider and model
curl \
  -H "X-API-Key: sk-..." \
  -H "X-LLM-Provider: openai" \
  -H "X-LLM-Model: gpt-5.6-luna" \
  -H "X-LLM-Effort: medium" \
  ...
```

Keys are bound to the request via `BYOKMiddleware` and are never logged or written to any database row. See [TECHNICAL.md — BYOK Key Resolution](TECHNICAL.md#byok-key-resolution) for the full chain.

---

## Running a Project (Synchronous)

```bash
curl -X POST http://localhost:8514/genai-research-system/run \
  -H "Content-Type: application/json" \
  -H "X-API-Key: AIza..." \
  -b cookies.txt \
  -d '{"input": "What are the main differences between LangGraph and CrewAI?"}'
```

**Response (`BaseResponse`):**

```json
{
  "output": "LangGraph uses typed state machines...",
  "latency": 2340.5,
  "confidence": 0.84,
  "session_id": 1,
  "session_memory": ["User: What are the... | Agent: LangGraph uses..."],
  "used_session_context": false,
  "success": true,
  "memory": [{"step": "research", "content": "...", "type": "action"}],
  "timeline": [{"timestamp": 0.0, "step": "planner", "event": "running", "data": ""}],
  "usage": {
    "input_tokens": 412,
    "output_tokens": 834,
    "total_tokens": 1246,
    "estimated_cost_usd": 0.000619,
    "models_used": ["gemini-3.7-flash"],
    "cost_breakdown": [...]
  }
}
```

**Guest run:** omit `Authorization` / cookie. History and session memory are skipped.

**Project names:** use the directory name (`genai-research-system`, `lg-support-agent`, `crew-hiring-system`). Aliases work too (`research-system`, `support-agent`, `hiring-system`).

**Switching providers:**

```bash
# OpenAI
curl -X POST http://localhost:8514/genai-nl2sql-agent/run \
  -H "Content-Type: application/json" \
  -H "X-API-Key: sk-..." \
  -H "X-LLM-Provider: openai" \
  -H "X-LLM-Model: gpt-5.6-luna" \
  -d '{"input": "top customers by revenue"}'

# Ollama (no API key needed)
curl -X POST http://localhost:8514/genai-nl2sql-agent/run \
  -H "Content-Type: application/json" \
  -H "X-LLM-Provider: ollama" \
  -H "X-LLM-Model: llama3" \
  -d '{"input": "top customers by revenue"}'
```

---

## Streaming Execution (SSE)

```bash
curl -N \
  -H "X-API-Key: AIza..." \
  -b cookies.txt \
  "http://localhost:8514/stream/genai-research-system?input=What+is+LangGraph"
```

Event stream:

```
event: step
data: {"step": "planner", "status": "running"}

event: step
data: {"step": "planner", "status": "done"}

event: step
data: {"step": "researcher", "status": "running"}

event: token
data: {"token": "LangGraph is a..."}

event: done
data: {"output": "...", "latency": 4210.5, "confidence": 0.91, ...}
```

| Event | When emitted |
|---|---|
| `step` | Each pipeline node start + end |
| `token` | Incremental text (research projects only) |
| `output` | Full text after completion (non-token projects) |
| `done` | Run complete — full `BaseResponse` payload |
| `error` | On failure — scrubbed message |

The `input` query parameter carries the task. BYOK headers (`X-API-Key`, `X-LLM-Provider`, etc.) apply the same way as synchronous runs.

---

## Queued Execution (Async Jobs)

Queued runs are authenticated and owner-scoped. Requires Redis and `GENAI_SYSTEMS_LAB_BYOK_ENCRYPTION_KEY`.

```bash
# Enqueue a job (returns 202 Accepted)
curl -X POST http://localhost:8514/jobs/crew-investment-analyst \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <jwt>" \
  -H "X-API-Key: sk-ant-..." \
  -d '{"input": "Analyze Tesla Q2 2026 earnings"}'
```

Response:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "project": "crew-investment-analyst",
  "status": "queued",
  "created_at": "2026-08-17T10:00:00Z"
}
```

```bash
# Poll for status
curl -H "Authorization: Bearer <jwt>" \
  http://localhost:8514/jobs/550e8400-e29b-41d4-a716-446655440000

# Cancel
curl -X DELETE \
  -H "Authorization: Bearer <jwt>" \
  http://localhost:8514/jobs/550e8400-e29b-41d4-a716-446655440000
```

Job statuses: `queued` → `running` → `succeeded` / `failed` / `cancelled`

> [!WARNING]
> Only the owner can view or cancel a job. Cross-user UUID lookups return `404` — identical to a missing job — to prevent enumeration.

> [!IMPORTANT]
> The API key is Fernet-encrypted in Redis with a 1-hour TTL. Set `GENAI_SYSTEMS_LAB_BYOK_ENCRYPTION_KEY` before queuing jobs. Generate a key:
> ```bash
> python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
> ```

---

## Session Memory (Multi-Turn)

Pass `session_id` from a prior response to continue a conversation:

```bash
# First run — new session created
curl -X POST http://localhost:8514/lg-support-agent/run \
  -H "Content-Type: application/json" \
  -H "X-API-Key: AIza..." \
  -b cookies.txt \
  -d '{"input": "I cannot connect to the database."}'
# Response includes "session_id": 42

# Follow-up — last 4 memory entries injected as context
curl -X POST http://localhost:8514/lg-support-agent/run \
  -H "Content-Type: application/json" \
  -H "X-API-Key: AIza..." \
  -b cookies.txt \
  -d '{"input": "What should I check in the connection string?", "session_id": 42}'
```

Memory window: 12 entries max, last 4 injected as `Previous context:` prefix.

**View session state:**

```bash
curl -b cookies.txt http://localhost:8514/session/42
```

**Clear session memory:**

```bash
curl -X POST -b cookies.txt http://localhost:8514/session/42/clear
```

---

## Run History

History uses **cursor-based pagination** via `limit` and `before_id` — not page numbers.

```bash
# First page (most recent 20 runs)
curl -b cookies.txt "http://localhost:8514/history?limit=20"

# Next page — pass the smallest id from the previous response as before_id
curl -b cookies.txt "http://localhost:8514/history?limit=20&before_id=85"

# Filter by project
curl -b cookies.txt "http://localhost:8514/history?limit=50&project=genai-research-system"

# Single run
curl -b cookies.txt http://localhost:8514/run/101
```

Response shape: `{"count": <int>, "runs": [...]}`

---

## Sharing a Run

```bash
# Create a public share link (default 7-day TTL)
curl -X POST \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  http://localhost:8514/run/101/share \
  -d '{"expires_in_hours": 72}'
# {"share_token": "abc123...", "is_public": true, "expires_at": "..."}

# Anyone can view it — no auth required
curl http://localhost:8514/shared/abc123...

# Revoke the share
curl -X DELETE -b cookies.txt http://localhost:8514/run/101/share
```

Maximum TTL: 720 hours (30 days). Default when omitted: 168 hours (7 days).

---

## Run Explanation

Generates a structured LLM-backed narrative from stored run artifacts:

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -H "X-API-Key: AIza..." \
  -b cookies.txt \
  http://localhost:8514/explain/101 \
  -d '{}'
```

Response includes `steps_taken`, `key_decisions`, `final_reasoning`, and `final_outcome`. The model is prohibited from inventing reasoning not present in the stored artifacts. Rate-limited to 20 req/min.

Override the explanation model with `X-LLM-Model`:

```bash
curl -X POST \
  -H "X-API-Key: sk-ant-..." \
  -H "X-LLM-Provider: anthropic" \
  -H "X-LLM-Model: claude-sonnet-5" \
  ...
```

---

## Evaluation

Run the registered benchmark suite for a project:

```bash
curl -X POST \
  -H "X-API-Key: AIza..." \
  http://localhost:8514/eval/genai-research-system
```

Returns per-case pass/fail, overall accuracy, and latency percentiles (mean, p50, p95, p99). Rate-limited to 6 requests per 5 minutes.

> [!NOTE]
> Provider-backed evaluations require the corresponding API key. Ollama evaluations run with no key.

---

## Metrics

```bash
# Aggregate (in-memory + persisted; survives process restarts)
curl http://localhost:8514/metrics

# Time-series (range: hour | day | week)
curl "http://localhost:8514/metrics/time?range=day"
curl "http://localhost:8514/metrics/time?range=hour&project=genai-research-system"
```

---

## Adding a New AI Project

1. Create a directory at the repo root: `genai-my-agent/`
2. Add `genai-my-agent/app/main.py` with a `run()` function:

```python
from shared.config import get_effective_api_key, get_model
from shared.llm import generate_text

def run(input: str, api_key: str) -> dict:
    model = get_model("genai-my-agent")
    result = generate_text(input, model=model)
    return {"output": result}
```

3. Restart the API — runner auto-discovers directories containing `app/main.py`.
4. Call it: `POST /genai-my-agent/run`
5. (Optional) Add to `portfolio/src/data/project-catalog.json` for frontend display.
6. (Optional) Register benchmark cases in `shared/eval/benchmarks.py`.

> [!TIP]
> Call `emit_step("node_name", "running")` and `emit_step("node_name", "done")` from `shared.api.step_events` at pipeline boundaries to emit native SSE step events.

> [!IMPORTANT]
> Never call `get_effective_api_key(required=True)` for Ollama routes — Ollama needs no key.

---

## Model Configuration

**Default for all projects:**

```bash
MODEL_DEFAULT_DEV=gemini-3.7-flash
MODEL_DEFAULT_PROD=gemini-3.7-flash
```

**Override all projects at once (JSON):**

```bash
PROJECT_MODELS_JSON='{"genai-research-system": "gpt-5.6-luna", "lg-support-agent": "claude-sonnet-5"}'
```

**Override one project:**

```bash
MODEL_DEV_GENAI_RESEARCH_SYSTEM=gpt-5.6-luna   # dev only
MODEL_GENAI_RESEARCH_SYSTEM=gpt-5.6-luna        # both envs
```

**Override per request (header — highest priority):**

```bash
curl -H "X-LLM-Model: claude-sonnet-5" -H "X-LLM-Provider: anthropic" ...
```

**Priority:** request header > per-project env var > `PROJECT_MODELS_JSON` > `MODEL_DEFAULT_<ENV>`

---

## Environment Variables Quick Reference

| Variable | Default | Purpose |
|---|---|---|
| `APP_ENV` | `dev` | `dev` or `prod` |
| `GENAI_SYSTEMS_LAB_JWT_SECRET` | ephemeral | JWT signing secret (≥16 chars, required in prod) |
| `GENAI_SYSTEMS_LAB_BYOK_ENCRYPTION_KEY` | — | Fernet key for queued-job API key encryption |
| `GENAI_SYSTEMS_LAB_DATABASE_URL` | SQLite | PostgreSQL URL for production |
| `GENAI_SYSTEMS_LAB_REDIS_URL` | `redis://localhost:6379/0` | Redis for queued jobs |
| `GENAI_SYSTEMS_LAB_ALLOWED_ORIGINS` | `http://localhost:8513` | CORS origin allowlist |
| `GENAI_SYSTEMS_LAB_ENABLE_PUBLIC_SIGNUP` | `false` in prod | Allow unauthenticated signup |
| `GENAI_SYSTEMS_LAB_ENABLE_UNSAFE_AGENTS` | `false` | Enable `lg-debugging-agent` (dev only) |
| `MODEL_DEFAULT_DEV` | `gemini-3.7-flash` | Default model in dev |
| `MODEL_DEFAULT_PROD` | `gemini-3.7-flash` | Default model in prod |
| `PROJECT_MODELS_JSON` | `{}` | Per-project model overrides (JSON) |
| `OTEL_ENABLED` | `false` | OpenTelemetry tracing |
| `LANGFUSE_ENABLED` | `false` | Langfuse LLM observability |

Full list: [TECHNICAL.md — Environment Variables](TECHNICAL.md#environment-variables) · [.env.example](.env.example)

---

## Deploying with Docker Compose

```bash
# Copy and populate the env template
cp .env.example .env
# Required: GENAI_SYSTEMS_LAB_JWT_SECRET, GENAI_SYSTEMS_LAB_BYOK_ENCRYPTION_KEY,
#           POSTGRES_PASSWORD, APP_ENV=prod

# Build and start all services
docker compose up --build
```

Services:
- `postgres` — PostgreSQL 17 (`postgres:17-alpine`)
- `redis` — Redis 8 (`redis:8-alpine`)
- `api` — FastAPI on port 8514 (applies migrations on startup)
- `worker` — RQ worker for queued jobs

> [!WARNING]
> Never commit a populated `.env` file. It is already excluded by `.gitignore`.

> [!IMPORTANT]
> In production: set `APP_ENV=prod`, provide a strong `GENAI_SYSTEMS_LAB_JWT_SECRET`, and set `GENAI_SYSTEMS_LAB_ALLOWED_ORIGINS` to your deployed frontend URL.

**Frontend:** the Next.js portfolio is not included in the Docker Compose stack. Build and deploy it separately:

```bash
cd portfolio
NEXT_PUBLIC_API_BASE_URL=https://your-api.example.com npm run build
npm start
```

Or deploy `portfolio/` as a Vercel project with `NEXT_PUBLIC_API_BASE_URL` set.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `401 Unauthorized` | Token expired or missing | Re-login; refresh Bearer token or cookie |
| `422 Unprocessable Entity` | Invalid request body | Check field names; `input` is the main field; `session_id` is optional int |
| `404 Not Found` on `/project/run` | Project name wrong or not discovered | Run `GET /projects`; ensure `app/main.py` exists in directory |
| `503 Service Unavailable` | Project unavailable | Check `GENAI_SYSTEMS_LAB_ENABLE_UNSAFE_AGENTS`; confirm project in `/projects` |
| `429 Too Many Requests` | Rate limit exceeded | Wait and retry; login = 10/min; signup = 5/min; stream = 30/min; explain = 20/min; eval = 6 per 5 min |
| SSE stream disconnects immediately | Missing or invalid API key | Confirm `X-API-Key` header is set and valid for the provider |
| Job stays `queued` forever | Worker not running | Start a worker: `uv run rq worker --url $GENAI_SYSTEMS_LAB_REDIS_URL` |
| Job `failed` with encryption error | Missing Fernet key | Set `GENAI_SYSTEMS_LAB_BYOK_ENCRYPTION_KEY`; generate with `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` |
| `RuntimeError: No API key available` | BYOK header missing | Add `X-API-Key: <your-key>` header |
| Cookie not sent in requests | SameSite policy | In prod with HTTPS, set `GENAI_SYSTEMS_LAB_AUTH_COOKIE_SAMESITE=none` |
| OpenAPI docs not loading | API not running | Check `http://localhost:8514/health`; review uvicorn startup output |
| `docker compose` build fails | Missing env vars | Ensure `POSTGRES_PASSWORD` is set in `.env` |
| `uv sync` fails | Missing uv | Install: `pip install uv` or `curl -LsSf https://astral.sh/uv/install.sh \| sh` |

---

## Further Reading

- [TECHNICAL.md](TECHNICAL.md) — Full API reference, schemas, env vars, data models, middleware
- [portfolio/USAGE.md](portfolio/USAGE.md) — Step-by-step frontend guide
- [ARCHITECTURE.md](ARCHITECTURE.md) — Platform design philosophy
- [CONTRIBUTING.md](CONTRIBUTING.md) — Dev setup, test commands, PR rules
- [.env.example](.env.example) — Annotated environment variable template

---

<p align="center">Made with ❤️ by Ahmad Mujtaba</p>
