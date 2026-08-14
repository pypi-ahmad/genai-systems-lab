from __future__ import annotations

from contextvars import ContextVar
from typing import Any

_LAST_LLM_CALL_METADATA: ContextVar[dict[str, Any] | None] = ContextVar(
    "last_llm_call_metadata",
    default=None,
)
_LLM_RUN_CALLS: ContextVar[tuple[dict[str, Any], ...] | None] = ContextVar(
    "llm_run_calls", default=None
)


def clear_llm_call_metadata() -> None:
    _LAST_LLM_CALL_METADATA.set(None)


def record_llm_call_metadata(metadata: dict[str, Any] | None) -> None:
    if metadata:
        _LAST_LLM_CALL_METADATA.set({**(_LAST_LLM_CALL_METADATA.get() or {}), **metadata})


def consume_llm_call_metadata() -> dict[str, Any] | None:
    metadata = _LAST_LLM_CALL_METADATA.get()
    _LAST_LLM_CALL_METADATA.set(None)
    return metadata


def begin_llm_run() -> None:
    _LLM_RUN_CALLS.set(())


def record_llm_run_call(call: dict[str, Any]) -> None:
    calls = _LLM_RUN_CALLS.get()
    if calls is not None:
        _LLM_RUN_CALLS.set((*calls, call))


def consume_llm_run_usage() -> dict[str, Any] | None:
    calls = _LLM_RUN_CALLS.get()
    _LLM_RUN_CALLS.set(None)
    if not calls:
        return None
    input_tokens = sum(int(call.get("input_tokens") or 0) for call in calls)
    output_tokens = sum(int(call.get("output_tokens") or 0) for call in calls)
    costs = [call.get("estimated_cost_usd") for call in calls]
    models = list(dict.fromkeys(str(call["model_used"]) for call in calls))
    grouped_costs: dict[tuple[Any, ...], dict[str, Any]] = {}
    for call in calls:
        breakdown = call.get("cost_breakdown")
        if not isinstance(breakdown, dict):
            continue
        key = (
            breakdown.get("model"),
            breakdown.get("pricing_tier"),
            breakdown.get("input_rate_per_million_usd"),
            breakdown.get("cached_input_rate_per_million_usd"),
            breakdown.get("output_rate_per_million_usd"),
        )
        existing = grouped_costs.get(key)
        if existing is None:
            grouped_costs[key] = dict(breakdown)
            continue
        for field in (
            "input_tokens",
            "cached_input_tokens",
            "output_tokens",
            "input_cost_usd",
            "output_cost_usd",
            "estimated_cost_usd",
        ):
            existing[field] = round(float(existing.get(field) or 0) + float(breakdown.get(field) or 0), 8)
    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
        "estimated_cost_usd": round(sum(float(cost) for cost in costs if cost is not None), 8)
        if any(cost is not None for cost in costs)
        else None,
        "models_used": models,
        "cost_breakdown": list(grouped_costs.values()),
        "calls": list(calls),
    }


__all__ = [
    "begin_llm_run",
    "clear_llm_call_metadata",
    "consume_llm_call_metadata",
    "consume_llm_run_usage",
    "record_llm_call_metadata",
    "record_llm_run_call",
]
