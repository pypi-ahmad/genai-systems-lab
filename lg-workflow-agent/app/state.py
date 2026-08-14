from __future__ import annotations

from typing import TypedDict

MAX_RETRIES = 3
MAX_PLAN_STEPS = 10
REASONING_MODEL = "gemini-3.7-flash"
SUMMARY_MODEL = "gemini-3.5-flash-lite"


class WorkflowState(TypedDict, total=False):
    task: str
    plan: list[str]
    current_step: int
    results: dict[str, str]
    iteration: int
    completed: bool


def initial_state(task: str) -> WorkflowState:
    return WorkflowState(
        task=task,
        plan=[],
        current_step=0,
        results={},
        iteration=0,
        completed=False,
    )
