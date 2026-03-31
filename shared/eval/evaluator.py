"""Shared evaluation helpers for task-level execution metrics."""

from __future__ import annotations

import time
from collections.abc import Iterable
from typing import Any, Callable


def run_evaluation(
    task_fn: Callable[..., Any],
    dataset: Iterable[Any],
) -> dict[str, Any]:
    """Run *task_fn* across a dataset and return structured metrics.

    The dataset may contain raw items or dictionaries with the following keys:

    - ``input``: primary positional argument passed to ``task_fn``
    - ``args``: additional positional arguments
    - ``kwargs``: keyword arguments
    - ``max_retries``: number of retries allowed after the initial attempt

    Each item produces a per-case metrics entry and contributes to the aggregate
    metrics for latency, success rate, error rate, and retries.
    """
    items = list(dataset)
    case_metrics: list[dict[str, Any]] = []

    total_retries = 0
    total_success = 0
    total_errors = 0
    latencies_ms: list[float] = []

    for index, item in enumerate(items):
        prepared = _prepare_case(item)
        case_result = _run_case(task_fn, index=index, case=prepared)

        case_metrics.append(case_result)
        latencies_ms.append(case_result["latency_ms"])
        total_retries += case_result["retries"]

        if case_result["success"]:
            total_success += 1
        else:
            total_errors += 1

    total = len(case_metrics)
    metrics = {
        "total": total,
        "successful": total_success,
        "failed": total_errors,
        "success_rate": (total_success / total) if total else 0.0,
        "error_rate": (total_errors / total) if total else 0.0,
        "retries": total_retries,
        "latency_ms": {
            "min": min(latencies_ms) if latencies_ms else 0.0,
            "max": max(latencies_ms) if latencies_ms else 0.0,
            "avg": (sum(latencies_ms) / total) if total else 0.0,
        },
        "cases": case_metrics,
    }
    return metrics


def _prepare_case(item: Any) -> dict[str, Any]:
    if isinstance(item, dict):
        if "input" in item:
            input_value = item["input"]
        else:
            input_value = item
        return {
            "input": input_value,
            "args": tuple(item.get("args", ())),
            "kwargs": dict(item.get("kwargs", {})),
            "max_retries": max(0, int(item.get("max_retries", 0))),
            "name": item.get("name"),
        }

    return {
        "input": item,
        "args": (),
        "kwargs": {},
        "max_retries": 0,
        "name": None,
    }


def _run_case(
    task_fn: Callable[..., Any],
    *,
    index: int,
    case: dict[str, Any],
) -> dict[str, Any]:
    start = time.perf_counter()
    max_retries = case["max_retries"]
    attempts = 0
    last_error: str | None = None
    output: Any = None

    while attempts <= max_retries:
        attempts += 1
        try:
            output = task_fn(case["input"], *case["args"], **case["kwargs"])
            last_error = None
            break
        except Exception as exc:
            last_error = str(exc)
            if attempts > max_retries:
                break

    latency_ms = (time.perf_counter() - start) * 1000
    success = last_error is None

    return {
        "index": index,
        "name": case["name"] or f"case_{index}",
        "success": success,
        "error": last_error,
        "retries": max(0, attempts - 1),
        "attempts": attempts,
        "latency_ms": latency_ms,
        "output": output,
    }
