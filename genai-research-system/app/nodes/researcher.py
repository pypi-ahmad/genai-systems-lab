from __future__ import annotations

from app.state import REASONING_MODEL, TOOLS, ResearchState
from shared.llm.gemini import generate_text


# Tool-specific research instructions injected into the researcher prompt.
_TOOL_INSTRUCTIONS: dict[str, str] = {
    "web_search": (
        "Approach: Search for the most recent, credible online sources. "
        "Cite specific publications, dates, and data points."
    ),
    "deep_analysis": (
        "Approach: Perform rigorous analytical reasoning. Break the topic into "
        "sub-components, evaluate trade-offs, and draw well-supported conclusions."
    ),
    "compare": (
        "Approach: Structure your response as a comparison. Use a clear framework "
        "(e.g. criteria-based table) to contrast the subjects. Highlight similarities "
        "and differences with concrete evidence."
    ),
    "summarize": (
        "Approach: Produce a concise summary of the topic. Identify the 3-5 most "
        "important points and present them clearly, omitting minor details."
    ),
    "fact_check": (
        "Approach: Verify the factual claims in this topic. Cross-reference multiple "
        "sources, note any conflicting evidence, and rate confidence for each claim."
    ),
}


def _build_prompt(query: str, task: str, critique: str | None, tone: str, tool: str = "") -> str:
    tone_guide = {
        "formal": "Write in a formal, academic style.",
        "casual": "Write in a casual, approachable style.",
        "technical": "Write in a technical style with precise terminology.",
    }
    parts = [
        "You are a research specialist. Produce detailed, evidence-based findings "
        "for the task below.",
        f"\nTone: {tone_guide.get(tone, tone_guide['formal'])}",
        f"\nOverall research query:\n{query}",
        f"\nCurrent task:\n{task}",
    ]

    # Inject tool-specific instructions when a tool is assigned.
    if tool:
        tool_desc = TOOLS.get(tool, "")
        tool_instr = _TOOL_INSTRUCTIONS.get(tool, "")
        parts.append(f"\nAssigned tool: {tool}")
        if tool_desc:
            parts.append(f"Tool purpose: {tool_desc}")
        if tool_instr:
            parts.append(tool_instr)

    if critique:
        parts.append(
            f"\nPrevious critique (address these issues):\n{critique}"
        )
    parts.append(
        "\nRequirements:\n"
        "- Be specific and cite concrete facts, comparisons, or data points.\n"
        "- Structure your response with clear sections.\n"
        "- If the critique above identifies gaps, focus on filling them.\n"
        "- Do NOT repeat the task statement — go straight to findings."
    )
    return "\n".join(parts)


def researcher_node(state: ResearchState) -> dict:
    task = state.get("current_task", "")
    query = state.get("query", "")

    if not task.strip():
        return {"findings": state.get("findings", {})}

    critique = state.get("critiques", {}).get(task)
    tool = state.get("tool_assignments", {}).get(task, "")

    finding = generate_text(
        prompt=_build_prompt(query, task, critique, state.get("tone", "formal"), tool),
        model=REASONING_MODEL,
    )

    updated = dict(state.get("findings", {}))
    updated[task] = finding
    return {"findings": updated}


# ---------------------------------------------------------------------------
# Parallel variant — researches all pending tasks concurrently
# ---------------------------------------------------------------------------

from concurrent.futures import ThreadPoolExecutor, as_completed


def _research_single(
    query: str, task: str, critique: str | None, tone: str, tool: str,
) -> tuple[str, str]:
    """Research a single task. Returns *(task, finding)*."""
    finding = generate_text(
        prompt=_build_prompt(query, task, critique, tone, tool),
        model=REASONING_MODEL,
    )
    return task, finding


def parallel_researcher_node(state: ResearchState) -> dict:
    """Research all pending tasks concurrently using threads."""
    query = state.get("query", "")
    plan = state.get("plan", [])
    findings = dict(state.get("findings", {}))
    critiques = state.get("critiques", {})
    tone = state.get("tone", "formal")
    tool_assignments = state.get("tool_assignments", {})

    # Revision pass → only re-research critiqued tasks.
    # First pass   → research every plan task not yet in findings.
    pending = (
        [t for t in plan if t in critiques]
        if critiques
        else [t for t in plan if t not in findings]
    )

    if not pending:
        return {"findings": findings}

    with ThreadPoolExecutor(max_workers=len(pending)) as pool:
        futures = {
            pool.submit(
                _research_single, query, task, critiques.get(task), tone,
                tool_assignments.get(task, ""),
            ): task
            for task in pending
        }
        for future in as_completed(futures):
            task, finding = future.result()
            findings[task] = finding

    return {"findings": findings}
