from __future__ import annotations

from app.state import REASONING_MODEL, WorkflowState
from app.tools import file_tool, analysis_tool
from shared.llm.gemini import generate_text


TOOL_DESCRIPTIONS = (
    f"1. {file_tool.TOOL_DESCRIPTION}\n"
    f"2. {analysis_tool.TOOL_DESCRIPTION}"
)


def _build_prompt(task: str, plan: list[str], current_step: int, results: dict[str, str]) -> str:
    step_name = plan[current_step]

    prior = ""
    for i, s in enumerate(plan[:current_step]):
        result = results.get(s, "No result.")
        prior += f"  Step {i + 1} ({s}): {result}\n"

    return (
        "You are a workflow executor. Execute the current step using the available tools.\n\n"
        f"Overall task: {task}\n\n"
        f"Full plan:\n" + "\n".join(f"  {i + 1}. {s}" for i, s in enumerate(plan)) + "\n\n"
        f"Prior results:\n{prior or '  None yet.'}\n\n"
        f"Current step ({current_step + 1}/{len(plan)}): {step_name}\n\n"
        f"Available tools:\n{TOOL_DESCRIPTIONS}\n\n"
        "Execute this step and provide a clear, concise result. "
        "State which tool you used and what the outcome was."
    )


def executor_node(state: WorkflowState) -> dict:
    task = state.get("task", "")
    plan = state.get("plan", [])
    current_step = state.get("current_step", 0)
    results = dict(state.get("results", {}))

    if current_step >= len(plan):
        return {"results": results}

    step_name = plan[current_step]

    response = generate_text(
        prompt=_build_prompt(task, plan, current_step, results),
        model=REASONING_MODEL,
    )

    results[step_name] = response.strip() or f"Step '{step_name}' executed."
    return {"results": results}
