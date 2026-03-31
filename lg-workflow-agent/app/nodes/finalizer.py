from __future__ import annotations

from app.state import SUMMARY_MODEL, WorkflowState
from shared.llm.gemini import generate_text


def _build_prompt(task: str, plan: list[str], results: dict[str, str]) -> str:
    step_details = ""
    for i, step in enumerate(plan):
        result = results.get(step, "No result.")
        step_details += f"  Step {i + 1} – {step}:\n    {result}\n\n"

    return (
        "You are a workflow summariser. Combine the step results into a single, "
        "coherent final output that directly addresses the original task.\n\n"
        f"Task: {task}\n\n"
        f"Plan ({len(plan)} steps):\n{step_details}"
        "Rules:\n"
        "- Synthesise the results; do not just list them.\n"
        "- Highlight key findings, numbers, and conclusions.\n"
        "- Keep the output concise but complete."
    )


def finalizer_node(state: WorkflowState) -> dict:
    task = state.get("task", "")
    plan = state.get("plan", [])
    results = state.get("results", {})

    if not plan and not results:
        return {"results": results}

    summary = generate_text(
        prompt=_build_prompt(task, plan, results),
        model=SUMMARY_MODEL,
    )

    results = dict(results)
    results["_final_summary"] = summary.strip() or "Workflow completed."
    return {"results": results}
