"""FastAPI application factory for project-level APIs."""

from __future__ import annotations

import asyncio
from collections import deque
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
import json
import os
import re
import threading
import time
from typing import Any, Literal

from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from pydantic import ValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import StreamingResponse

import secrets as _secrets
from datetime import timezone as _timezone

from .auth import AUTH_COOKIE_NAME, JWT_TTL_SECONDS, authenticate_user, create_access_token, create_user, get_current_user, get_optional_current_user, save_run, serialize_run
from .confidence import compute_run_confidence
from .db import get_db_session, init_db
from .eval_runner import run_project_evaluation
from .models import OperationalMetric, Run, RunSession, User
from .run_explainer import build_run_explanation
from .runner import ProjectUnavailableError, list_available, resolve_project_name, run_project
from .session_memory import (
    build_session_prompt,
    deserialize_session_memory_entries,
    preview_session_memory_entries,
    serialize_session_memory_entries,
    update_session_memory_entries,
)
from shared.config import get_effective_api_key, get_request_model, get_request_provider, reset_byok_api_key, reset_request_model, reset_request_provider, set_byok_api_key, set_request_model, set_request_provider
from shared.llm import GeminiGenerationError, GeminiTimeoutError
from shared.llm.catalog import build_provider_catalog, get_model_spec, infer_provider, provider_requires_api_key
from shared.logging import get_logger, new_request_id, reset_log_context, set_log_context, setup_otel, shutdown_otel
from shared.logging.otel import span as otel_span
from shared.observability.langfuse import score_trace as score_langfuse_trace
from shared.project_catalog import build_pipeline_nodes_index, list_project_manifest_entries
from shared.schemas import AuthConfigResponse, AuthRequest, AuthResponse, AuthUserResponse, BaseRequest, BaseResponse, HistoryResponse, HistoryRunResponse, LLMCatalogResponse, MetricsResponse, RunExplanationResponse, SessionResponse, ShareRunRequest, ShareRunResponse, SharedRunResponse, StatusResponse, TimeSeriesMetricPointResponse

logger = get_logger(__name__)

MAX_INPUT_LENGTH = 10_000  # characters
MAX_HISTORY_PAGE_SIZE = 200
DEFAULT_HISTORY_PAGE_SIZE = 50
DEFAULT_SHARE_TTL_HOURS = 24 * 7  # Public share links auto-expire after 7 days by default.
MAX_SHARE_TTL_HOURS = 24 * 30
MemoryEntryPayload = dict[str, str]
TimelineEntryPayload = dict[str, str | float]
_DEFAULT_ALLOWED_ORIGINS = (
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
)
_CORS_ALLOWED_METHODS = ["DELETE", "GET", "OPTIONS", "PATCH", "POST", "PUT"]
_CORS_ALLOWED_HEADERS = ["Authorization", "Content-Type", "X-API-Key", "X-LLM-Model", "X-LLM-Provider", "X-Requested-With"]

# Only trust X-Forwarded-For when the immediate peer is a known reverse proxy.
# Leave empty in local dev; set in production via the env var.
_TRUSTED_PROXY_IPS = tuple(
    ip.strip()
    for ip in os.getenv("GENAI_SYSTEMS_LAB_TRUSTED_PROXIES", "").split(",")
    if ip.strip()
)


# -- In-memory metrics store ---------------------------------------------------

