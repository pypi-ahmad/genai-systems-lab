from __future__ import annotations

from contextvars import ContextVar
from typing import Any


_LAST_LLM_CALL_METADATA: ContextVar[dict[str, Any] | None] = ContextVar(
    "last_llm_call_metadata",
    default=None,
)


def clear_llm_call_metadata() -> None:
    _LAST_LLM_CALL_METADATA.set(None)


def record_llm_call_metadata(metadata: dict[str, Any] | None) -> None:
    _LAST_LLM_CALL_METADATA.set(metadata or None)


def consume_llm_call_metadata() -> dict[str, Any] | None:
    metadata = _LAST_LLM_CALL_METADATA.get()
    _LAST_LLM_CALL_METADATA.set(None)
    return metadata


__all__ = [
    "clear_llm_call_metadata",
    "consume_llm_call_metadata",
    "record_llm_call_metadata",
]