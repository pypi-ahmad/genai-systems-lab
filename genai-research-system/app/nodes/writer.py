from __future__ import annotations

from app.state import REASONING_MODEL, WRITING_MODEL, ResearchState
from shared.llm.gemini import generate_structured, generate_text


SCENARIO_SCHEMA = {
    "label": "Short name for the scenario",
    "probability": "Estimated likelihood as a decimal between 0 and 1",
    "outcome": "Description of the projected outcome",
    "key_drivers": ["Factor that drives this scenario"],
    "implications": ["Practical implication if this scenario unfolds"],
}


def _build_prompt(query: str, plan: list[str], findings: dict[str, str], critiques: dict[str, str], tone: str, originality_feedback: str = "", editor_feedback: str = "") -> str:
    tone_guide = {
        "formal": "Use a formal, academic tone with precise language and structured argumentation.",
        "casual": "Use a casual, conversational tone that is accessible and easy to read.",
        "technical": "Use a technical tone with domain-specific terminology, detailed specifications, and data-driven language.",
    }
    parts = [
        "You are a research report writer. Synthesize the findings below into "
        "a polished Markdown report.\n",
        f"Tone: {tone_guide.get(tone, tone_guide['formal'])}\n",
        f"Research query:\n{query}\n",
    ]

    if originality_feedback:
        parts.append(
            f"IMPORTANT — Originality feedback from a previous draft (address these issues):\n"
            f"{originality_feedback}\n"
            "Rewrite the report with more original analysis, unique insights, "
            "concrete examples, and non-obvious observations. Avoid generic statements.\n"
        )

    if editor_feedback:
        parts.append(
            f"IMPORTANT — Editorial feedback from a previous draft (address these issues):\n"
            f"{editor_feedback}\n"
            "Revise the report to fix the structural, clarity, and coherence "
            "issues identified above.\n"
        )

    parts.append("Findings by task:")
    for task in plan:
        finding = findings.get(task, "No findings available.")
        parts.append(f"\n### {task}\n{finding}")

    if critiques:
        parts.append("\nUnresolved critiques (note these as limitations):")
        for task, critique in critiques.items():
            parts.append(f"- {task}: {critique}")

    parts.append(
        "\nReport format:\n"
        "- Title (derived from the query)\n"
        "- Executive Summary (2-3 sentences)\n"
        "- One section per task with detailed content\n"
        "- Conclusion\n"
        "- If there are unresolved critiques, add a Limitations section"
    )
    return "\n".join(parts)


def writer_node(state: ResearchState) -> dict:
    query = state.get("query", "")
    plan = state.get("plan", [])
    findings = state.get("findings", {})
    critiques = state.get("critiques", {})

    if not findings:
        return {"final_output": "No findings to report."}

    report = generate_text(
        prompt=_build_prompt(
            query, plan, findings, critiques,
            state.get("tone", "formal"),
            state.get("originality_feedback", ""),
            state.get("editor_feedback", ""),
        ),
        model=WRITING_MODEL,
    )

    best_case: dict = {}
    worst_case: dict = {}
    try:
        scenarios = generate_structured(
            prompt=_scenario_prompt(query, findings),
            model=REASONING_MODEL,
            schema={
                "best_case": SCENARIO_SCHEMA,
                "worst_case": SCENARIO_SCHEMA,
            },
        )
        if isinstance(scenarios.get("best_case"), dict):
            best_case = scenarios["best_case"]
        if isinstance(scenarios.get("worst_case"), dict):
            worst_case = scenarios["worst_case"]
    except Exception:
        pass

    return {
        "final_output": report,
        "editor_feedback": "",
        "best_case": best_case,
        "worst_case": worst_case,
    }


def _scenario_prompt(query: str, findings: dict[str, str]) -> str:
    parts = [
        "You are a scenario analyst. Based on the research findings below, "
        "simulate two scenarios: a best_case (optimistic) and a worst_case "
        "(pessimistic) projection.\n",
        f"Research query:\n{query}\n",
        "Findings:",
    ]
    for task, finding in findings.items():
        parts.append(f"\n### {task}\n{finding}")
    parts.append(
        "\nFor each scenario, provide:\n"
        "- label: a short descriptive name\n"
        "- probability: estimated likelihood (0.0–1.0)\n"
        "- outcome: what happens in this scenario\n"
        "- key_drivers: factors that make this scenario likely\n"
        "- implications: practical consequences"
    )
    return "\n".join(parts)