class _MetricsStore:
    """Thread-safe in-memory store for per-project request metrics."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._projects: dict[str, dict[str, Any]] = {}

    def record(self, project: str, latency_ms: float, success: bool) -> None:
        with self._lock:
            entry = self._projects.setdefault(
                project, {"requests": 0, "total_latency_ms": 0.0, "successes": 0}
            )
            entry["requests"] += 1
            entry["total_latency_ms"] += latency_ms
            if success:
                entry["successes"] += 1

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            total_requests = 0
            total_latency = 0.0
            total_successes = 0
            projects: list[dict[str, Any]] = []

            for name, entry in sorted(self._projects.items()):
                reqs = entry["requests"]
                avg_lat = entry["total_latency_ms"] / reqs if reqs else 0.0
                rate = entry["successes"] / reqs if reqs else 0.0
                total_requests += reqs
                total_latency += entry["total_latency_ms"]
                total_successes += entry["successes"]
                projects.append({
                    "name": name,
                    "latency": round(avg_lat, 2),
                    "success_rate": round(rate, 4),
                })

            return {
                "total_requests": total_requests,
                "avg_latency": round(
                    total_latency / total_requests if total_requests else 0.0, 2
                ),
                "success_rate": round(
                    total_successes / total_requests if total_requests else 0.0, 4
                ),
                "projects": projects,
            }


metrics_store = _MetricsStore()

MetricsTimeRange = Literal["hour", "day", "week"]


def _env_flag(name: str, default: bool) -> bool:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    return raw_value.strip().lower() in {"1", "true", "yes", "on"}


def _resolve_allowed_origins(explicit_origins: list[str] | None) -> list[str]:
    if explicit_origins is not None:
        candidates = explicit_origins
    else:
        configured = os.getenv("GENAI_SYSTEMS_LAB_ALLOWED_ORIGINS", "").strip()
        candidates = configured.split(",") if configured else list(_DEFAULT_ALLOWED_ORIGINS)

    cleaned: list[str] = []
    for candidate in candidates:
        origin = candidate.strip().rstrip("/")
        if origin and origin not in cleaned:
            cleaned.append(origin)

    return cleaned or list(_DEFAULT_ALLOWED_ORIGINS)


def _public_signup_enabled() -> bool:
    default_enabled = os.getenv("APP_ENV", "dev").strip().lower() != "prod"
    return _env_flag("GENAI_SYSTEMS_LAB_ENABLE_PUBLIC_SIGNUP", default_enabled)


def _auth_cookie_samesite() -> Literal["lax", "strict", "none"]:
    configured = os.getenv("GENAI_SYSTEMS_LAB_AUTH_COOKIE_SAMESITE", "lax").strip().lower()
    if configured in {"lax", "strict", "none"}:
        return configured
    return "lax"


def _auth_cookie_secure() -> bool:
    default_secure = os.getenv("APP_ENV", "dev").strip().lower() == "prod"
    return _env_flag("GENAI_SYSTEMS_LAB_AUTH_COOKIE_SECURE", default_secure)


def _set_auth_cookie(response: Response, token: str) -> None:
    same_site = _auth_cookie_samesite()
    secure = _auth_cookie_secure() or same_site == "none"
    response.set_cookie(
        key=AUTH_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=secure,
        samesite=same_site,
        max_age=JWT_TTL_SECONDS,
        path="/",
    )


def _clear_auth_cookie(response: Response) -> None:
    same_site = _auth_cookie_samesite()
    secure = _auth_cookie_secure() or same_site == "none"
    response.delete_cookie(
        key=AUTH_COOKIE_NAME,
        httponly=True,
        secure=secure,
        samesite=same_site,
        path="/",
    )


def _metrics_time_cutoff(time_range: MetricsTimeRange) -> datetime:
    now = datetime.now(UTC)
    if time_range == "hour":
        return now - timedelta(hours=1)
    if time_range == "week":
        return now - timedelta(days=7)
    return now - timedelta(days=1)


def _serialize_metric_point(run: Run) -> TimeSeriesMetricPointResponse:
    return TimeSeriesMetricPointResponse(
        timestamp=run.timestamp.isoformat() if run.timestamp else "",
        latency=round(run.latency_ms, 2),
        confidence=round(run.confidence_score, 2),
        success=run.success,
    )


def _serialize_operational_metric_point(metric: OperationalMetric) -> TimeSeriesMetricPointResponse:
    return TimeSeriesMetricPointResponse(
        timestamp=metric.timestamp.isoformat() if metric.timestamp else "",
        latency=round(metric.latency_ms, 2),
        confidence=round(metric.confidence_score, 2),
        success=metric.success,
    )


def _record_operational_metric(
    session: Session,
    *,
    project: str,
    latency_ms: float,
    confidence_score: float,
    success: bool,
) -> None:
    try:
        session.add(
            OperationalMetric(
                project=project,
                latency_ms=round(max(latency_ms, 0.0), 2),
                confidence_score=round(max(confidence_score, 0.0), 2),
                success=success,
            )
        )
        session.commit()
    except Exception as exc:
        session.rollback()
        logger.warning(
            "failed to persist operational metric",
            extra={"project_name": project, "error": str(exc)},
        )


def _score_langfuse_confidence(trace_id: str | None, confidence: float) -> None:
    if not trace_id:
        return

    score_langfuse_trace(
        trace_id=trace_id,
        name="confidence",
        value=round(confidence, 4),
        comment="Heuristic run confidence from API post-processing.",
    )


def _snapshot_persisted_metrics(session: Session) -> MetricsResponse:
    rows = session.execute(
        select(
            OperationalMetric.project,
            OperationalMetric.latency_ms,
            OperationalMetric.success,
        ).order_by(OperationalMetric.project.asc(), OperationalMetric.id.asc())
    ).all()

    if not rows:
        return MetricsResponse()

    total_requests = 0
    total_latency = 0.0
    total_successes = 0
    project_totals: dict[str, dict[str, float]] = {}

    for project_name, latency_ms, success in rows:
        total_requests += 1
        total_latency += float(latency_ms)
        total_successes += 1 if success else 0

        project_entry = project_totals.setdefault(
            project_name,
            {"requests": 0.0, "latency_ms": 0.0, "successes": 0.0},
        )
        project_entry["requests"] += 1
        project_entry["latency_ms"] += float(latency_ms)
        if success:
            project_entry["successes"] += 1

    projects = [
        {
            "name": project_name,
            "latency": round(values["latency_ms"] / values["requests"], 2),
            "success_rate": round(values["successes"] / values["requests"], 4),
        }
        for project_name, values in project_totals.items()
    ]

    return MetricsResponse(
        total_requests=total_requests,
        avg_latency=round(total_latency / total_requests if total_requests else 0.0, 2),
        success_rate=round(total_successes / total_requests if total_requests else 0.0, 4),
        projects=projects,
    )


# -- Pipeline node IDs per project (derived from shared project catalog) -------

PIPELINE_NODES = build_pipeline_nodes_index()


def _get_pipeline_nodes(project_name: str) -> list[str]:
    """Resolve streaming step node IDs for a requested project name."""
    direct = PIPELINE_NODES.get(project_name)
    if direct:
        return direct

    normalized = project_name.removeprefix("genai-").removeprefix("lg-").removeprefix("crew-")
    normalized_match = PIPELINE_NODES.get(normalized)
    if normalized_match:
        return normalized_match

    try:
        resolved = resolve_project_name(project_name)
    except ValueError:
        return []

    resolved_normalized = resolved.removeprefix("genai-").removeprefix("lg-").removeprefix("crew-")
    return PIPELINE_NODES.get(resolved_normalized, [])


def _format_memory_step(step_id: str) -> str:
    cleaned = step_id.replace("_", " ").replace("-", " ").strip()
    return cleaned.title() if cleaned else "Agent Step"


def _memory_entry_type(step_id: str, status: str) -> str:
    if status != "running":
        return "observation"

    normalized = step_id.lower()
    thought_keywords = (
        "plan",
        "planner",
        "schema",
        "spec",
        "critic",
        "evaluator",
        "validator",
        "review",
        "auditor",
        "analyzer",
        "classifier",
        "router",
        "coordinator",
    )
    if any(keyword in normalized for keyword in thought_keywords):
        return "thought"

    return "action"


def _memory_content(step_name: str, status: str, entry_type: str, error: str | None = None) -> str:
    if status == "running":
        if entry_type == "thought":
            return f"{step_name} is reasoning about the next best move."
        return f"{step_name} is executing its current task."

    if status == "done":
        return f"{step_name} finished and recorded its result."

    if error:
        return f"{step_name} failed: {error}"
    return f"{step_name} failed during execution."


def _build_memory_entry(step_id: str, status: str, *, error: str | None = None) -> MemoryEntryPayload:
    step_name = _format_memory_step(step_id)
    entry_type = _memory_entry_type(step_id, status)
    if status != "running":
        entry_type = "observation"

    return {
        "step": step_name,
        "type": entry_type,
        "content": _memory_content(step_name, status, entry_type, error),
    }


def _append_memory_entry(
    memory_entries: list[MemoryEntryPayload],
    step_id: str,
    status: str,
    *,
    error: str | None = None,
) -> None:
    memory_entries.append(_build_memory_entry(step_id, status, error=error))


def _append_timeline_entry(
    timeline_entries: list[TimelineEntryPayload],
    *,
    timestamp: float,
    step_id: str,
    event: str,
    data: str,
) -> None:
    timeline_entries.append({
        "timestamp": round(max(0.0, timestamp), 4),
        "step": step_id,
        "event": event,
        "data": data,
    })


def _append_execution_trace(
    memory_entries: list[MemoryEntryPayload],
    timeline_entries: list[TimelineEntryPayload],
    start_time: float,
    step_id: str,
    status: str,
    *,
    error: str | None = None,
) -> None:
    memory_entry = _build_memory_entry(step_id, status, error=error)
    memory_entries.append(memory_entry)
    _append_timeline_entry(
        timeline_entries,
        timestamp=time.perf_counter() - start_time,
        step_id=step_id,
        event=status,
        data=memory_entry["content"],
    )


def _append_result_memory_entry(
    memory_entries: list[MemoryEntryPayload],
    *,
    success: bool,
    latency_ms: float,
    output_text: str,
) -> None:
    content = (
        f"Run completed in {round(latency_ms, 2)} ms."
        if success
        else f"Run finished with an error after {round(latency_ms, 2)} ms."
    )
    if output_text and not success:
        content = f"{content} Output: {output_text[:240]}"

    memory_entries.append({
        "step": "Result",
        "type": "observation",
        "content": content,
    })


def _append_result_timeline_entry(
    timeline_entries: list[TimelineEntryPayload],
    *,
    start_time: float,
    success: bool,
    latency_ms: float,
    output_text: str,
) -> None:
    content = (
        f"Run completed in {round(latency_ms, 2)} ms."
        if success
        else f"Run finished with an error after {round(latency_ms, 2)} ms."
    )
    if output_text and not success:
        content = f"{content} Output: {output_text[:240]}"

    _append_timeline_entry(
        timeline_entries,
        timestamp=max(round(latency_ms / 1000, 4), time.perf_counter() - start_time),
        step_id="result",
        event="completed" if success else "failed",
        data=content,
    )


def _append_fallback_memory_entries(memory_entries: list[MemoryEntryPayload], project_name: str) -> None:
    if memory_entries:
        return

    for node_id in _get_pipeline_nodes(project_name):
        _append_memory_entry(memory_entries, node_id, "running")


def _append_fallback_timeline_entries(
    timeline_entries: list[TimelineEntryPayload],
    project_name: str,
) -> None:
    if timeline_entries:
        return

    for index, node_id in enumerate(_get_pipeline_nodes(project_name)):
        running_entry = _build_memory_entry(node_id, "running")
        done_entry = _build_memory_entry(node_id, "done")
        base_timestamp = index * 0.28
        _append_timeline_entry(
            timeline_entries,
            timestamp=base_timestamp + 0.04,
            step_id=node_id,
            event="running",
            data=running_entry["content"],
        )
        _append_timeline_entry(
            timeline_entries,
            timestamp=base_timestamp + 0.18,
            step_id=node_id,
            event="done",
            data=done_entry["content"],
        )


def _discover_projects() -> list[dict[str, str]]:
    """Return a list of runnable projects (folders containing app/main.py)."""
    available = set(list_available())
    items = list_project_manifest_entries(runnable_projects=available)
    known_slugs = {
        item["slug"]
        for item in items
        if isinstance(item, dict) and isinstance(item.get("slug"), str)
    }

    for project_name in sorted(available - known_slugs):
        items.append({"name": project_name, "slug": project_name})

    return items


def _serialize_session_payload(run_session: RunSession) -> dict[str, Any]:
    memory_entries = deserialize_session_memory_entries(run_session.memory_text)
    preview = preview_session_memory_entries(memory_entries)
    return {
        "id": run_session.id,
        "user_id": run_session.user_id,
        "memory": preview,
        "entry_count": len(memory_entries),
        "updated_at": run_session.updated_at.isoformat() if run_session.updated_at else None,
    }


def _resolve_run_session(
    session: Session,
    *,
    user_id: int,
    session_id: int | None,
) -> RunSession:
    if session_id is not None:
        run_session = session.scalar(
            select(RunSession).where(RunSession.id == session_id, RunSession.user_id == user_id)
        )
        if run_session is None:
            raise HTTPException(status_code=404, detail="Session not found.")
        return run_session

    run_session = RunSession(
        user_id=user_id,
        memory_text=serialize_session_memory_entries([]),
    )
    session.add(run_session)
    session.commit()
    session.refresh(run_session)
    return run_session


# -- Middleware ----------------------------------------------------------------

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log every incoming request and its response status."""

    async def dispatch(self, request: Request, call_next):  # noqa: ANN001
        request_id = request.headers.get("X-Request-ID") or new_request_id()
        project_name = request.path_params.get("project_name") or request.path_params.get("project")
        tokens = set_log_context(request_id=request_id, project_name=project_name)

        try:
            logger.info(
                "%s %s",
                request.method,
                request.url.path,
                extra={"request_id": request_id, "project_name": project_name or "-"},
            )
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            logger.info(
                "%s %s -> %s",
                request.method,
                request.url.path,
                response.status_code,
                extra={"request_id": request_id, "project_name": project_name or "-"},
            )
            return response
        finally:
            reset_log_context(tokens)


