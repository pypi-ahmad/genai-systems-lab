"""Evaluator node – decides success/retry based on execution_result."""

from __future__ import annotations

from app.state import AnalysisState


def evaluator_node(state: AnalysisState) -> dict:
    iteration = state.get("iteration", 0) + 1
    result = state.get("execution_result", {})

    has_data = bool(result.get("data"))
    no_error = result.get("error") is None
    success = has_data and no_error

    return {"success": success, "iteration": iteration}
