"""Asyncio-based stress testing for throughput and error-rate analysis."""

from __future__ import annotations

import asyncio
import functools
import time
from dataclasses import dataclass, field
from typing import Any, Callable

from .metrics import latency_stats as _latency_stats


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass
class StressResult:
    """Aggregate output from a stress test run."""

    total_requests: int
    successful: int
    failed: int
    failure_rate: float
    avg_latency_ms: float
    p95_latency_ms: float
    latencies_ms: list[float] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    elapsed_s: float = 0.0


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def run_stress_test(
    task_fn: Callable[..., Any],
    *,
    concurrency: int = 20,
    total: int = 100,
    args: tuple[Any, ...] = (),
    kwargs: dict[str, Any] | None = None,
) -> StressResult:
    """Simulate *total* concurrent calls to *task_fn* and return metrics.

    ``task_fn`` may be a regular function **or** an async coroutine.
    Concurrency is controlled via an ``asyncio.Semaphore`` so you can
    safely set *total* > *concurrency* on rate-limited backends.

    Args:
        task_fn: The function to stress-test.
        concurrency: Max simultaneous in-flight calls (20–100).
        total: Total number of requests to issue.
        args: Positional arguments forwarded to *task_fn*.
        kwargs: Keyword arguments forwarded to *task_fn*.

    Returns:
        A ``StressResult`` with avg latency, p95 latency, failure rate,
        per-request latencies, and captured error messages.
    """
    kw = kwargs or {}
    is_coro = asyncio.iscoroutinefunction(task_fn)
    sem = asyncio.Semaphore(concurrency)

    async def _call() -> tuple[float, str | None]:
        async with sem:
            start = time.perf_counter()
            try:
                if is_coro:
                    await task_fn(*args, **kw)
                else:
                    loop = asyncio.get_running_loop()
                    await loop.run_in_executor(
                        None, functools.partial(task_fn, *args, **kw),
                    )
                return (time.perf_counter() - start) * 1000, None
            except Exception as exc:
                return (time.perf_counter() - start) * 1000, str(exc)

    wall_start = time.perf_counter()
    results = await asyncio.gather(*(_call() for _ in range(total)))
    elapsed = time.perf_counter() - wall_start

    latencies: list[float] = []
    errors: list[str] = []
    for ms, err in results:
        latencies.append(ms)
        if err is not None:
            errors.append(err)

    stats = _latency_stats(latencies)
    successful = total - len(errors)

    return StressResult(
        total_requests=total,
        successful=successful,
        failed=len(errors),
        failure_rate=len(errors) / total if total else 0.0,
        avg_latency_ms=stats.get("mean", 0.0),
        p95_latency_ms=stats.get("p95", 0.0),
        latencies_ms=latencies,
        errors=errors[:50],
        elapsed_s=elapsed,
    )


# ---------------------------------------------------------------------------
# Convenience wrapper for sync callers
# ---------------------------------------------------------------------------

class StressRunner:
    """Thin wrapper that calls ``run_stress_test`` from synchronous code.

    Usage::

        runner = StressRunner(fn=call_llm, args=("prompt",),
                              concurrency=20, total=100)
        result = runner.run()
    """

    def __init__(
        self,
        fn: Callable[..., Any],
        *,
        args: tuple[Any, ...] = (),
        kwargs: dict[str, Any] | None = None,
        concurrency: int = 20,
        total: int = 100,
    ) -> None:
        self.fn = fn
        self.args = args
        self.kwargs = kwargs or {}
        self.concurrency = concurrency
        self.total = total

    def run(self) -> StressResult:
        return asyncio.run(
            run_stress_test(
                self.fn,
                concurrency=self.concurrency,
                total=self.total,
                args=self.args,
                kwargs=self.kwargs,
            )
        )
