from __future__ import annotations

from app.state import MAX_PLAN_TASKS, REASONING_MODEL, TOOLS, ResearchState
from shared.llm.gemini import generate_structured


PLAN_SCHEMA = {
    "type": "object",
    "properties": {
        "tasks": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "task": {
                        "type": "string",
                        "description": "A concrete, bounded research sub-task.",
                    },
                    "tool": {
                        "type": "string",
                        "description": "The tool best suited for this sub-task.",
                    },
                },
                "required": ["task", "tool"],
            },
            "description": "Ordered list of research sub-tasks with tool assignments.",
        },
    },
    "required": ["tasks"],
}

DEFAULT_TOOL = "deep_analysis"


def _build_prompt(query: str) -> str:
    tool_block = "\n".join(f"- {name}: {desc}" for name, desc in TOOLS.items())
    return (
        "You are a research planner. Break the following query into "
        f"3 to {MAX_PLAN_TASKS} concrete, bounded research sub-tasks.\n\n"
        "For each sub-task, choose the single best tool from the list below:\n"
        f"{tool_block}\n\n"
        "Rules:\n"
        "- Each task must be specific and directly executable.\n"
        "- Tasks should cover distinct aspects of the query.\n"
        "- Order tasks from foundational to advanced.\n"
        "- Do NOT include vague tasks like 'research more' or 'analyze deeper'.\n"
        "- Choose the tool that best fits the nature of each task.\n\n"
        f"Query:\n{query}"
    )


def planner_node(state: ResearchState) -> dict:
    query = state.get("query", "")
    if not query.strip():
        return {
            "plan": [query.strip() or "Address the research query."],
            "tool_assignments": {},
        }

    result = generate_structured(
        prompt=_build_prompt(query),
        model=REASONING_MODEL,
        schema=PLAN_SCHEMA,
    )

    raw_tasks = result.get("tasks", [])

    plan: list[str] = []
    tool_assignments: dict[str, str] = {}

    for entry in raw_tasks:
        if isinstance(entry, dict):
            task = entry.get("task", "").strip()
            tool = entry.get("tool", DEFAULT_TOOL).strip()
        elif isinstance(entry, str):
            task = entry.strip()
            tool = DEFAULT_TOOL
        else:
            continue

        if not task:
            continue

        # Validate tool name — fall back to default if unknown.
        if tool not in TOOLS:
            tool = DEFAULT_TOOL

        plan.append(task)
        tool_assignments[task] = tool

    if not plan:
        plan = [f"Research: {query}"]
        tool_assignments[plan[0]] = DEFAULT_TOOL

    plan = plan[:MAX_PLAN_TASKS]
    tool_assignments = {t: tool_assignments[t] for t in plan}

    return {"plan": plan, "tool_assignments": tool_assignments}