class RequestTimingMiddleware(BaseHTTPMiddleware):
    """Add an ``X-Process-Time-Ms`` header and record latency in log context."""

    async def dispatch(self, request: Request, call_next):  # noqa: ANN001
        start = time.perf_counter()
        with otel_span(
            "http_request",
            attributes={
                "http.method": request.method,
                "http.target": request.url.path,
            },
        ):
            response = await call_next(request)
            elapsed_ms = (time.perf_counter() - start) * 1000
            latency_str = f"{elapsed_ms:.2f}"
            response.headers["X-Process-Time-Ms"] = latency_str
            # Push latency into the log context so subsequent records carry it
            set_log_context(latency_ms=latency_str)
            logger.info(
                "request completed",
                extra={"latency_ms": latency_str},
            )
            return response


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Catch unhandled exceptions and return a structured JSON error.

    Never return internal exception strings to the client — traceback text and
    exception messages routinely contain file paths, SQL fragments, and third-
    party library internals.  The full traceback is logged server-side keyed
    on the request id so operators can still correlate.
    """

    async def dispatch(self, request: Request, call_next):  # noqa: ANN001
        try:
            return await call_next(request)
        except Exception:
            request_id = request.headers.get("X-Request-ID", "-")
            logger.exception(
                "Unhandled error on %s %s",
                request.method,
                request.url.path,
                extra={"request_id": request_id},
            )
            return JSONResponse(
                status_code=500,
                content={
                    "error": "internal_server_error",
                    "request_id": request_id,
                },
            )


class RequestRateLimitMiddleware(BaseHTTPMiddleware):
    """Apply lightweight in-memory rate limiting to the shared API.

    Notes:
    - Per-process only.  For multi-worker / multi-instance deployments, put a
      real distributed limiter in front (nginx ``limit_req``, Cloudflare,
      AWS WAF, ``fastapi-limiter`` on Redis).  The audit flagged this as
      ``C-11``.
    - X-Forwarded-For is only trusted when the immediate peer is listed in
      ``GENAI_SYSTEMS_LAB_TRUSTED_PROXIES`` to prevent IP spoofing.
    - Empty deques are swept periodically to bound memory.
    """

    _DEFAULT_LIMIT = (120, 60)
    _RULES: tuple[tuple[str, str, int, int], ...] = (
        ("/auth/signup", "signup", 5, 60),
        ("/auth/login", "login", 10, 60),
        ("/eval/", "evaluation", 6, 300),
        ("/stream/", "stream", 30, 60),
        ("/explain/", "explain", 20, 60),
        ("/shared/", "shared", 60, 60),
    )
    _SWEEP_INTERVAL_SECONDS = 300.0

    def __init__(self, app: Any) -> None:
        super().__init__(app)
        self._lock = threading.Lock()
        self._timestamps: dict[tuple[str, str], deque[float]] = {}
        self._last_sweep = time.monotonic()

    @staticmethod
    def _client_identifier(request: Request) -> str:
        peer_host = request.client.host if request.client else None
        forwarded_for = request.headers.get("x-forwarded-for", "").strip()
        # Only honour X-Forwarded-For when the peer is a known reverse proxy.
        if forwarded_for and peer_host and peer_host in _TRUSTED_PROXY_IPS:
            candidate = forwarded_for.split(",", 1)[0].strip()
            if candidate:
                return candidate
        if peer_host:
            return peer_host
        return "unknown"

    @classmethod
    def _resolve_rule(cls, path: str) -> tuple[str, int, int]:
        for prefix, bucket, limit, window_seconds in cls._RULES:
            if path.startswith(prefix):
                return bucket, limit, window_seconds
        return "default", cls._DEFAULT_LIMIT[0], cls._DEFAULT_LIMIT[1]

    def _sweep_expired(self, now: float) -> None:
        """Drop empty deques and stale buckets.  Caller must hold ``self._lock``."""
        if now - self._last_sweep < self._SWEEP_INTERVAL_SECONDS:
            return
        self._last_sweep = now
        stale_keys: list[tuple[str, str]] = []
        for key, timestamps in self._timestamps.items():
            # An entry is stale if its newest timestamp is older than the
            # longest configured window (kept generous at 300 s to be safe).
            if not timestamps or (now - timestamps[-1]) > 600.0:
                stale_keys.append(key)
        for key in stale_keys:
            self._timestamps.pop(key, None)

    async def dispatch(self, request: Request, call_next):  # noqa: ANN001
        if request.method == "OPTIONS" or _env_flag("GENAI_SYSTEMS_LAB_DISABLE_RATE_LIMITS", False):
            return await call_next(request)

        bucket, limit, window_seconds = self._resolve_rule(request.url.path)
        now = time.monotonic()
        key = (bucket, self._client_identifier(request))

        with self._lock:
            self._sweep_expired(now)
            timestamps = self._timestamps.setdefault(key, deque())
            cutoff = now - window_seconds
            while timestamps and timestamps[0] <= cutoff:
                timestamps.popleft()

            if len(timestamps) >= limit:
                retry_after = max(1, int(window_seconds - (now - timestamps[0])))
                response = JSONResponse(
                    status_code=429,
                    content={"detail": "Rate limit exceeded. Slow down and retry."},
                )
                response.headers["Retry-After"] = str(retry_after)
                return response

            timestamps.append(now)

        return await call_next(request)


# -- Regex for control chars (keep newlines/tabs) ----------------------------
#
# ``InputValidationMiddleware`` previously HTML-escaped every string in the
# request body (turning quotes into ``&quot;``, apostrophes into ``&#x27;``,
# ``<`` into ``&lt;``) and additionally rejected any input containing common
# SQL keywords (``UNION SELECT``, ``; DROP ``, ``-- ``) or inline event
# handlers.  That was catastrophic for an LLM platform:
#
#   1. Every prompt reaching the model was corrupted; "O'Brien" became
#      ``O&#x27;Brien``.
#   2. Projects like ``genai-nl2sql-agent``, ``genai-code-copilot``, and
#      ``lg-debugging-agent`` must accept SQL and HTML fragments from the user.
#      The regex blocklist silently rejected valid prompts with a 422.
#
# The middleware is now purely a DoS guardrail:
#   * reject non-JSON bodies cleanly,
#   * reject empty or oversized ``input`` fields,
#   * reject null bytes (which break most downstream libraries).
#
# XSS protection belongs at the output/render layer (React escapes by default);
# prompt-injection defence belongs to project system prompts and guardrail
# models, not to a regex WAF.

_CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


class InputValidationMiddleware(BaseHTTPMiddleware):
    """Validate incoming JSON bodies on mutating methods.

    Only structural / size checks are performed here; string contents are
    passed through untouched so that the downstream LLM sees exactly what the
    user typed.
    """

    async def dispatch(self, request: Request, call_next):  # noqa: ANN001
        if request.method not in {"POST", "PUT", "PATCH"}:
            return await call_next(request)

        content_type = request.headers.get("content-type", "")
        if "application/json" not in content_type:
            return await call_next(request)

        body_bytes = await request.body()
        try:
            body = json.loads(body_bytes) if body_bytes else {}
        except (json.JSONDecodeError, ValueError):
            return JSONResponse(
                status_code=422,
                content={"error": "invalid_json", "detail": "Request body is not valid JSON."},
            )

        raw_input = body.get("input") if isinstance(body, dict) else None
        if isinstance(raw_input, str):
            if raw_input.strip() == "":
                return JSONResponse(
                    status_code=422,
                    content={"error": "empty_input", "detail": "The 'input' field must not be empty."},
                )
            if len(raw_input) > MAX_INPUT_LENGTH:
                return JSONResponse(
                    status_code=422,
                    content={
                        "error": "input_too_long",
                        "detail": f"The 'input' field exceeds the maximum length of {MAX_INPUT_LENGTH} characters.",
                    },
                )
            if "\x00" in raw_input:
                return JSONResponse(
                    status_code=422,
                    content={"error": "null_byte_rejected", "detail": "Null bytes are not allowed."},
                )

        return await call_next(request)


def _validate_stream_input(value: str) -> str:
    """Validate stream query input with the same safety rules as batch runs."""
    if value.strip() == "":
        raise HTTPException(status_code=422, detail="The 'input' field must not be empty.")

    if len(value) > MAX_INPUT_LENGTH:
        raise HTTPException(
            status_code=422,
            detail=f"The 'input' field exceeds the maximum length of {MAX_INPUT_LENGTH} characters.",
        )

    # Strip ASCII control chars (except \t, \n, \r) so log lines stay clean,
    # but do not HTML-escape — the LLM should see exactly what the user typed.
    return _CONTROL_RE.sub("", value)


# -- API key validation --------------------------------------------------------
_MIN_API_KEY_LENGTH = 20
_MAX_API_KEY_LENGTH = 256
# Accept the full character set used by real provider keys: alphanumerics, the
# url-safe base64 symbols, plus ``.`` (Anthropic admin keys), ``/`` and ``+``
# (legacy base64), ``=`` (padding), and ``:`` (multi-part tokens).  Anything
# outside this set is almost certainly garbage.
_API_KEY_RE = re.compile(r"^[A-Za-z0-9_\-./=+:]+$")


def _validate_api_key_format(key: str) -> str | None:
    """Return an error message if *key* looks invalid, else ``None``."""
    if len(key) < _MIN_API_KEY_LENGTH:
        return "API key too short."
    if len(key) > _MAX_API_KEY_LENGTH:
        return "API key too long."
    if not _API_KEY_RE.match(key):
        return "API key contains invalid characters."
    return None


def _safe_sse_error_payload(exc: BaseException, request_id: str) -> str:
    """Return a safe JSON payload for SSE ``event: error`` frames.

    Only leak messages from exceptions whose ``str`` is known to be operator-
    controlled (``HTTPException.detail``, ``ValueError``,
    ``ProjectUnavailableError``).  Everything else is logged server-side with
    the request id and reduced to a generic ``internal_server_error`` on the
    wire.  Mirrors ``ErrorHandlingMiddleware`` for the batch path.
    """
    if isinstance(exc, HTTPException):
        return json.dumps({"error": exc.detail, "request_id": request_id})
    if isinstance(exc, (ValueError, ProjectUnavailableError)):
        message = str(exc) or "Execution failed."
        return json.dumps({"error": message, "request_id": request_id})
    logger.exception("sse stream failed", extra={"request_id": request_id})
    return json.dumps({"error": "internal_server_error", "request_id": request_id})


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Attach a conservative set of security response headers.

    Intentionally small (no inline ``script-src``, no ``frame-ancestors``) so
    the separately-hosted Next.js portfolio controls its own CSP.  The
    backend serves JSON, a bit of OpenAPI HTML from FastAPI, and SSE — none of
    those should ever be framed, rendered as HTML by a browser, or sniffed.
    """

    _HEADERS = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "Referrer-Policy": "no-referrer",
        "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=()",
        "Cross-Origin-Opener-Policy": "same-origin",
        "Cross-Origin-Resource-Policy": "same-site",
    }

    async def dispatch(self, request: Request, call_next):  # noqa: ANN001
        response = await call_next(request)
        for header, value in self._HEADERS.items():
            response.headers.setdefault(header, value)
        # HSTS only in prod to avoid breaking local http:// dev.
        if os.getenv("APP_ENV", "dev").strip().lower() == "prod":
            response.headers.setdefault(
                "Strict-Transport-Security",
                "max-age=63072000; includeSubDomains",
            )
        return response


