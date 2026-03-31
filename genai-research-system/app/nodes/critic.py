from __future__ import annotations

from app.state import MAX_REVISIONS, REASONING_MODEL, ResearchState
from shared.llm.gemini import generate_structured


CRITIC_SCHEMA = {
    "type": "object",
    "properties": {
        "approved": {
            "type": "boolean",
            "description": "True if the finding is adequate, False if revision is needed.",
        },
        "critique": {
            "type": "string",
            "description": "Specific, actionable feedback. Empty string if approved.",
        },
    },
    "required": ["approved", "critique"],
}


def _build_prompt(query: str, task: str, finding: str) -> str:
    return (
        "You are a research critic. Evaluate the finding below for accuracy, "
        "depth, evidence quality, and relevance to the task.\n\n"
        f"Overall research query:\n{query}\n\n"
        f"Task:\n{task}\n\n"
        f"Finding:\n{finding}\n\n"
        "Rules:\n"
        "- If the finding is thorough, well-supported, and addresses the task, "
        "set approved=true and leave critique empty.\n"
        "- If the finding has gaps, unsupported claims, or missing depth, "
        "set approved=false and provide specific, actionable feedback.\n"
        "- Do NOT request perfection — approve findings that are substantively adequate."
    )


def critic_node(state: ResearchState) -> dict:
    task = state.get("current_task", "")
    finding = state.get("findings", {}).get(task, "")
    iteration = state.get("iteration", 0)

    if not task.strip() or not finding.strip():
        return {"critiques": state.get("critiques", {}), "iteration": iteration}

    at_limit = iteration >= MAX_REVISIONS

    if at_limit:
        return {"critiques": state.get("critiques", {}), "iteration": iteration}

    result = generate_structured(
        prompt=_build_prompt(state.get("query", ""), task, finding),
        model=REASONING_MODEL,
        schema=CRITIC_SCHEMA,
    )

    approved = result.get("approved", True)
    critique_text = result.get("critique", "").strip()

    updated_critiques = dict(state.get("critiques", {}))

    if approved or not critique_text:
        updated_critiques.pop(task, None)
        return {"critiques": updated_critiques, "iteration": iteration}

    updated_critiques[task] = critique_text
    return {"critiques": updated_critiques, "iteration": iteration + 1}


# ---------------------------------------------------------------------------
# Parallel variant — critiques all findings concurrently
# ---------------------------------------------------------------------------

from concurrent.futures import ThreadPoolExecutor, as_completed


def _critique_single(
    query: str, task: str, finding: str,
) -> tuple[str, bool, str]:
    """Critique one finding. Returns *(task, approved, critique_text)*."""
    result = generate_structured(
        prompt=_build_prompt(query, task, finding),
        model=REASONING_MODEL,
        schema=CRITIC_SCHEMA,
    )
    approved = result.get("approved", True)
    critique_text = result.get("critique", "").strip()
    return task, approved, critique_text


def parallel_critic_node(state: ResearchState) -> dict:
    """Review all findings concurrently using threads."""
    plan = state.get("plan", [])
    findings = state.get("findings", {})
    query = state.get("query", "")
    iteration = state.get("iteration", 0)

    if iteration >= MAX_REVISIONS:
        return {"critiques": {}, "iteration": iteration}

    tasks_to_review = [t for t in plan if t in findings and findings[t].strip()]

    if not tasks_to_review:
        return {"critiques": {}, "iteration": iteration}

    updated_critiques: dict[str, str] = {}

    with ThreadPoolExecutor(max_workers=len(tasks_to_review)) as pool:
        futures = {
            pool.submit(_critique_single, query, task, findings[task]): task
            for task in tasks_to_review
        }
        for future in as_completed(futures):
            task, approved, critique_text = future.result()
            if not approved and critique_text:
                updated_critiques[task] = critique_text

    new_iteration = iteration + 1 if updated_critiques else iteration
    return {"critiques": updated_critiques, "iteration": new_iteration}
