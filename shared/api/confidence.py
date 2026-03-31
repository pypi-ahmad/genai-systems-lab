"""Confidence scoring helpers for project runs."""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Mapping, Sequence
from typing import Any

NUMERIC_EXACT_KEYS = {
    "accuracy",
    "adjusted_confidence",
    "avg_score",
    "behavioral_score",
    "confidence",
    "match_score",
    "overall_match_score",
    "quality_score",
    "relevance_score",
    "screening_score",
    "score",
    "semantic_score",
    "technical_score",
}
NUMERIC_PARTIAL_TOKENS = ("confidence", "score", "accuracy", "quality", "match", "relevance", "semantic")
NUMERIC_EXCLUDE_TOKENS = (
    "count",
    "latency",
    "ms",
    "step",
    "steps",
    "source",
    "question",
    "year",
    "weeks",
    "hours",
    "minutes",
    "chunk",
)
BOOLEAN_QUALITY_KEYS = {"fixed", "passed", "pass", "resolved", "valid"}
RETRY_KEYS = {"retries", "retry_count", "retrycount", "retry_attempts", "retryattempts"}
ATTEMPT_KEYS = {"attempt", "attempts", "iteration", "iterations", "pass_count", "passes"}


def compute_run_confidence(
    *,
    output_text: str,
    success: bool,
    latency_ms: float,
    timeline_entries: Sequence[Mapping[str, Any]] | None = None,
) -> tuple[float, dict[str, float]]:
    """Compute a hybrid confidence score for a project run.

    Formula:
      0.4 * evaluator_score
    + 0.3 * execution_success
    + 0.2 * consistency_score
    + 0.1 * latency_score
    """

    parsed_output = _parse_output_text(output_text)
    evaluator_score = _compute_evaluator_score(parsed_output, output_text, success)
    retries = _infer_retry_count(parsed_output, timeline_entries or ())
    consistency_score = round(1.0 / (1.0 + retries), 4)
    latency_score = round(5000.0 / (5000.0 + max(latency_ms, 0.0)), 4)
    execution_success = 1.0 if success else 0.0

    confidence = _clamp01(
        (0.4 * evaluator_score)
        + (0.3 * execution_success)
        + (0.2 * consistency_score)
        + (0.1 * latency_score)
    )

    return round(confidence, 2), {
        "evaluator_score": round(evaluator_score, 4),
        "execution_success": execution_success,
        "consistency_score": round(consistency_score, 4),
        "latency_score": round(latency_score, 4),
        "retries": float(retries),
    }


def _parse_output_text(output_text: str) -> Any:
    text = output_text.strip()
    if not text:
        return None

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def _compute_evaluator_score(parsed_output: Any, output_text: str, success: bool) -> float:
    weighted_candidates: list[tuple[float, float]] = []
    _collect_evaluator_candidates(parsed_output, weighted_candidates)
    if weighted_candidates:
        total_weight = sum(weight for _, weight in weighted_candidates)
        if total_weight > 0:
            return _clamp01(
                sum(value * weight for value, weight in weighted_candidates) / total_weight
            )

    if isinstance(parsed_output, Mapping):
        meaningful_fields = sum(1 for value in parsed_output.values() if _has_meaningful_value(value))
        if meaningful_fields >= 5:
            return 0.78 if success else 0.38
        if meaningful_fields >= 2:
            return 0.7 if success else 0.32
        if meaningful_fields >= 1:
            return 0.62 if success else 0.28

    if isinstance(parsed_output, list) and parsed_output:
        return 0.66 if success else 0.3

    if output_text.strip():
        return 0.58 if success else 0.24

    return 0.1 if success else 0.0


def _collect_evaluator_candidates(node: Any, candidates: list[tuple[float, float]]) -> None:
    if isinstance(node, Mapping):
        for raw_key, value in node.items():
            key = str(raw_key).strip().lower()
            if isinstance(value, bool):
                normalized = _normalize_boolean_metric(key, value)
                if normalized is not None:
                    candidates.append(normalized)
            elif isinstance(value, (int, float)):
                normalized = _normalize_numeric_metric(key, float(value))
                if normalized is not None:
                    candidates.append(normalized)
            else:
                _collect_evaluator_candidates(value, candidates)
        return

    if isinstance(node, Sequence) and not isinstance(node, (str, bytes, bytearray)):
        for item in node:
            _collect_evaluator_candidates(item, candidates)


def _normalize_numeric_metric(key: str, value: float) -> tuple[float, float] | None:
    if value < 0:
        return None

    if any(token in key for token in NUMERIC_EXCLUDE_TOKENS):
        return None

    if key in NUMERIC_EXACT_KEYS:
        normalized = _normalize_fraction(value)
        if normalized is not None:
            weight = 1.0 if "confidence" in key else 0.8
            return normalized, weight

    if any(token in key for token in NUMERIC_PARTIAL_TOKENS):
        normalized = _normalize_fraction(value)
        if normalized is not None:
            return normalized, 0.6

    return None


def _normalize_boolean_metric(key: str, value: bool) -> tuple[float, float] | None:
    if key in BOOLEAN_QUALITY_KEYS:
        return (1.0 if value else 0.0), 0.45
    return None


def _normalize_fraction(value: float) -> float | None:
    if 0.0 <= value <= 1.0:
        return round(value, 4)
    if 1.0 < value <= 100.0:
        return round(value / 100.0, 4)
    return None


def _infer_retry_count(parsed_output: Any, timeline_entries: Sequence[Mapping[str, Any]]) -> int:
    output_retries = _extract_output_retries(parsed_output)
    timeline_retries = _extract_timeline_retries(timeline_entries)
    return max(output_retries, timeline_retries)


def _extract_output_retries(node: Any) -> int:
    retries = 0
    if isinstance(node, Mapping):
        for raw_key, value in node.items():
            key = str(raw_key).strip().lower()
            if isinstance(value, bool):
                continue

            if isinstance(value, (int, float)):
                numeric_value = max(0, int(round(float(value))))
                if key in RETRY_KEYS:
                    retries = max(retries, numeric_value)
                elif key in ATTEMPT_KEYS:
                    retries = max(retries, max(0, numeric_value - 1))

            nested_retries = _extract_output_retries(value)
            retries = max(retries, nested_retries)
        return retries

    if isinstance(node, Sequence) and not isinstance(node, (str, bytes, bytearray)):
        for item in node:
            retries = max(retries, _extract_output_retries(item))

    return retries


def _extract_timeline_retries(timeline_entries: Sequence[Mapping[str, Any]]) -> int:
    running_steps = Counter(
        str(entry.get("step", "")).strip().lower()
        for entry in timeline_entries
        if str(entry.get("event", "")).strip().lower() == "running"
        and str(entry.get("step", "")).strip().lower() not in {"", "result"}
    )
    return sum(max(0, count - 1) for count in running_steps.values())


def _has_meaningful_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, Mapping):
        return any(_has_meaningful_value(item) for item in value.values())
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(_has_meaningful_value(item) for item in value)
    return True


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))