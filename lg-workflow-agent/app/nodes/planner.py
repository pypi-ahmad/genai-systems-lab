from __future__ import annotations

from app.state import MAX_PLAN_STEPS, REASONING_MODEL, WorkflowState
from shared.llm.gemini import generate_structured


PLAN_SCHEMA = {
    "type": "object",
    "properties": {
        "steps": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Ordered list of workflow execution steps.",
        },
    },
    "required": ["steps"],
}

MIN_STEPS = 3
MAX_STEPS = 6


def _build_prompt(task: str) -> str:
    return (
        "You are a workflow planner. Break the following task into "
        f"{MIN_STEPS} to {MAX_STEPS} concrete, ordered execution steps.\n\n"
        "Rules:\n"
        "- Each step must be a single imperative sentence.\n"
        "- Steps must be sequentially dependent — each builds on the previous.\n"
        "- Each step must have a clear completion criteria.\n"
        "- Do NOT include vague steps like 'do more work' or 'continue analysis'.\n\n"
        f"Task:\n{task}"
    )


def planner_node(state: WorkflowState) -> dict:
    task = state.get("task", "")
    if not task.strip():
        return {"plan": ["Execute the task directly."], "current_step": 0, "iteration": 0}

    result = generate_structured(
        prompt=_build_prompt(task),
        model=REASONING_MODEL,
        schema=PLAN_SCHEMA,
    )

    steps = [s.strip() for s in result.get("steps", []) if s.strip()]

    if not steps:
        steps = [f"Execute: {task}"]

    return {"plan": steps[:min(MAX_STEPS, MAX_PLAN_STEPS)], "current_step": 0, "iteration": 0}
