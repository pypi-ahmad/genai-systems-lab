from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any

from app.graph import build_graph
from app.metrics import collect_research_metrics
from app.state import DEFAULT_FORMATS, DEFAULT_TONE, VALID_FORMATS, VALID_TONES, initial_state
from shared.logging import get_logger, log_context, new_request_id


LOGGER = get_logger(__name__)
PROJECT_NAME = "genai-research-system"


def normalize_formats(formats: tuple[str, ...] | list[str] | None) -> tuple[str, ...]:
    if not formats:
        return DEFAULT_FORMATS

    normalized: list[str] = []
    for fmt in formats:
        value = str(fmt).strip().lower()
        if not value:
            continue
        if value == "all":
            return ("report", "blog", "linkedin", "twitter")
        if value in VALID_FORMATS and value != "all" and value not in normalized:
            normalized.append(value)

    return tuple(normalized or DEFAULT_FORMATS)


def normalize_tone(tone: str | None) -> str:
    candidate = (tone or DEFAULT_TONE).strip().lower()
    if candidate not in VALID_TONES:
        return DEFAULT_TONE
    return candidate


def run_research_workflow(
    query: str,
    *,
    tone: str = DEFAULT_TONE,
    formats: tuple[str, ...] | list[str] | None = None,
    request_id: str | None = None,
) -> dict[str, Any]:
    run_id = request_id or new_request_id()
    normalized_tone = normalize_tone(tone)
    normalized_formats = normalize_formats(formats)
    started_at = datetime.now(timezone.utc).isoformat()

    with log_context(request_id=run_id, project_name=PROJECT_NAME):
        LOGGER.info(
            "research workflow started",
            extra={"error": "-"},
        )
        start = time.perf_counter()
        graph = build_graph()
        state = initial_state(query, tone=normalized_tone, formats=normalized_formats)
        state["run_id"] = run_id
        state["started_at"] = started_at

        try:
            result = graph.invoke(state)
        except Exception as exc:
            elapsed_ms = (time.perf_counter() - start) * 1000
            LOGGER.exception(
                "research workflow failed",
                extra={"latency_ms": f"{elapsed_ms:.2f}", "error": str(exc)},
            )
            raise

        elapsed_ms = (time.perf_counter() - start) * 1000
        result["run_id"] = run_id
        result["started_at"] = started_at
        result["completed_at"] = datetime.now(timezone.utc).isoformat()
        result["total_duration_ms"] = round(elapsed_ms, 2)
        result["quality_metrics"] = collect_research_metrics(query, result)

        LOGGER.info(
            "research workflow completed",
            extra={
                "latency_ms": f"{elapsed_ms:.2f}",
                "error": "-",
            },
        )

        return {
            "run_id": run_id,
            "query": query,
            "tone": normalized_tone,
            "formats": list(normalized_formats),
            "report": result.get("final_output", ""),
            "blog": result.get("blog", ""),
            "linkedin_post": result.get("linkedin_post", ""),
            "twitter_thread": result.get("twitter_thread", ""),
            "best_case": result.get("best_case", {}),
            "worst_case": result.get("worst_case", {}),
            "metrics": result["quality_metrics"],
            "node_timings": dict(result.get("node_timings", {}) or {}),
            "trace": list(result.get("execution_trace", []) or []),
            "state": result,
        }