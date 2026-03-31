from __future__ import annotations

from app.state import MAX_EDITOR_REVISIONS, REASONING_MODEL, ResearchState
from shared.llm.gemini import generate_structured


EDITOR_SCHEMA = {
    "type": "object",
    "properties": {
        "approved": {
            "type": "boolean",
            "description": (
                "True if the report meets quality standards and needs no further "
                "revision. False if it needs improvement."
            ),
        },
        "feedback": {
            "type": "string",
            "description": (
                "Specific, actionable editorial feedback describing what the "
                "writer must fix — e.g. unclear sections, poor structure, "
                "weak transitions, redundancy, or missing context. "
                "Empty string if approved."
            ),
        },
    },
    "required": ["approved", "feedback"],
}


def _build_prompt(report: str, query: str, tone: str) -> str:
    return (
        "You are a senior editor reviewing a research report for publication. "
        "Evaluate the report for clarity, logical structure, coherence, "
        "readability, and tone consistency.\n\n"
        f"Research query: {query}\n"
        f"Requested tone: {tone}\n\n"
        f"Report:\n{report}\n\n"
        "Evaluation criteria:\n"
        "1. **Structure** — Does the report have a clear introduction, body, "
        "and conclusion? Are sections logically ordered?\n"
        "2. **Clarity** — Is every sentence easy to understand? Are technical "
        "terms explained where needed?\n"
        "3. **Coherence** — Do paragraphs flow logically? Are transitions smooth?\n"
        "4. **Tone** — Does the writing match the requested tone consistently?\n"
        "5. **Completeness** — Does the conclusion summarize key findings? "
        "Are there dangling references or incomplete thoughts?\n\n"
        "Rules:\n"
        "- Set approved=true ONLY if the report is ready for publication "
        "with no meaningful improvements needed.\n"
        "- If not approved, provide specific feedback listing EXACTLY what "
        "must be fixed, referencing section names or sentences.\n"
        "- Do NOT rewrite the report yourself — just describe the problems."
    )


def editor_node(state: ResearchState) -> dict:
    report = state.get("final_output", "")
    query = state.get("query", "")
    tone = state.get("tone", "formal")
    revisions = state.get("editor_revisions", 0)

    if not report.strip():
        return {"editor_feedback": "", "editor_revisions": revisions}

    if revisions >= MAX_EDITOR_REVISIONS:
        return {"editor_feedback": "", "editor_revisions": revisions}

    try:
        result = generate_structured(
            prompt=_build_prompt(report, query, tone),
            model=REASONING_MODEL,
            schema=EDITOR_SCHEMA,
        )
    except Exception:
        return {"editor_feedback": "", "editor_revisions": revisions}

    approved = result.get("approved", True)
    feedback = result.get("feedback", "").strip()

    if approved or not feedback:
        return {"editor_feedback": "", "editor_revisions": revisions}

    return {
        "editor_feedback": feedback,
        "editor_revisions": revisions + 1,
    }
