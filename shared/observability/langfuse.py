"""Langfuse observability integration for genai-systems-lab.

This module wraps the current observation-based Langfuse SDK. When Langfuse is
disabled or credentials are missing, all public helpers degrade to no-ops.
"""

from __future__ import annotations

import functools
import logging
import os
import time
from contextlib import contextmanager, nullcontext
from typing import Any, Callable, Generator

logger = logging.getLogger(__name__)

_langfuse_client: Any | None = None
_langfuse_available: bool | None = None


def _is_enabled() -> bool:
    return os.getenv("LANGFUSE_ENABLED", "false").strip().lower() in {"1", "true", "yes", "on"}


def _credentials_present() -> bool:
    return bool(os.getenv("LANGFUSE_PUBLIC_KEY", "").strip() and os.getenv("LANGFUSE_SECRET_KEY", "").strip())


def _base_url() -> str:
    return (
        os.getenv("LANGFUSE_BASE_URL", "").strip()
        or os.getenv("LANGFUSE_HOST", "").strip()
        or "https://cloud.langfuse.com"
    )


def _merge_metadata(*metadata_items: dict[str, Any] | None) -> dict[str, Any] | None:
    merged: dict[str, Any] = {}
    for item in metadata_items:
        if isinstance(item, dict):
            merged.update(item)
    return merged or None


def _string_metadata(metadata: dict[str, Any] | None) -> dict[str, str] | None:
    if not isinstance(metadata, dict):
        return None

    normalized: dict[str, str] = {}
    for key, value in metadata.items():
        if value is None:
            continue
        normalized[str(key)] = str(value)[:200]
    return normalized or None


def _ensure_client() -> Any | None:
    global _langfuse_client, _langfuse_available

    if _langfuse_available is False:
        return None
    if _langfuse_client is not None:
        return _langfuse_client

    if not _is_enabled() or not _credentials_present():
        _langfuse_available = False
        return None

    try:
        from langfuse import Langfuse  # type: ignore[import-untyped]

        _langfuse_client = Langfuse(
            public_key=os.getenv("LANGFUSE_PUBLIC_KEY", "").strip(),
            secret_key=os.getenv("LANGFUSE_SECRET_KEY", "").strip(),
            base_url=_base_url(),
            tracing_enabled=True,
        )
        _langfuse_available = True
        logger.info("Langfuse observability initialised")
        return _langfuse_client
    except Exception:
        _langfuse_available = False
        logger.debug("Langfuse not available; observability disabled", exc_info=True)
        return None


def get_client() -> Any | None:
    return _ensure_client()


def flush() -> None:
    client = get_client()
    if client is None:
        return
    try:
        client.flush()
    except Exception:
        logger.debug("Failed to flush Langfuse events", exc_info=True)


def shutdown() -> None:
    global _langfuse_client, _langfuse_available
    client = _langfuse_client
    if client is not None:
        try:
            client.shutdown()
        except Exception:
            logger.debug("Failed to shutdown Langfuse client", exc_info=True)
    _langfuse_client = None
    _langfuse_available = None


def create_trace(
    *,
    name: str,
    input: Any | None = None,
    metadata: dict[str, Any] | None = None,
    user_id: str | None = None,
    session_id: str | None = None,
    tags: list[str] | None = None,
    version: str | None = None,
) -> Any | None:
    client = get_client()
    if client is None:
        return None
    try:
        trace = client.start_observation(
            name=name,
            as_type="span",
            input=input,
            metadata=_merge_metadata(
                metadata,
                {
                    "user_id": user_id,
                    "session_id": session_id,
                    "tags": tags or [],
                },
            ),
            version=version,
        )
        return trace
    except Exception:
        logger.debug("Failed to create Langfuse root observation", exc_info=True)
        return None


