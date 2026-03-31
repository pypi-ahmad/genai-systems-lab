from __future__ import annotations

from app.state import REASONING_MODEL, WorkflowState
from shared.llm.gemini import generate_structured


MAX_STEP_RETRIES = 2

VALIDATION_SCHEMA = {
    "type": "object",
    "properties": {
        "valid": {
            "type": "boolean",
            "description": "True if the step result satisfies its intent.",
        },
        "feedback": {
            "type": "string",
            "description": "If invalid, explain what is wrong and how to fix it.",
        },
    },
    "required": ["valid", "feedback"],
}


def _build_prompt(step_name: str, step_result: str, task: str, prior_results: dict[str, str]) -> str:
    prior = ""
    for name, res in prior_results.items():
        if name != step_name:
            prior += f"  {name}: {res}\n"

    return (
        "You are a workflow validator. Evaluate whether the step result "
        "satisfies the step's intent and is consistent with prior results.\n\n"
        f"Overall task: {task}\n\n"
        f"Prior results:\n{prior or '  None.'}\n\n"
        f"Step to validate: {step_name}\n"
        f"Step result:\n{step_result}\n\n"
        "Rules:\n"
        "- Mark valid=true if the result is substantive and addresses the step.\n"
        "- Mark valid=false if the result is empty, generic, or contradicts prior results.\n"
        "- Provide specific, actionable feedback when invalid."
    )


def validator_node(state: WorkflowState) -> dict:
    plan = state.get("plan", [])
    current_step = state.get("current_step", 0)
    results = state.get("results", {})
    iteration = state.get("iteration", 0)
    task = state.get("task", "")

    if current_step >= len(plan):
        return {"iteration": iteration}

    step_name = plan[current_step]
    step_result = results.get(step_name, "")

    # Empty result is always invalid
    if not step_result.strip():
        if iteration < MAX_STEP_RETRIES:
            return {"iteration": iteration + 1}
        return {"iteration": iteration}

    response = generate_structured(
        prompt=_build_prompt(step_name, step_result, task, results),
        model=REASONING_MODEL,
        schema=VALIDATION_SCHEMA,
    )

    valid = response.get("valid", False)

    if valid:
        return {"iteration": 0}

    # Invalid — allow retry if under limit
    if iteration < MAX_STEP_RETRIES:
        return {"iteration": iteration + 1}

    # Max retries exhausted — allow progression as best-effort
    return {"iteration": iteration}
