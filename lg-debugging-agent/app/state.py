from __future__ import annotations

from typing import TypedDict

MAX_ITERATIONS = 3
EXEC_TIMEOUT = 10
REASONING_MODEL = "gemini-3.1-pro-preview"
EXPLANATION_MODEL = "gemini-3-flash-preview"


class DebugState(TypedDict, total=False):
    input_code: str
    error_message: str
    analysis: str
    diff: str
    fixed_code: str
    test_cases: str
    test_result: str
    iteration: int
    is_resolved: bool


def initial_state(input_code: str, error_message: str) -> DebugState:
    return DebugState(
        input_code=input_code,
        error_message=error_message,
        analysis="",
        diff="",
        fixed_code="",
        test_cases="",
        test_result="",
        iteration=0,
        is_resolved=False,
    )
