"""Reusable scoring metrics for evaluation and benchmarking."""

from __future__ import annotations

import re
from typing import Sequence


def keyword_accuracy(pred: str, expected: Sequence[str] | str) -> float:
    """Return the fraction of expected keywords found in ``pred``.

    ``expected`` may be either a sequence of keywords or a single whitespace-
    separated string of keywords. Matching is case-insensitive and based on
    substring presence.
    """
    if isinstance(expected, str):
        keywords = [token for token in expected.split() if token]
    else:
        keywords = [token for token in expected if token]

    if not keywords:
        return 1.0

    pred_lower = pred.lower()
    matches = sum(1 for keyword in keywords if keyword.lower() in pred_lower)
    return matches / len(keywords)


def structural_match(pred: str, pattern: str) -> float:
    """Return ``1.0`` if ``pred`` matches a regex or literal structure.

    If *pattern* looks like a regex, it is evaluated as one. If regex parsing
    fails, the function falls back to a case-insensitive substring check.
    """
    try:
        return 1.0 if re.search(pattern, pred, re.IGNORECASE) else 0.0
    except re.error:
        return 1.0 if pattern.lower() in pred.lower() else 0.0


def latency_stats(latencies_ms: Sequence[float]) -> dict[str, float]:
    """Compute min / max / mean / p95 from a list of latencies in ms."""
    if not latencies_ms:
        return {"min": 0.0, "max": 0.0, "mean": 0.0, "p95": 0.0}
    s = sorted(latencies_ms)
    n = len(s)
    return {
        "min": s[0],
        "max": s[-1],
        "mean": sum(s) / n,
        "p95": s[int(n * 0.95)] if n > 1 else s[0],
    }
