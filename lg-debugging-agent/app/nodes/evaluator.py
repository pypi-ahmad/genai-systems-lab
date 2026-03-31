from __future__ import annotations

from app.state import MAX_ITERATIONS, DebugState


def _test_passed(test_result: str) -> bool:
    return "exit_code: 0" in test_result and "stderr:" not in test_result


def evaluator_node(state: DebugState) -> dict:
    test_result = state.get("test_result", "")
    iteration = state.get("iteration", 0) + 1

    if _test_passed(test_result):
        return {"is_resolved": True, "iteration": iteration}

    if iteration >= MAX_ITERATIONS:
        return {"is_resolved": True, "iteration": iteration}

    return {"is_resolved": False, "iteration": iteration}