def _current_request_provider() -> str:
    provider = get_request_provider()
    if provider:
        return provider
    return infer_provider(get_request_model())


_BYOK_EXEMPT_PREFIXES = (
    "/health",
    "/llm/",
    "/projects",
    "/auth/",
    "/metrics",
    "/history",
    "/session/",
    "/shared/",
    "/run/",       # share / unshare — no LLM call
    "/openapi",
    "/docs",
    "/redoc",
)


class BYOKMiddleware:
    """Pure ASGI middleware that binds a per-request BYOK Google API key.

    Reads the key from the ``x-api-key`` request header.  Routes that invoke
    an LLM receive a **400** response when the header is missing.
    Read-only / auth / metadata routes are exempt.

    The key is never logged, stored in the database, or included in responses.
    """

    def __init__(self, app: Any) -> None:
        self.app = app

    async def __call__(self, scope: dict, receive: Any, send: Any) -> None:
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        # Let CORS preflight requests pass through without BYOK enforcement.
        if scope.get("type") == "http" and scope.get("method") == "OPTIONS":
            await self.app(scope, receive, send)
            return

        path: str = scope.get("path", "")

        # 1. Prefer x-api-key header
        api_key: str | None = None
        requested_model: str | None = None
        requested_provider: str | None = None
        for header_name, header_value in scope.get("headers", []):
            if header_name == b"x-api-key":
                api_key = header_value.decode("latin-1").strip()
            elif header_name == b"x-llm-model":
                requested_model = header_value.decode("latin-1").strip()
            elif header_name == b"x-llm-provider":
                requested_provider = header_value.decode("latin-1").strip().lower()

        requested_spec = get_model_spec(requested_model)
        resolved_provider = requested_provider or requested_spec["provider"]
        if requested_provider and requested_spec["provider"] != "ollama" and requested_provider != requested_spec["provider"]:
            body = json.dumps({"detail": "Selected provider does not match the selected model."}).encode()
            await send({
                "type": "http.response.start",
                "status": 400,
                "headers": [
                    [b"content-type", b"application/json"],
                    [b"content-length", str(len(body)).encode()],
                ],
            })
            await send({"type": "http.response.body", "body": body})
            return

        # Exempt paths that never call the LLM
        is_exempt = path == "/" or any(path.startswith(prefix) for prefix in _BYOK_EXEMPT_PREFIXES)

        if not api_key and not is_exempt and provider_requires_api_key(resolved_provider):
            body = json.dumps({"detail": "Missing x-api-key header."}).encode()
            await send({
                "type": "http.response.start",
                "status": 400,
                "headers": [
                    [b"content-type", b"application/json"],
                    [b"content-length", str(len(body)).encode()],
                ],
            })
            await send({"type": "http.response.body", "body": body})
            return

        # Validate key format (never log the actual key value)
        if api_key:
            fmt_error = _validate_api_key_format(api_key)
            if fmt_error:
                body = json.dumps({"detail": fmt_error}).encode()
                await send({
                    "type": "http.response.start",
                    "status": 400,
                    "headers": [
                        [b"content-type", b"application/json"],
                        [b"content-length", str(len(body)).encode()],
                    ],
                })
                await send({"type": "http.response.body", "body": body})
                return

        provider_token = set_request_provider(resolved_provider)
        model_token = set_request_model(requested_model)

        if api_key:
            token = set_byok_api_key(api_key)
            try:
                await self.app(scope, receive, send)
            finally:
                reset_byok_api_key(token)
                reset_request_model(model_token)
                reset_request_provider(provider_token)
        else:
            try:
                await self.app(scope, receive, send)
            finally:
                reset_request_model(model_token)
                reset_request_provider(provider_token)


