from __future__ import annotations

from typing import TypedDict

MAX_ITERATIONS = 3
MAX_PLAN_STEPS = 10
REASONING_MODEL = "gemini-3.1-pro-preview"
EXPLANATION_MODEL = "gemini-3-flash-preview"

SUPPORTED_OPERATIONS = [
    "filter",
    "group_by",
    "sort",
    "aggregate",
    "pivot",
    "merge",
    "select",
    "drop",
    "rename",
]

SUPPORTED_ENGINES = ["pandas", "duckdb"]


class AnalysisState(TypedDict, total=False):
    query: str
    engine: str
    plan: list[dict]
    execution_result: dict
    explanation: str
    chart_path: str
    iteration: int
    success: bool


def initial_state(query: str, engine: str = "pandas") -> AnalysisState:
    return AnalysisState(
        query=query,
        engine=engine,
        plan=[],
        execution_result={},
        explanation="",
        chart_path="",
        iteration=0,
        success=False,
    )