def trace_llm_call(
    *,
    name: str,
    model: str,
    input: Any,
    output: Any,
    usage: dict[str, int] | None = None,
    cost_details: dict[str, float] | None = None,
    metadata: dict[str, Any] | None = None,
    latency_ms: float | None = None,
    trace: Any | None = None,
    level: str = "DEFAULT",
) -> Any | None:
    client = get_client()
    if client is None:
        return None

    generation_metadata = _merge_metadata(
        metadata,
        {"latency_ms": round(latency_ms, 2)} if latency_ms is not None else None,
    )

    try:
        if trace is not None:
            with trace.start_as_current_observation(
                name=name,
                as_type="generation",
                input=input,
                metadata=generation_metadata,
                model=model,
                usage_details=usage,
                cost_details=cost_details,
                level=level,
            ) as generation:
                generation.update(
                    output=output,
                    metadata=generation_metadata,
                    model=model,
                    usage_details=usage,
                    cost_details=cost_details,
                    level=level,
                )
                return generation

        with client.start_as_current_observation(
            name=name,
            as_type="generation",
            input=input,
            metadata=generation_metadata,
            model=model,
            usage_details=usage,
            cost_details=cost_details,
            level=level,
        ) as generation:
            generation.update(
                output=output,
                metadata=generation_metadata,
                model=model,
                usage_details=usage,
                cost_details=cost_details,
                level=level,
            )
            return generation
    except Exception:
        logger.debug("Failed to record Langfuse generation", exc_info=True)
        return None


def trace_span(
    *,
    name: str,
    trace: Any | None = None,
    input: Any | None = None,
    output: Any | None = None,
    metadata: dict[str, Any] | None = None,
) -> Any | None:
    client = get_client()
    if client is None:
        return None

    try:
        span = (
            trace.start_observation(
                name=name,
                as_type="span",
                input=input,
                output=output,
                metadata=metadata,
            )
            if trace is not None
            else client.start_observation(
                name=name,
                as_type="span",
                input=input,
                output=output,
                metadata=metadata,
            )
        )
        return span
    except Exception:
        logger.debug("Failed to record Langfuse span", exc_info=True)
        return None


def score_trace(
    *,
    name: str,
    value: float,
    trace: Any | None = None,
    trace_id: str | None = None,
    comment: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    if trace is not None:
        try:
            trace.score_trace(name=name, value=value, comment=comment, metadata=metadata)
            return
        except Exception:
            logger.debug("Failed to attach Langfuse trace score", exc_info=True)

    client = get_client()
    if client is None or not trace_id:
        return

    try:
        client.create_score(
            name=name,
            value=value,
            trace_id=trace_id,
            comment=comment,
            metadata=metadata,
        )
    except Exception:
        logger.debug("Failed to create Langfuse score", exc_info=True)


def observe(
    *,
    name: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> Callable:
    def decorator(fn: Callable) -> Callable:
        trace_name = name or fn.__qualname__

        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start = time.perf_counter()
            with trace_context(
                trace_name,
                input={"args": str(args)[:500], "kwargs": str(kwargs)[:500]},
                metadata=metadata,
            ) as trace:
                result = fn(*args, **kwargs)
                elapsed_ms = (time.perf_counter() - start) * 1000
                if trace is not None:
                    try:
                        trace.update(
                            output=str(result)[:2000],
                            metadata=_merge_metadata(metadata, {"latency_ms": round(elapsed_ms, 2)}),
                        )
                    except Exception:
                        logger.debug("Failed to update Langfuse observation", exc_info=True)
                return result

        return wrapper

    return decorator


@contextmanager
def trace_context(
    name: str,
    *,
    input: Any | None = None,
    metadata: dict[str, Any] | None = None,
    user_id: str | None = None,
    session_id: str | None = None,
    tags: list[str] | None = None,
    version: str | None = None,
) -> Generator[Any | None, None, None]:
    client = get_client()
    if client is None:
        yield None
        return

    from langfuse import propagate_attributes  # type: ignore[import-untyped]

    propagation = (
        propagate_attributes(
            user_id=user_id,
            session_id=session_id,
            metadata=_string_metadata(metadata),
            version=version,
            tags=tags,
            trace_name=name,
        )
        if any([user_id, session_id, metadata, version, tags])
        else nullcontext()
    )

    try:
        with client.start_as_current_observation(
            name=name,
            as_type="span",
            input=input,
            metadata=metadata,
            version=version,
        ) as trace:
            start = time.perf_counter()
            with propagation:
                try:
                    yield trace
                except Exception as exc:
                    elapsed_ms = (time.perf_counter() - start) * 1000
                    try:
                        trace.update(
                            output=f"ERROR: {exc}",
                            metadata=_merge_metadata(
                                metadata,
                                {"latency_ms": round(elapsed_ms, 2), "error": str(exc)},
                            ),
                            level="ERROR",
                            status_message=str(exc),
                        )
                    except Exception:
                        logger.debug("Failed to update Langfuse error observation", exc_info=True)
                    raise
    finally:
        flush()
