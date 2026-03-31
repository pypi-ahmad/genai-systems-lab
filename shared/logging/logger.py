"""Centralised structured logging with request and project context.

Features
--------
* **Context-var injection** — ``request_id``, ``project_name`` and
  ``latency_ms`` are automatically attached to every log record via
  :class:`_ContextFilter`.
* **Two formatters** — human-friendly :pypi:`rich` output (default) and
  machine-readable JSON lines (``json=True``).
* **OpenTelemetry aware** — when the optional ``opentelemetry-api``
  package is installed the current ``trace_id`` and ``span_id`` are
  injected into every record automatically.
"""

from __future__ import annotations

import contextvars
import json as _json
import logging
import os
import sys
import time
import uuid
from contextlib import contextmanager
from typing import Any, TextIO

from rich.logging import RichHandler


# ---------------------------------------------------------------------------
# Context variables
# ---------------------------------------------------------------------------
_ROOT_CONFIGURED = False

_request_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "request_id",
    default=None,
)
_project_name_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "project_name",
    default=None,
)
_latency_ms_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "latency_ms",
    default=None,
)


# ---------------------------------------------------------------------------
# OpenTelemetry helpers (optional — no hard dep)
# ---------------------------------------------------------------------------
def _otel_trace_context() -> tuple[str, str]:
    """Return ``(trace_id, span_id)`` from the current OTel context.

    Falls back to ``("-", "-")`` when *opentelemetry-api* is not installed
    or there is no active span.
    """
    try:
        from opentelemetry import trace  # type: ignore[import-untyped]

        span = trace.get_current_span()
        ctx = span.get_span_context()
        if ctx and ctx.trace_id:
            return (
                format(ctx.trace_id, "032x"),
                format(ctx.span_id, "016x"),
            )
    except Exception:  # noqa: BLE001
        pass
    return ("-", "-")


# ---------------------------------------------------------------------------
# Log filter — populates structured fields on every record
# ---------------------------------------------------------------------------
class _ContextFilter(logging.Filter):
    """Populate structured fields on every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "request_id"):
            record.request_id = _request_id_var.get() or "-"  # type: ignore[attr-defined]
        if not hasattr(record, "project_name"):
            record.project_name = _project_name_var.get() or "-"  # type: ignore[attr-defined]
        if not hasattr(record, "latency_ms"):
            record.latency_ms = _latency_ms_var.get() or "-"  # type: ignore[attr-defined]
        if not hasattr(record, "error"):
            record.error = "-"  # type: ignore[attr-defined]

        # OpenTelemetry trace context (cheap no-op when OTel is absent)
        if not hasattr(record, "trace_id"):
            trace_id, span_id = _otel_trace_context()
            record.trace_id = trace_id  # type: ignore[attr-defined]
            record.span_id = span_id  # type: ignore[attr-defined]

        return True


# ---------------------------------------------------------------------------
# Formatters
# ---------------------------------------------------------------------------
def _build_formatter() -> logging.Formatter:
    return logging.Formatter(
        "%(message)s | request_id=%(request_id)s project=%(project_name)s "
        "latency_ms=%(latency_ms)s error=%(error)s "
        "trace_id=%(trace_id)s span_id=%(span_id)s"
    )


class _JSONFormatter(logging.Formatter):
    """Emit one JSON object per log line — suitable for cloud log ingestion."""

    def format(self, record: logging.LogRecord) -> str:
        # Let the base formatter run so exc_info is rendered.
        message = record.getMessage()
        payload: dict[str, Any] = {
            "ts": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": message,
            "request_id": getattr(record, "request_id", "-"),
            "project": getattr(record, "project_name", "-"),
            "latency_ms": getattr(record, "latency_ms", "-"),
            "error": getattr(record, "error", "-"),
            "trace_id": getattr(record, "trace_id", "-"),
            "span_id": getattr(record, "span_id", "-"),
        }
        if record.exc_info and not record.exc_text:
            record.exc_text = self.formatException(record.exc_info)
        if record.exc_text:
            payload["exception"] = record.exc_text
        return _json.dumps(payload, default=str)


# ---------------------------------------------------------------------------
# Root logger configuration
# ---------------------------------------------------------------------------
def _configure_root_logger(
    *,
    level: int = logging.INFO,
    stream: TextIO = sys.stderr,
    rich: bool = True,
    json: bool = False,
) -> None:
    global _ROOT_CONFIGURED
    if _ROOT_CONFIGURED:
        return

    root = logging.getLogger()
    root.setLevel(level)

    handler: logging.Handler
    if json:
        handler = logging.StreamHandler(stream)
        handler.setFormatter(_JSONFormatter())
    elif rich:
        handler = RichHandler(
            rich_tracebacks=True,
            markup=False,
            show_time=True,
            show_path=False,
        )
        handler.setFormatter(_build_formatter())
    else:
        handler = logging.StreamHandler(stream)
        handler.setFormatter(_build_formatter())

    handler.addFilter(_ContextFilter())

    root.handlers.clear()
    root.addHandler(handler)
    _ROOT_CONFIGURED = True


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------
def new_request_id() -> str:
    return uuid.uuid4().hex[:12]


def set_log_context(
    *,
    request_id: str | None = None,
    project_name: str | None = None,
    latency_ms: str | None = None,
) -> dict[str, contextvars.Token[Any]]:
    tokens: dict[str, contextvars.Token[Any]] = {}
    if request_id is not None:
        tokens["request_id"] = _request_id_var.set(request_id)
    if project_name is not None:
        tokens["project_name"] = _project_name_var.set(project_name)
    if latency_ms is not None:
        tokens["latency_ms"] = _latency_ms_var.set(latency_ms)
    return tokens


def reset_log_context(tokens: dict[str, contextvars.Token[Any]]) -> None:
    for key in ("request_id", "project_name", "latency_ms"):
        token = tokens.get(key)
        if token is not None:
            {
                "request_id": _request_id_var,
                "project_name": _project_name_var,
                "latency_ms": _latency_ms_var,
            }[key].reset(token)


@contextmanager
def log_context(
    *,
    request_id: str | None = None,
    project_name: str | None = None,
    latency_ms: str | None = None,
):
    tokens = set_log_context(
        request_id=request_id,
        project_name=project_name,
        latency_ms=latency_ms,
    )
    try:
        yield
    finally:
        reset_log_context(tokens)


class LatencyTimer:
    """Convenience context-manager that records elapsed ms into log context.

    Usage::

        with LatencyTimer():
            do_work()
        # latency_ms is now set in the current log context
    """

    def __enter__(self) -> "LatencyTimer":
        self._start = time.perf_counter()
        return self

    def __exit__(self, *exc: object) -> None:
        self.elapsed_ms = (time.perf_counter() - self._start) * 1000
        _latency_ms_var.set(f"{self.elapsed_ms:.2f}")


def get_logger(
    name: str,
    *,
    level: int = logging.INFO,
    stream: TextIO = sys.stderr,
    rich: bool = True,
    json: bool | None = None,
) -> logging.Logger:
    """Return a named logger with shared structured output across modules.

    Parameters
    ----------
    json:
        When *True* emit JSON-lines output.  Defaults to the value of
        the ``LOG_FORMAT=json`` environment variable, falling back to
        *False* (rich console output).
    """
    use_json = json if json is not None else os.getenv("LOG_FORMAT", "").lower() == "json"
    _configure_root_logger(level=level, stream=stream, rich=rich, json=use_json)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = True
    return logger