# -- Factory -------------------------------------------------------------------

def create_app(
    *,
    title: str = "GenAI Systems Lab",
    version: str = "1.0.0",
    description: str = "",
    allowed_origins: list[str] | None = None,
) -> FastAPI:
    """Create a pre-configured FastAPI instance.

    Projects create their own ``FastAPI`` via this factory and mount
    project-specific routers::

        from shared.api import create_app
        app = create_app(title="NL2SQL Agent")
        app.include_router(my_router)
    """
    init_db()

    @asynccontextmanager
    async def _lifespan(_app: FastAPI):
        if _env_flag("OTEL_ENABLED", False):
            console_export = _env_flag("OTEL_CONSOLE_EXPORT", False)
            if setup_otel(console_export=console_export):
                logger.info("OpenTelemetry tracing enabled for shared API.")
            else:
                logger.warning("OTEL_ENABLED is set, but OpenTelemetry packages are unavailable.")
        try:
            yield
        finally:
            shutdown_otel()

    app = FastAPI(title=title, version=version, description=description, lifespan=_lifespan)

    # Middleware executes in reverse registration order.
    app.add_middleware(ErrorHandlingMiddleware)
    app.add_middleware(RequestTimingMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(InputValidationMiddleware)
    app.add_middleware(BYOKMiddleware)
    app.add_middleware(RequestRateLimitMiddleware)

    origins = _resolve_allowed_origins(allowed_origins)
    if os.getenv("APP_ENV", "dev").strip().lower() == "prod" and allowed_origins is None:
        if not os.getenv("GENAI_SYSTEMS_LAB_ALLOWED_ORIGINS", "").strip():
            # Fail loudly: a silent localhost-only fallback in prod is
            # indistinguishable from "login is broken for every user".
            raise RuntimeError(
                "GENAI_SYSTEMS_LAB_ALLOWED_ORIGINS must be set when APP_ENV=prod "
                "to enable cross-origin browser sessions.  Refusing to start "
                "with an implicit localhost-only allowlist."
            )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=_CORS_ALLOWED_METHODS,
        allow_headers=_CORS_ALLOWED_HEADERS,
        expose_headers=["X-Process-Time-Ms", "X-Request-ID"],
    )

    # GZip is registered last so it wraps every other middleware.  The 1 KB
    # threshold keeps tiny JSON responses (``/health``) uncompressed; SSE
    # responses are already streamed without a ``Content-Length`` header and
    # are skipped by Starlette's GZipMiddleware automatically.
    app.add_middleware(GZipMiddleware, minimum_size=1024)

    # -- Routes ----------------------------------------------------------------

    @app.get("/")
    async def root() -> dict[str, str]:
        return {
            "service": "genai-systems-lab-api",
            "status": "ok",
            "health": "/health",
            "catalog": "/llm/catalog",
        }

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/llm/catalog", response_model=LLMCatalogResponse)
    async def llm_catalog() -> LLMCatalogResponse:
        return LLMCatalogResponse(**build_provider_catalog())

    @app.get("/projects")
    async def projects() -> dict[str, Any]:
        items = _discover_projects()
        return {"count": len(items), "projects": items}

    @app.get("/auth/config", response_model=AuthConfigResponse)
    async def auth_config() -> AuthConfigResponse:
        return AuthConfigResponse(public_signup=_public_signup_enabled())

    @app.post("/auth/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
    async def signup(
        body: AuthRequest,
        response: Response,
        session: Session = Depends(get_db_session),
    ) -> AuthResponse:
        if not _public_signup_enabled():
            raise HTTPException(status_code=403, detail="Public signup is disabled.")

        email = body.email.strip().lower()
        password = body.password.strip()
        if not email or "@" not in email:
            raise HTTPException(status_code=422, detail="A valid email is required.")
        if len(password) < 8:
            raise HTTPException(status_code=422, detail="Password must be at least 8 characters.")

        try:
            user = create_user(session, email, password)
        except IntegrityError as exc:
            session.rollback()
            raise HTTPException(status_code=409, detail="An account with that email already exists.") from exc

        token = create_access_token(user)
        _set_auth_cookie(response, token)

        return AuthResponse(
            token=token,
            user={"id": user.id, "email": user.email},
        )

    @app.post("/auth/login", response_model=AuthResponse)
    async def login(
        body: AuthRequest,
        response: Response,
        session: Session = Depends(get_db_session),
    ) -> AuthResponse:
        user = authenticate_user(session, body.email, body.password)
        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password.")

        token = create_access_token(user)
        _set_auth_cookie(response, token)

        return AuthResponse(
            token=token,
            user={"id": user.id, "email": user.email},
        )

    @app.post("/auth/logout", response_model=StatusResponse)
    async def logout(response: Response) -> StatusResponse:
        _clear_auth_cookie(response)
        return StatusResponse(status="ok")

    @app.get("/auth/me", response_model=AuthUserResponse)
    async def auth_me(current_user: User = Depends(get_current_user)) -> AuthUserResponse:
        return AuthUserResponse(id=current_user.id, email=current_user.email)

    @app.post("/{project_name}/run", response_model=BaseResponse)
    async def run(
        project_name: str,
        body: BaseRequest,
        current_user: User | None = Depends(get_optional_current_user),
        session: Session = Depends(get_db_session),
    ) -> BaseResponse:
        start = time.perf_counter()
        success = False
        confidence = 0.0
        metrics_project = project_name
        memory_entries: list[MemoryEntryPayload] = []
        timeline_entries: list[TimelineEntryPayload] = []
        result = None
        run_session: RunSession | None = None
        existing_session_memory: list[dict[str, str]] = []
        prepared_input = body.input
        used_session_context = False

        if current_user is not None:
            run_session = _resolve_run_session(
                session,
                user_id=current_user.id,
                session_id=body.session_id,
            )
            existing_session_memory = deserialize_session_memory_entries(run_session.memory_text)
            prepared_input, used_session_context, _ = build_session_prompt(body.input, existing_session_memory)

        def step_memory_emitter(step: str, status: str) -> None:
            _append_execution_trace(memory_entries, timeline_entries, start, step, status)

        try:
            api_key = get_effective_api_key(required=provider_requires_api_key(_current_request_provider()))
            # Run the project on a worker thread so the LLM call does not block
            # the event loop; ProjectUnavailableError / ValueError surface the
            # same way as a direct call.
            result = await asyncio.to_thread(
                run_project,
                project_name,
                prepared_input,
                api_key=api_key,
                step_emitter=step_memory_emitter,
            )
            success = result.exit_code == 0
            metrics_project = result.project

            _append_fallback_memory_entries(memory_entries, result.project)
            _append_fallback_timeline_entries(timeline_entries, result.project)
            _append_result_memory_entry(
                memory_entries,
                success=result.exit_code == 0,
                latency_ms=result.elapsed_ms,
                output_text=result.output,
            )
            _append_result_timeline_entry(
                timeline_entries,
                start_time=start,
                success=result.exit_code == 0,
                latency_ms=result.elapsed_ms,
                output_text=result.output,
            )

            confidence, _ = compute_run_confidence(
                output_text=result.output,
                success=result.exit_code == 0,
                latency_ms=result.elapsed_ms,
                timeline_entries=timeline_entries,
            )
            _score_langfuse_confidence(result.trace_id, confidence)
        except ProjectUnavailableError as exc:
            logger.warning("project unavailable", extra={"project_name": project_name, "error": str(exc)})
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except ValueError as exc:
            logger.warning("project run rejected", extra={"project_name": project_name, "error": str(exc)})
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        finally:
            elapsed_ms = (time.perf_counter() - start) * 1000
            metrics_store.record(metrics_project, elapsed_ms, success)
            _record_operational_metric(
                session,
                project=metrics_project,
                latency_ms=result.elapsed_ms if result is not None else elapsed_ms,
                confidence_score=confidence,
                success=success,
            )

        session_payload = {"id": None, "memory": []}
        if current_user is not None and run_session is not None:
            updated_session_memory = update_session_memory_entries(
                existing_session_memory,
                user_input=body.input,
                output_text=result.output,
            )
            run_session.memory_text = serialize_session_memory_entries(updated_session_memory)
            session.add(run_session)

            session_payload = _serialize_session_payload(run_session)

            save_run(
                session,
                user_id=current_user.id,
                session_id=run_session.id,
                project=result.project,
                input_text=body.input,
                output_text=result.output,
                memory=memory_entries,
                timeline=timeline_entries,
                latency_ms=result.elapsed_ms,
                confidence_score=confidence,
                success=success,
            )

        return BaseResponse(
            output=result.output,
            latency=result.elapsed_ms,
            confidence=confidence,
            session_id=session_payload["id"],
            session_memory=session_payload["memory"],
            used_session_context=used_session_context,
            success=result.exit_code == 0,
            memory=memory_entries,
            timeline=timeline_entries,
        )

    @app.get("/metrics", response_model=MetricsResponse)
    async def metrics(session: Session = Depends(get_db_session)) -> MetricsResponse:
        persisted = _snapshot_persisted_metrics(session)
        if persisted.total_requests > 0:
            return persisted
        return MetricsResponse(**metrics_store.snapshot())

    @app.get("/metrics/time", response_model=list[TimeSeriesMetricPointResponse])
    async def metrics_time(
        project: str | None = None,
        time_range: MetricsTimeRange = Query(default="day", alias="range"),
        session: Session = Depends(get_db_session),
    ) -> list[TimeSeriesMetricPointResponse]:
        query = select(OperationalMetric).where(OperationalMetric.timestamp >= _metrics_time_cutoff(time_range))

        if project:
            project_value = project.strip()
            if project_value:
                try:
                    project_value = resolve_project_name(project_value)
                except ValueError:
                    pass
                query = query.where(OperationalMetric.project == project_value)

        metrics_rows = session.scalars(
            query.order_by(OperationalMetric.timestamp.asc(), OperationalMetric.id.asc())
        ).all()
        return [
            _serialize_operational_metric_point(metric)
            for metric in metrics_rows
            if metric.timestamp is not None
        ]

    @app.get("/history", response_model=HistoryResponse)
    async def history(
        current_user: User = Depends(get_current_user),
        session: Session = Depends(get_db_session),
        limit: int = Query(default=DEFAULT_HISTORY_PAGE_SIZE, ge=1, le=MAX_HISTORY_PAGE_SIZE),
        before_id: int | None = Query(default=None, ge=1),
    ) -> HistoryResponse:
        query = select(Run).where(Run.user_id == current_user.id)
        if before_id is not None:
            query = query.where(Run.id < before_id)
        runs = session.scalars(
            query.order_by(Run.timestamp.desc(), Run.id.desc()).limit(limit)
        ).all()
        items = [serialize_run(run) for run in runs]
        return HistoryResponse(count=len(items), runs=items)

    @app.get("/run/{run_id}", response_model=HistoryRunResponse)
    async def get_run(
        run_id: int,
        current_user: User = Depends(get_current_user),
        session: Session = Depends(get_db_session),
    ) -> HistoryRunResponse:
        run = session.scalar(
            select(Run).where(Run.id == run_id, Run.user_id == current_user.id)
        )
        if run is None:
            raise HTTPException(status_code=404, detail="Run not found.")
        return HistoryRunResponse(**serialize_run(run))

    @app.get("/session/{session_id}", response_model=SessionResponse)
    async def get_session_state(
        session_id: int,
        current_user: User = Depends(get_current_user),
        session: Session = Depends(get_db_session),
    ) -> SessionResponse:
        run_session = session.scalar(
            select(RunSession).where(RunSession.id == session_id, RunSession.user_id == current_user.id)
        )
        if run_session is None:
            raise HTTPException(status_code=404, detail="Session not found.")
        return SessionResponse(**_serialize_session_payload(run_session))

    @app.post("/session/{session_id}/clear", response_model=SessionResponse)
    async def clear_session_state(
        session_id: int,
        current_user: User = Depends(get_current_user),
        session: Session = Depends(get_db_session),
    ) -> SessionResponse:
        run_session = session.scalar(
            select(RunSession).where(RunSession.id == session_id, RunSession.user_id == current_user.id)
        )
        if run_session is None:
            raise HTTPException(status_code=404, detail="Session not found.")

        run_session.memory_text = serialize_session_memory_entries([])
        session.add(run_session)
        session.commit()
        session.refresh(run_session)
        return SessionResponse(**_serialize_session_payload(run_session))

    @app.post("/explain/{run_id}", response_model=RunExplanationResponse)
    async def explain_run(
        run_id: int,
        current_user: User = Depends(get_current_user),
        session: Session = Depends(get_db_session),
    ) -> RunExplanationResponse:
        run = session.scalar(
            select(Run).where(Run.id == run_id, Run.user_id == current_user.id)
        )
        if run is None:
            raise HTTPException(status_code=404, detail="Saved run not found.")

        serialized = serialize_run(run)

        try:
            explanation = build_run_explanation(
                project=run.project,
                input_text=run.input_text,
                output_text=run.output_text,
                memory=serialized["memory"],
                timeline=serialized["timeline"],
            )
            return RunExplanationResponse(**explanation)
        except GeminiTimeoutError as exc:
            logger.warning(
                "run explanation timed out",
                extra={"run_id": run_id, "user_id": current_user.id, "error": str(exc)},
            )
            raise HTTPException(status_code=504, detail="Explanation generation timed out.") from exc
        except (GeminiGenerationError, ValidationError, ValueError) as exc:
            logger.warning(
                "run explanation failed",
                extra={"run_id": run_id, "user_id": current_user.id, "error": str(exc)},
            )
            raise HTTPException(
                status_code=503,
                detail="Could not generate a structured explanation for this run.",
            ) from exc

    @app.get("/stream/{project_name}")
    async def stream(
        project_name: str,
        request: Request,
        input: str = "",
        session_id: int | None = None,
        current_user: User | None = Depends(get_optional_current_user),
        session: Session = Depends(get_db_session),
    ) -> StreamingResponse:
        """Stream project output as Server-Sent Events.

        Emits ``event: step`` frames with ``{"step": "<node>", "status": "running|done|error"}``
        while the project is executing, then streams token chunks once the final
        output is available.
        A final ``event: done`` frame signals completion.
        """

        validated_input = _validate_stream_input(input)
        sse_request_id = request.headers.get("X-Request-ID", "-")
        run_session: RunSession | None = None
        existing_session_memory: list[dict[str, str]] = []
        prepared_input = validated_input
        used_session_context = False

        if current_user is not None:
            run_session = _resolve_run_session(
                session,
                user_id=current_user.id,
                session_id=session_id,
            )
            existing_session_memory = deserialize_session_memory_entries(run_session.memory_text)
            prepared_input, used_session_context, _ = build_session_prompt(validated_input, existing_session_memory)

        async def event_stream():
            start = time.perf_counter()
            success = False
            confidence = 0.0
            metrics_project = project_name
            memory_entries: list[MemoryEntryPayload] = []
            timeline_entries: list[TimelineEntryPayload] = []
            result = None
            try:
                loop = asyncio.get_running_loop()
                step_queue: asyncio.Queue[dict[str, Any] | None] = asyncio.Queue()

                def step_emitter(step: str, status: str) -> None:
                    loop.call_soon_threadsafe(step_queue.put_nowait, {"step": step, "status": status})

                api_key = get_effective_api_key(required=provider_requires_api_key(_current_request_provider()))
                run_task = asyncio.create_task(
                    asyncio.to_thread(run_project, project_name, prepared_input, api_key=api_key, step_emitter=step_emitter)
                )
                nodes = _get_pipeline_nodes(project_name)
                seen_steps: list[tuple[str, str]] = []
                running_steps: list[str] = []

                while True:
                    if run_task.done() and step_queue.empty():
                        break
                    try:
                        step_event = await asyncio.wait_for(step_queue.get(), timeout=0.05)
                    except asyncio.TimeoutError:
                        continue
                    if step_event is None:
                        continue
                    step_name = step_event["step"]
                    step_status = step_event["status"]
                    if step_status == "running":
                        running_steps = [name for name in running_steps if name != step_name]
                        running_steps.append(step_name)
                    else:
                        running_steps = [name for name in running_steps if name != step_name]
                    seen_steps.append((step_name, step_status))
                    _append_execution_trace(
                        memory_entries,
                        timeline_entries,
                        start,
                        step_name,
                        step_status,
                        error=step_event.get("error"),
                    )
                    yield f"event: step\ndata: {json.dumps(step_event)}\n\n"

                try:
                    result = await run_task
                except Exception as exc:
                    # Only surface the message to the user-facing step frame
                    # when the exception is operator-controlled; otherwise
                    # scrub to ``Execution failed.`` so stack traces / internal
                    # detail never reach the browser.  The SSE ``error`` frame
                    # then goes through the same scrubbing helper.
                    if isinstance(exc, (ValueError, ProjectUnavailableError, HTTPException)):
                        user_message = getattr(exc, "detail", None) or str(exc) or "Execution failed."
                    else:
                        user_message = "Execution failed."
                    if running_steps:
                        failed_step = running_steps[-1]
                        step_error = {
                            "step": failed_step,
                            "status": "error",
                            "error": user_message,
                        }
                        _append_execution_trace(
                            memory_entries,
                            timeline_entries,
                            start,
                            failed_step,
                            "error",
                            error=user_message,
                        )
                        yield f"event: step\ndata: {json.dumps(step_error)}\n\n"
                    error_payload = _safe_sse_error_payload(exc, sse_request_id)
                    yield f"event: error\ndata: {error_payload}\n\n"
                    return

                success = result.exit_code == 0
                metrics_project = result.project

                if not seen_steps and nodes:
                    # The project emitted no real step events.  Synthesise a
                    # running/done pair per pipeline node so the UI has
                    # something to render, but do not pace the events with
                    # artificial sleeps (previously ~40 ms per node = up to
                    # ~300 ms of fake latency for a large graph).
                    for index, node_id in enumerate(nodes):
                        synthetic_running = {"step": node_id, "status": "running"}
                        _append_memory_entry(memory_entries, node_id, "running")
                        _append_timeline_entry(
                            timeline_entries,
                            timestamp=index * 0.28 + 0.04,
                            step_id=node_id,
                            event="running",
                            data=_memory_content(_format_memory_step(node_id), "running", _memory_entry_type(node_id, "running")),
                        )
                        yield f"event: step\ndata: {json.dumps(synthetic_running)}\n\n"
                        synthetic_done = {"step": node_id, "status": "done"}
                        _append_memory_entry(memory_entries, node_id, "done")
                        _append_timeline_entry(
                            timeline_entries,
                            timestamp=index * 0.28 + 0.18,
                            step_id=node_id,
                            event="done",
                            data=_memory_content(_format_memory_step(node_id), "done", "observation"),
                        )
                        yield f"event: step\ndata: {json.dumps(synthetic_done)}\n\n"

                _append_fallback_memory_entries(memory_entries, result.project)
                _append_fallback_timeline_entries(timeline_entries, result.project)
                _append_result_memory_entry(
                    memory_entries,
                    success=result.exit_code == 0,
                    latency_ms=result.elapsed_ms,
                    output_text=result.output,
                )
                _append_result_timeline_entry(
                    timeline_entries,
                    start_time=start,
                    success=result.exit_code == 0,
                    latency_ms=result.elapsed_ms,
                    output_text=result.output,
                )

                confidence, _ = compute_run_confidence(
                    output_text=result.output,
                    success=result.exit_code == 0,
                    latency_ms=result.elapsed_ms,
                    timeline_entries=timeline_entries,
                )
                _score_langfuse_confidence(result.trace_id, confidence)

                session_payload = {"id": None, "memory": []}
                if current_user is not None and run_session is not None:
                    updated_session_memory = update_session_memory_entries(
                        existing_session_memory,
                        user_input=validated_input,
                        output_text=result.output,
                    )
                    run_session.memory_text = serialize_session_memory_entries(updated_session_memory)
                    session.add(run_session)

                    session_payload = _serialize_session_payload(run_session)

                    save_run(
                        session,
                        user_id=current_user.id,
                        session_id=run_session.id,
                        project=result.project,
                        input_text=validated_input,
                        output_text=result.output,
                        memory=memory_entries,
                        timeline=timeline_entries,
                        latency_ms=result.elapsed_ms,
                        confidence_score=confidence,
                        success=success,
                    )

                # Honest output emission (C-3 / HI-1 in the audit).
                #
                # ``result.output`` is already a *completed* string by the
                # time we get here — the project ran to completion inside
                # ``asyncio.to_thread(run_project, ...)`` above.  Earlier
                # revisions sliced that completed string into 80-char pieces
                # and emitted them as ``{"token": "..."}`` SSE frames to
                # mimic token-level streaming.  That was theatre, not
                # streaming: no provider token boundaries, no pacing tied to
                # real generation, and every "token" was already sitting in
                # memory.  We now emit the full completed output as a single
                # frame so the UI can render it as soon as it arrives, and
                # document the field as the full output rather than a
                # provider token.  Real provider-native token streaming
                # requires threading the streaming SDK API through each
                # project pipeline and is tracked separately.
                output_payload = json.dumps({"output": result.output})
                yield f"event: output\ndata: {output_payload}\n\n"

                # Final summary event
                done_payload = json.dumps({
                    "output": result.output,
                    "latency": round(result.elapsed_ms, 2),
                    "confidence": confidence,
                    "session_id": session_payload["id"],
                    "session_memory": session_payload["memory"],
                    "used_session_context": used_session_context,
                    "success": result.exit_code == 0,
                    "memory": memory_entries,
                    "timeline": timeline_entries,
                })
                yield f"event: done\ndata: {done_payload}\n\n"

            except ProjectUnavailableError as exc:
                error_payload = _safe_sse_error_payload(exc, sse_request_id)
                yield f"event: error\ndata: {error_payload}\n\n"
            except ValueError as exc:
                error_payload = _safe_sse_error_payload(exc, sse_request_id)
                yield f"event: error\ndata: {error_payload}\n\n"
            except Exception as exc:
                error_payload = _safe_sse_error_payload(exc, sse_request_id)
                yield f"event: error\ndata: {error_payload}\n\n"
            finally:
                elapsed_ms = (time.perf_counter() - start) * 1000
                metrics_store.record(metrics_project, elapsed_ms, success)
                _record_operational_metric(
                    session,
                    project=metrics_project,
                    latency_ms=result.elapsed_ms if result is not None else elapsed_ms,
                    confidence_score=confidence,
                    success=success,
                )

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    @app.post("/run/{run_id}/share", response_model=ShareRunResponse)
    async def share_run(
        run_id: int,
        body: ShareRunRequest | None = None,
        current_user: User = Depends(get_current_user),
        session: Session = Depends(get_db_session),
    ) -> ShareRunResponse:
        run = session.scalar(
            select(Run).where(Run.id == run_id, Run.user_id == current_user.id)
        )
        if run is None:
            raise HTTPException(status_code=404, detail="Run not found.")

        if not run.share_token:
            run.share_token = _secrets.token_urlsafe(32)

        run.is_public = True
        # Default to a bounded TTL so forgotten shares do not stay public
        # forever.  Explicit ``expires_in_hours = 0`` can be treated as
        # "permanent" by setting it to ``None`` server-side (but ShareRunRequest
        # already enforces ``ge=1``, so users can't accidentally choose 0).
        requested_hours = body.expires_in_hours if body else None
        if requested_hours is None:
            requested_hours = DEFAULT_SHARE_TTL_HOURS
        requested_hours = max(1, min(requested_hours, MAX_SHARE_TTL_HOURS))
        run.expires_at = datetime.now(UTC) + timedelta(hours=requested_hours)

        session.commit()
        session.refresh(run)

        return ShareRunResponse(
            share_token=run.share_token,
            is_public=True,
            expires_at=run.expires_at.isoformat() if run.expires_at else None,
        )

    @app.delete("/run/{run_id}/share")
    async def unshare_run(
        run_id: int,
        current_user: User = Depends(get_current_user),
        session: Session = Depends(get_db_session),
    ) -> dict[str, bool]:
        run = session.scalar(
            select(Run).where(Run.id == run_id, Run.user_id == current_user.id)
        )
        if run is None:
            raise HTTPException(status_code=404, detail="Run not found.")

        run.share_token = None
        run.is_public = False
        run.expires_at = None
        session.commit()

        return {"success": True}

    @app.get("/shared/{share_token}", response_model=SharedRunResponse)
    async def get_shared_run(
        share_token: str,
        session: Session = Depends(get_db_session),
    ) -> SharedRunResponse:
        run = session.scalar(
            select(Run).where(Run.share_token == share_token, Run.is_public == True)  # noqa: E712
        )
        if run is None:
            raise HTTPException(status_code=404, detail="Shared run not found.")

        if run.expires_at is not None:
            # ``expires_at`` is stored timezone-aware via SQLAlchemy but SQLite
            # round-trips can strip tzinfo — coerce to UTC defensively.
            expires_at = run.expires_at
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=_timezone.utc)
            if expires_at < datetime.now(UTC):
                raise HTTPException(status_code=410, detail="This shared link has expired.")

        serialized = serialize_run(run)
        return SharedRunResponse(
            id=serialized["id"],
            project=serialized["project"],
            input=serialized["input"],
            output=serialized["output"],
            memory=serialized["memory"],
            timeline=serialized["timeline"],
            latency=serialized["latency"],
            confidence=serialized["confidence"],
            timestamp=serialized["timestamp"],
        )

    @app.post("/eval/{project}")
    async def evaluate(project: str) -> dict[str, Any]:
        try:
            return run_project_evaluation(project)
        except ValueError as exc:
            logger.warning("evaluation rejected", extra={"project_name": project, "error": str(exc)})
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    return app


app = create_app()
