"""Shared observability layer for production LLM monitoring.

Currently integrates Langfuse for traces, latency, token/cost tracking,
and prompt version history.  All integrations degrade gracefully when
the corresponding SDK is not installed or env vars are unset.
"""

from .langfuse import (
    create_trace,
    flush,
    get_client,
    observe,
    score_trace,
    shutdown,
    trace_context,
    trace_llm_call,
    trace_span,
)

__all__ = [
    "create_trace",
    "flush",
    "get_client",
    "observe",
    "score_trace",
    "shutdown",
    "trace_context",
    "trace_llm_call",
    "trace_span",
]
