# Technical Reference — GenAI Systems Lab

**v1.2.0** · [GitHub](https://github.com/pypi-ahmad/genai-systems-lab) · [Usage Guide](USAGE.md) · [Architecture](ARCHITECTURE.md)

A comprehensive reference for the platform's API, schemas, environment variables, data models, middleware stack, and internal subsystems.

---

## Table of Contents

- [Platform Architecture](#platform-architecture)
- [Project Contract](#project-contract)
- [API Routes](#api-routes)
- [Request Headers](#request-headers)
- [Request / Response Schemas](#request--response-schemas)
- [Environment Variables](#environment-variables)
- [Data Models](#data-models)
- [Middleware Stack](#middleware-stack)
- [BYOK Key Resolution](#byok-key-resolution)
- [Authentication](#authentication)
- [Session Memory](#session-memory)
- [Confidence Scoring](#confidence-scoring)
- [LLM Dispatch](#llm-dispatch)
- [Queue System](#queue-system)
- [SSE Streaming](#sse-streaming)
- [Evaluation](#evaluation)

---

## Platform Architecture

The platform is a single FastAPI process that auto-discovers 20 AI project modules at startup. Every module implements one contract (`run()`), and the platform provides everything else: auth, validation, LLM dispatch, streaming, persistence, metrics, eval.

### Module map

| Path | Responsibility |
|---|---|
| `shared/api/app.py` | FastAPI factory, all 25 routes, full middleware stack |
| `shared/api/models.py` | SQLAlchemy ORM: `User`, `RunSession`, `Run`, `OperationalMetric`, `Job` |
| `shared/api/auth.py` | JWT lifecycle, PBKDF2 hashing, cookie management |
| `shared/api/runner.py` | Project auto-discovery, 29-alias resolution, dynamic import, `run()` dispatch |
| `shared/api/session_memory.py` | 12-entry window, 4-entry context injection, dedup |
| `shared/api/confidence.py` | Composite 4-component confidence score |
| `shared/api/eval_runner.py` | Benchmark suite execution and latency percentiles |
| `shared/api/jobs.py` | RQ job creation and cancellation |
| `shared/api/run_explainer.py` | LLM-backed structured run explanation |
| `shared/api/step_events.py` | `ContextVar`-based `StepEmitter` for SSE |
| `shared/api/langgraph_events.py` | `instrument_node` wrapper for LangGraph SSE |
| `shared/schemas/common.py` | All Pydantic request/response schemas |
| `shared/config.py` | `Settings`, BYOK `ContextVar` bindings, model resolution |
| `shared/llm/dispatch.py` | Provider routing from request-scoped `ContextVar` values |
| `shared/llm/catalog.py` | Static provider catalog + dynamic Ollama discovery |
| `shared/llm/gemini_provider.py` | Gemini `google-genai` SDK client (cached per key) |
| `shared/llm/providers.py` | HTTP clients for OpenAI, Anthropic, xAI, Ollama (zero SDK deps) |
| `shared/eval/benchmarks.py` | Per-project benchmark datasets (all 20 projects) |
| `shared/project_catalog.py` | `project-catalog.json` loader; `PIPELINE_NODES` for synthetic SSE |

---

## Project Contract

Every AI project module must expose a single `run()` function:

```python
# <project-dir>/app/main.py
def run(input: str, api_key: str) -> dict:
    ...
    return {"output": "...", ...}  # any dict; platform reads "output" as str
```

| Parameter | Notes |
|---|---|
| `input` | Task string, already session-prepended by the platform when `session_id` is set |
| `api_key` | BYOK key from `BYOKMiddleware`; prefer `get_effective_api_key()` from `shared.config` |

**Auto-discovery:** any directory at the repo root containing `app/main.py` is registered at startup. No manual registration required.

**Alias resolution:** 29 aliases are maintained in `shared/api/runner.py` — 20 from the project catalog and 9 legacy names (e.g. `nl2sql-agent` → `genai-nl2sql-agent`). Prefix-stripped names also work (`research-system` → `genai-research-system`).

**Security exclusion:** `lg-debugging-agent` executes model-generated Python and is removed from all shared API/eval surfaces unless `GENAI_SYSTEMS_LAB_ENABLE_UNSAFE_AGENTS=true` **and** `APP_ENV != prod`.

---

## API Routes

Backend default: `http://localhost:8514`. All routes return JSON. OpenAPI docs at `/docs`.

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/` | — | Service identity, version |
| `GET` | `/health` | — | `{"status": "ok"}` |
| `GET` | `/llm/catalog` | — | All providers, models, pricing, effort options; dynamic Ollama discovery |
| `GET` | `/projects` | — | List all auto-discovered project names |
| `GET` | `/auth/config` | — | `{"public_signup": bool}` |
| `POST` | `/auth/signup` | — | Create account (201); sets HttpOnly `genai_session` cookie |
| `POST` | `/auth/login` | — | Authenticate (200); sets HttpOnly `genai_session` cookie |
| `POST` | `/auth/logout` | JWT/cookie | Clear session cookie |
| `GET` | `/auth/me` | JWT/cookie | `{"id": int, "email": str}` |
| `POST` | `/{project}/run` | Optional JWT/cookie + `X-API-Key` | Synchronous execution; guest runs skip history/session |
| `GET` | `/stream/{project}` | Optional JWT/cookie + `X-API-Key` | SSE streaming execution |
| `POST` | `/jobs/{project}` | JWT/cookie + `X-API-Key` | Enqueue job (202); owner-scoped; requires Redis |
| `GET` | `/jobs/{job_id}` | JWT/cookie | Job status + output; cross-user UUIDs return 404 |
| `DELETE` | `/jobs/{job_id}` | JWT/cookie | Cancel queued/running job; returns 409 if terminal |
| `GET` | `/metrics` | — | Aggregate request count, latency, success rate (in-memory + persisted) |
| `GET` | `/metrics/time` | — | Time-series bucketed metrics (`?range=hour\|day\|week&project=...`) |
| `GET` | `/history` | JWT/cookie | Cursor-paginated run history (`?limit=50&before_id=<int>&project=...`) |
| `GET` | `/run/{run_id}` | JWT/cookie | Single saved run detail |
| `GET` | `/session/{session_id}` | JWT/cookie | Session memory state (last 5 entries) |
| `POST` | `/session/{session_id}/clear` | JWT/cookie | Wipe session memory |
| `POST` | `/explain/{run_id}` | JWT/cookie + `X-API-Key` | Structured LLM explanation from stored artifacts; rate-limited 20/min |
| `POST` | `/run/{run_id}/share` | JWT/cookie | Create public share link; TTL 7 days default, max 30 days |
| `DELETE` | `/run/{run_id}/share` | JWT/cookie | Revoke public share |
| `GET` | `/shared/{share_token}` | — | View public shared run (no auth) |
| `POST` | `/eval/{project}` | `X-API-Key` | Run benchmark suite; rate-limited 6 requests per 5 minutes |

> [!NOTE]
> `Authorization: Bearer <token>` and the HttpOnly `genai_session` cookie are both accepted on all authenticated routes. Query-string JWTs (`?token=...`) are **never** accepted on any route, including the SSE stream.

---

## Request Headers

| Header | Required | Description |
|---|---|---|
| `Authorization` | Auth routes | `Bearer <jwt>` |
| `X-API-Key` | LLM routes | Provider API key (not needed for Ollama) |
| `X-LLM-Provider` | No | Force provider: `gemini` `openai` `anthropic` `xai` `agnes` `ollama` |
| `X-LLM-Model` | No | Override model ID (takes precedence over all config) |
| `X-LLM-Effort` | No | Reasoning effort: `none` `low` `medium` `high` `xhigh` `max` |

---

## Request / Response Schemas

All schemas are defined in `shared/schemas/common.py`.

### Auth

| Schema | Fields |
|---|---|
| `AuthRequest` | `email: str` (min 3), `password: str` (min 8) |
| `AuthResponse` | `token: str`, `user: AuthUserResponse` |
| `AuthUserResponse` | `id: int`, `email: str` |
| `AuthConfigResponse` | `public_signup: bool` |

### Run

| Schema | Fields |
|---|---|
| `BaseRequest` | `input: str = ""`, `session_id: int \| None = None` |
| `BaseResponse` | `output: str`, `latency: float`, `confidence: float`, `session_id: int \| None`, `session_memory: list[str]`, `used_session_context: bool`, `success: bool`, `memory: list[RunMemoryEntryResponse]`, `timeline: list[RunTimelineEntryResponse]`, `usage: UsageResponse \| None` |
| `RunMemoryEntryResponse` | `step: str`, `content: str`, `type: str` |
| `RunTimelineEntryResponse` | `timestamp: float`, `step: str`, `event: str`, `data: str` |

### Usage / Cost

| Schema | Fields |
|---|---|
| `UsageResponse` | `input_tokens: int`, `output_tokens: int`, `total_tokens: int`, `estimated_cost_usd: float \| None`, `models_used: list[str]`, `cost_breakdown: list[UsageCostBreakdownResponse]` |
| `UsageCostBreakdownResponse` | `model: str`, `pricing_tier: "standard"\|"long_context"`, `input_tokens: int`, `cached_input_tokens: int`, `output_tokens: int`, `input_rate_per_million_usd: float`, `cached_input_rate_per_million_usd: float \| None`, `output_rate_per_million_usd: float`, `input_cost_usd: float`, `output_cost_usd: float`, `estimated_cost_usd: float` |

### History

| Schema | Fields |
|---|---|
| `HistoryRunResponse` | `id: int`, `user_id: int`, `session_id: int \| None`, `project: str`, `input: str`, `output: str`, `memory: list[RunMemoryEntryResponse]`, `timeline: list[RunTimelineEntryResponse]`, `latency: float`, `confidence: float`, `success: bool`, `timestamp: str \| None`, `share_token: str \| None`, `is_public: bool`, `expires_at: str \| None`, `prompt_tokens: int \| None`, `completion_tokens: int \| None`, `total_tokens: int \| None`, `cost_usd: float \| None`, `model_used: str \| None` |
| `HistoryResponse` | `count: int`, `runs: list[HistoryRunResponse]` |

### Session

| Schema | Fields |
|---|---|
| `SessionResponse` | `id: int`, `user_id: int`, `memory: list[str]`, `entry_count: int`, `updated_at: str \| None` |

### Jobs

| Schema | Fields |
|---|---|
| `JobResponse` | `id: str`, `project: str`, `status: Literal["queued","running","succeeded","failed","cancelled"]`, `output: str \| None`, `error: str \| None`, `usage: UsageResponse \| None`, `created_at: str \| None`, `started_at: str \| None`, `finished_at: str \| None` |

### Share

| Schema | Fields |
|---|---|
| `ShareRunRequest` | `expires_in_hours: int \| None = None` (max 720 hours / 30 days; omit for no expiry) |
| `ShareRunResponse` | `share_token: str`, `is_public: bool`, `expires_at: str \| None` |
| `SharedRunResponse` | Full run data without `user_id`; publicly accessible |

### Explain

| Schema | Fields |
|---|---|
| `RunExplanationResponse` | `steps_taken: list[RunExplanationStepResponse]`, `key_decisions: list[RunExplanationDecisionResponse]`, `final_reasoning: str`, `final_outcome: str` |
| `RunExplanationStepResponse` | `step: str`, `what_happened: str`, `why_it_mattered: str` |
| `RunExplanationDecisionResponse` | `decision: str`, `reason: str` |

### Metrics

| Schema | Fields |
|---|---|
| `MetricsResponse` | `total_requests: int`, `avg_latency: float`, `success_rate: float`, `projects: list[ProjectMetricsResponse]` |
| `ProjectMetricsResponse` | `name: str`, `latency: float`, `success_rate: float` |
| `TimeSeriesMetricPointResponse` | `timestamp: str`, `latency: float`, `confidence: float`, `success: bool` |

### LLM Catalog

| Schema | Fields |
|---|---|
| `LLMCatalogResponse` | `default_model: str`, `providers: list[LLMProviderResponse]` |
| `LLMProviderResponse` | `id: str`, `label: str`, `requires_api_key: bool`, `api_key_label: str`, `api_key_help_url: str \| None`, `api_key_placeholder: str`, `available: bool`, `unavailable_reason: str \| None`, `models: list[LLMModelOptionResponse]` |
| `LLMModelOptionResponse` | `id: str`, `label: str`, `provider: Literal[gemini\|openai\|anthropic\|xai\|agnes\|ollama]`, `effort_options: list[str]`, `pricing: dict[str, float\|int\|str] \| None` |

---

## Environment Variables

All variables from `shared/config.py` and `.env.example`:

| Variable | Default | Description |
|---|---|---|
| `APP_ENV` | `dev` | `dev` or `prod`. Controls signup posture, unsafe-agent gate, JWT secret enforcement |
| `GENAI_SYSTEMS_LAB_JWT_SECRET` | ephemeral per-process | HS256 signing key; must be ≥ 16 chars; **required** in prod |
| `GENAI_SYSTEMS_LAB_JWT_TTL_SECONDS` | `604800` (7 days) | JWT token lifetime |
| `GENAI_SYSTEMS_LAB_ALLOWED_ORIGINS` | `http://localhost:8513,...` | Comma-separated CORS origin allowlist |
| `GENAI_SYSTEMS_LAB_ENABLE_PUBLIC_SIGNUP` | `true` in dev, `false` in prod | Allow unauthenticated `/auth/signup` |
| `GENAI_SYSTEMS_LAB_ENABLE_UNSAFE_AGENTS` | `false` | Enable `lg-debugging-agent` in dev; always ignored in prod |
| `GENAI_SYSTEMS_LAB_DATABASE_URL` | SQLite `.data/genai_systems_lab.db` | SQLAlchemy DB URL; set PostgreSQL URL for production |
| `DATABASE_URL` | — | Fallback if `GENAI_SYSTEMS_LAB_DATABASE_URL` is not set |
| `GENAI_SYSTEMS_LAB_REDIS_URL` | `redis://localhost:6379/0` | Redis URL for queued job execution |
| `GENAI_SYSTEMS_LAB_BYOK_ENCRYPTION_KEY` | — | Fernet key for encrypting queued-job API keys in Redis |
| `GENAI_SYSTEMS_LAB_AUTH_COOKIE_SAMESITE` | `lax` | Cookie `SameSite` policy: `lax` `strict` `none` |
| `GENAI_SYSTEMS_LAB_AUTH_COOKIE_SECURE` | `true` in prod | Set `Secure` flag on session cookie |
| `GENAI_SYSTEMS_LAB_AUTH_COOKIE_NAME` | `genai_systems_lab_session` | Session cookie name |
| `GENAI_SYSTEMS_LAB_DISABLE_RATE_LIMITS` | `false` | Bypass all rate limiting (testing only) |
| `GENAI_SYSTEMS_LAB_TRUSTED_PROXIES` | — | Comma-separated trusted proxy IPs for `X-Forwarded-For` |
| `POSTGRES_PASSWORD` | — | PostgreSQL password for Docker Compose |
| `OLLAMA_BASE_URL` | `http://127.0.0.1:11434` | Local Ollama server URL |
| `OPENAI_EMBEDDING_MODEL` | `text-embedding-3-small` | OpenAI embedding model |
| `GEMINI_EMBEDDING_MODEL` | `gemini-embedding-2-preview` | Gemini embedding model |
| `OLLAMA_EMBEDDING_MODEL` | `embeddinggemma` | Ollama embedding model |
| `OTEL_ENABLED` | `false` | Enable OpenTelemetry startup wiring |
| `OTEL_CONSOLE_EXPORT` | `false` | Mirror spans to console exporter |
| `OTEL_SERVICE_NAME` | `genai-systems-lab` | OTel service name |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `http://localhost:4317` | OTLP gRPC collector endpoint |
| `LANGFUSE_ENABLED` | `false` | Enable Langfuse LLM tracing |
| `LANGFUSE_SECRET_KEY` | — | Langfuse project secret key |
| `LANGFUSE_PUBLIC_KEY` | — | Langfuse project public key |
| `LANGFUSE_HOST` | `https://cloud.langfuse.com` | Langfuse server (cloud or self-hosted) |
| `MODEL_DEFAULT_DEV` | `gemini-3.7-flash` | Default LLM model in dev |
| `MODEL_DEFAULT_PROD` | `gemini-3.7-flash` | Default LLM model in prod |
| `PROJECT_MODELS_JSON` | `{}` | JSON object mapping project slug → model override |

**Per-project model overrides (highest priority after request header):**

```
MODEL_DEV_<PROJECT_KEY>=<model>   # dev only, e.g. MODEL_DEV_GENAI_RESEARCH_SYSTEM
MODEL_<PROJECT_KEY>=<model>       # both envs
```

`PROJECT_KEY` is the project directory name uppercased with hyphens replaced by underscores.

---

## Data Models

SQLAlchemy ORM tables defined in `shared/api/models.py`.

### `users`

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PK | Auto-increment |
| `email` | TEXT UNIQUE NOT NULL | |
| `password_hash` | TEXT NOT NULL | PBKDF2-HMAC-SHA256, 310k iterations, 16-byte salt |
| `created_at` | DATETIME | UTC |

### `sessions`

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PK | |
| `user_id` | INTEGER FK → users | |
| `memory` | TEXT | JSON array of `"User: ... \| Agent: ..."` strings |
| `created_at` | DATETIME | |
| `updated_at` | DATETIME | |

### `runs`

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PK | |
| `user_id` | INTEGER FK → users | Nullable (guest runs) |
| `session_id` | INTEGER FK → sessions | Nullable |
| `project` | TEXT NOT NULL | |
| `input` | TEXT NOT NULL | |
| `output` | TEXT | |
| `memory` | TEXT | JSON array of memory entry objects |
| `timeline` | TEXT | JSON array of timeline entry objects |
| `latency_ms` | REAL | |
| `confidence` | REAL | |
| `success` | BOOLEAN | |
| `timestamp` | DATETIME | UTC |
| `share_token` | TEXT UNIQUE | Nullable; set on share creation |
| `is_public` | BOOLEAN | Default false |
| `expires_at` | DATETIME | Nullable; share expiry |

### `operational_metrics`

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PK | |
| `project` | TEXT NOT NULL | |
| `latency_ms` | REAL | |
| `confidence` | REAL | |
| `success` | BOOLEAN | |
| `timestamp` | DATETIME | UTC; indexed |

### `jobs`

| Column | Type | Notes |
|---|---|---|
| `id` | TEXT PK | UUID |
| `user_id` | INTEGER FK → users | Owner; cross-user lookup → 404 |
| `project` | TEXT NOT NULL | |
| `status` | TEXT | `queued` `running` `succeeded` `failed` `cancelled` |
| `input` | TEXT | |
| `output` | TEXT | Nullable until complete |
| `error` | TEXT | Nullable |
| `usage` | TEXT | JSON; `UsageResponse`-shaped |
| `created_at` | DATETIME | |
| `started_at` | DATETIME | Nullable |
| `finished_at` | DATETIME | Nullable |

---

## Middleware Stack

Applied outermost → innermost in `shared/api/app.py`:

| Class | Purpose |
|---|---|
| `GZipMiddleware` | Compress responses ≥ 1 KB; skips SSE streams |
| `CORSMiddleware` | Explicit `GENAI_SYSTEMS_LAB_ALLOWED_ORIGINS` allowlist; `allow_credentials=True` |
| `RequestRateLimitMiddleware` | Per-IP sliding window: signup 5/60s, login 10/60s, eval 6/300s, stream 30/60s, explain 20/60s, default 120/60s |
| `BYOKMiddleware` | Binds `X-API-Key`, `X-LLM-Provider`, `X-LLM-Model`, `X-LLM-Effort` headers to `ContextVar` for request duration |
| `InputValidationMiddleware` | POST/PUT/PATCH: rejects empty `input`, inputs > 10,000 chars, and payloads matching XSS/SQL-injection/JS-protocol/null-byte patterns; HTML-escapes remaining strings |
| `SecurityHeadersMiddleware` | Adds `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy`, `Cross-Origin-Opener-Policy`, `Cross-Origin-Resource-Policy` |
| `RequestLoggingMiddleware` | Assigns `request_id`; structured request/response logs with project name |
| `RequestTimingMiddleware` | Adds `X-Process-Time-Ms` response header; opens OTel span when enabled |
| `ErrorHandlingMiddleware` | Catches unhandled exceptions; returns scrubbed JSON `{"detail": "..."}` — internal stack traces never reach the client |

---

## BYOK Key Resolution

```
Request arrives
  │
  └─ BYOKMiddleware reads headers:
       X-API-Key        → _BYOK_API_KEY     (ContextVar)
       X-LLM-Provider   → _REQUEST_PROVIDER (ContextVar)
       X-LLM-Model      → _REQUEST_MODEL    (ContextVar)
       X-LLM-Effort     → _REQUEST_EFFORT   (ContextVar)
  │
  └─ Route handler calls get_effective_api_key():
       if _BYOK_API_KEY is set  → return it
       if provider is "ollama"  → return "" (no key required)
       else                     → raise RuntimeError("No API key available")
  │
  └─ Key used for this request only; never logged; never written to any DB row
  │
  └─ Queued jobs only:
       Key is Fernet-encrypted with GENAI_SYSTEMS_LAB_BYOK_ENCRYPTION_KEY
       Stored in Redis with 1-hour TTL
       Deleted when the RQ worker consumes or cancels the job
```

> [!IMPORTANT]
> Keys from `.env` are NOT used at runtime. Every LLM call must come with an explicit `X-API-Key` header (or use Ollama).

---

## Authentication

| Concern | Implementation |
|---|---|
| Token type | JWT HS256 via PyJWT; decode allowlist `["HS256"]` blocks `alg:none` and RS/HS confusion attacks |
| Payload | `{sub, email, iat, exp}` with 7-day TTL (`GENAI_SYSTEMS_LAB_JWT_TTL_SECONDS`) |
| Cookie | HttpOnly `genai_session` cookie set on signup/login; `SameSite` via `GENAI_SYSTEMS_LAB_AUTH_COOKIE_SAMESITE` |
| Password | PBKDF2-HMAC-SHA256, 310,000 iterations, 16-byte random salt, `hmac.compare_digest()` for timing safety |
| Prod requirement | `GENAI_SYSTEMS_LAB_JWT_SECRET` ≥ 16 chars required; missing = startup error |
| Dev fallback | Ephemeral per-process secret; clear warning logged on startup |
| Signup posture | `APP_ENV=prod` → signup off by default; override with `GENAI_SYSTEMS_LAB_ENABLE_PUBLIC_SIGNUP=true` |
| Rate limits | Login + signup: 10 req/min per IP |

---

## Session Memory

Stored in the `sessions.memory` column as a JSON array.

| Parameter | Value |
|---|---|
| Window size | 12 entries max |
| Deduplication | Against last 2 entries by normalized content |
| Context injection | Last 4 entries prepended as `Previous context:\n` prefix on subsequent runs |
| Entry format | `"User: <input_preview> \| Agent: <output_preview>"` — max 620 chars per entry |
| Guest runs | Session memory skipped entirely (no `session_id` returned) |

**Lifecycle:**
1. Run completes → entry appended to session window
2. Window trimmed to 12 entries + dedup
3. Next run in same session → last 4 entries injected as context prefix before dispatch
4. `POST /session/{id}/clear` wipes the array

---

## Confidence Scoring

```
confidence = 0.4 × evaluator + 0.3 × execution + 0.2 × consistency + 0.1 × latency
```

Implemented in `shared/api/confidence.py`:

| Component | Weight | How derived |
|---|---|---|
| Evaluator score | 0.4 | Extracted from output fields: `confidence`, `accuracy`, `score`, `quality_score`, `quality`, `evaluation_score`, `eval_score` — or inferred from output structure (presence of structured keys) |
| Execution success | 0.3 | `1.0` if run succeeded, `0.0` on any failure |
| Consistency score | 0.2 | `1 / (1 + retries)` — inferred from `retry_count` or `retries` in output dict or timeline entries |
| Latency score | 0.1 | `5000 / (5000 + latency_ms)` — asymptotes toward 0 for slow runs |

---

## LLM Dispatch

`shared/llm/dispatch.py` resolves provider and model per request:

**Provider resolution order:**
1. `_REQUEST_PROVIDER` ContextVar (from `X-LLM-Provider` header)
2. `infer_provider(model_id)` — matches known model prefixes to providers
3. Unknown model ID → Ollama (local fallback)

**Model resolution order:**
1. `_REQUEST_MODEL` ContextVar (from `X-LLM-Model` header)
2. `MODEL_{ENV}_{PROJECT_KEY}` env var (dev/prod-specific)
3. `MODEL_{PROJECT_KEY}` env var (both envs)
4. `PROJECT_MODELS_JSON` — JSON mapping in env
5. `MODEL_DEFAULT_{ENV}` — `gemini-3.7-flash` by default

**Providers:**

| Provider | Implementation | SDK/method |
|---|---|---|
| `gemini` | `shared/llm/gemini_provider.py` | `google-genai` SDK; client cached per API key |
| `openai` | `shared/llm/providers.py` | Raw `urllib.request` HTTP; zero SDK deps |
| `anthropic` | `shared/llm/providers.py` | Raw `urllib.request` HTTP; zero SDK deps |
| `xai` | `shared/llm/providers.py` | OpenAI-compatible responses API |
| `agnes` | `shared/llm/providers.py` | HTTP; never a runtime env fallback |
| `ollama` | `shared/llm/providers.py` | Local HTTP on `OLLAMA_BASE_URL`; no key required |

**Shared retry/backoff:** 3 attempts, exponential backoff (1 s → 2 s → 4 s), 120 s timeout per attempt.

---

## Queue System

Requires Redis (`GENAI_SYSTEMS_LAB_REDIS_URL`) and `GENAI_SYSTEMS_LAB_BYOK_ENCRYPTION_KEY`.

| Step | Detail |
|---|---|
| Enqueue | `POST /jobs/{project}` → RQ job created → `202 Accepted` with `JobResponse` |
| Ownership | `user_id` from JWT stored in job record; cross-user UUID lookups return `404` |
| Storage | Job state persisted to `jobs` table (SQLite/PostgreSQL) |
| Key lifecycle | API key Fernet-encrypted → stored in Redis key `job:{id}:api_key` → 1-hour TTL → deleted when worker starts |
| Worker | Separate `rq worker` process; `docker compose up worker` or manual `uv run rq worker` |
| Cancellation | `DELETE /jobs/{id}` — queued or running → `cancelled`; terminal state → `409 Conflict` |

---

## SSE Streaming

`GET /stream/{project}` — uses `text/event-stream` response type.

| Event | Payload format | When emitted |
|---|---|---|
| `step` | `{"step": "<node_id>", "status": "running\|done\|error"}` | Per pipeline node; native projects use `emit_step()`, others use catalog-derived `PIPELINE_NODES` |
| `token` | `{"token": "<delta>"}` | Incremental tokens from `genai-research-system` and `lg-research-agent` only |
| `output` | `{"output": "<full text>"}` | Non-token projects after completion |
| `done` | Full `BaseResponse` payload (JSON) | Run complete; includes latency, confidence, memory, timeline |
| `error` | `{"error": "<scrubbed>", "code": 5xx}` | On failure; internal detail never reaches client |

**Auth on SSE:** JWT via `Authorization` header or HttpOnly cookie. Query-string tokens rejected.

---

## Evaluation

`POST /eval/{project}` — rate-limited to 6 requests per 5 minutes.

| Field | Description |
|---|---|
| Benchmark datasets | `shared/eval/benchmarks.py` — rule-based test cases for all 20 projects |
| Metrics returned | Per-case pass/fail, overall accuracy, latency percentiles (mean, p50, p95, p99) |
| CI gate | `backend-platform` job discovers and runs every `test_*.py` under `crew-*`, `genai-*`, `lg-*` directories |
| Provider-backed eval | Runs only when the relevant CI secrets are configured |

---

## Error Responses

All errors return JSON with a `detail` field:

| Status | Meaning |
|---|---|
| `400` | Bad request (validation, malformed body) |
| `401` | Missing or invalid JWT/cookie |
| `403` | Forbidden (e.g. project excluded, wrong owner) |
| `404` | Run/job/session not found (also returned for cross-user job UUIDs) |
| `409` | Conflict (e.g. cancelling a terminal job) |
| `422` | Unprocessable entity (Pydantic schema mismatch) |
| `429` | Rate limit exceeded |
| `503` | Project unavailable (optional runtime not installed, unsafe agent disabled) |

---

## Repository

- GitHub: <https://github.com/pypi-ahmad/genai-systems-lab>
- License: MIT — see [LICENSE](LICENSE)
- How-to guide: [USAGE.md](USAGE.md)
- Architecture: [ARCHITECTURE.md](ARCHITECTURE.md)

---

<p align="center">Made with ❤️ by Ahmad Mujtaba</p>
