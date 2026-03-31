from __future__ import annotations

from app.state import EXPLANATION_MODEL, AnalysisState
from shared.llm.gemini import generate_text


def _build_prompt(query: str, plan: list[dict], execution_result: dict) -> str:
    ops = []
    for i, step in enumerate(plan):
        op = step.get("operation", "?")
        col = step.get("column", "?")
        parts = [f"Step {i + 1}: {op} on '{col}'"]
        for key in ("metric", "target", "condition", "value", "order"):
            if key in step:
                parts.append(f"{key}={step[key]}")
        ops.append("  ".join(parts))

    plan_text = "\n".join(ops) if ops else "(no operations)"

    data = execution_result.get("data", [])
    columns = execution_result.get("columns", [])
    shape = execution_result.get("shape", [])

    if isinstance(data, list):
        preview = data[:10]
    else:
        preview = data

    return (
        "You are a data analyst. The user asked a question and a series of "
        "data operations were executed. Explain the results clearly.\n\n"
        "Requirements:\n"
        "- Directly answer the user's question.\n"
        "- Highlight key findings, patterns, and notable values.\n"
        "- Note any caveats or limitations of the data.\n"
        "- Be concise but thorough.\n\n"
        f"User question:\n{query}\n\n"
        f"Operations executed:\n{plan_text}\n\n"
        f"Result columns: {columns}\n"
        f"Result shape: {shape}\n"
        f"Result data (up to 10 rows):\n{preview}"
    )


def analyzer_node(state: AnalysisState) -> dict:
    execution_result = state.get("execution_result", {})

    if execution_result.get("error"):
        return {"explanation": ""}

    query = state.get("query", "")
    plan = state.get("plan", [])

    if not query.strip():
        return {"explanation": "Analysis complete. See raw results."}

    try:
        response = generate_text(
            prompt=_build_prompt(query, plan, execution_result),
            model=EXPLANATION_MODEL,
        )
    except Exception:
        return {"explanation": "Analysis complete. See raw results."}

    explanation = response.strip() if response else "Analysis complete. See raw results."
    return {"explanation": explanation}