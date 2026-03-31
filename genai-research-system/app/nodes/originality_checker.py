from __future__ import annotations

from app.state import MAX_ORIGINALITY_REWRITES, REASONING_MODEL, ResearchState
from shared.llm.gemini import generate_structured


ORIGINALITY_SCHEMA = {
    "type": "object",
    "properties": {
        "score": {
            "type": "number",
            "description": (
                "Originality score from 0.0 to 1.0.  "
                "1.0 = highly original with novel insights; "
                "0.0 = entirely generic / boilerplate."
            ),
        },
        "passed": {
            "type": "boolean",
            "description": "True if the report is sufficiently original (score >= 0.7).",
        },
        "feedback": {
            "type": "string",
            "description": (
                "Specific, actionable feedback listing which sections are "
                "generic or lack original analysis.  Empty string if passed."
            ),
        },
    },
    "required": ["score", "passed", "feedback"],
}

ORIGINALITY_THRESHOLD = 0.7


def _build_prompt(report: str, query: str) -> str:
    return (
        "You are an originality reviewer. Evaluate the research report below "
        "for originality, depth of insight, and avoidance of generic filler.\n\n"
        f"Research query:\n{query}\n\n"
        f"Report:\n{report}\n\n"
        "Scoring guide:\n"
        "- 0.9-1.0: Contains novel analysis, unique comparisons, or non-obvious insights.\n"
        "- 0.7-0.9: Mostly original with some standard observations.\n"
        "- 0.4-0.7: Mixed — some original points but relies on common knowledge.\n"
        "- 0.0-0.4: Largely generic, boilerplate, or restates well-known facts.\n\n"
        "Rules:\n"
        "- Set passed=true only if score >= 0.7.\n"
        "- If not passed, provide specific feedback identifying which paragraphs "
        "or sections need more original analysis, concrete examples, or data.\n"
        "- Do NOT penalize factual accuracy — focus on depth and novelty."
    )


def originality_checker_node(state: ResearchState) -> dict:
    report = state.get("final_output", "")
    query = state.get("query", "")
    rewrites = state.get("originality_rewrites", 0)

    if not report.strip():
        return {
            "originality_score": 0.0,
            "originality_feedback": "",
            "originality_rewrites": rewrites,
        }

    if rewrites >= MAX_ORIGINALITY_REWRITES:
        return {
            "originality_score": state.get("originality_score", 0.0),
            "originality_feedback": "",
            "originality_rewrites": rewrites,
        }

    try:
        result = generate_structured(
            prompt=_build_prompt(report, query),
            model=REASONING_MODEL,
            schema=ORIGINALITY_SCHEMA,
        )
    except Exception:
        return {
            "originality_score": 1.0,
            "originality_feedback": "",
            "originality_rewrites": rewrites,
        }

    score = float(result.get("score", 1.0))
    score = max(0.0, min(1.0, score))
    passed = result.get("passed", score >= ORIGINALITY_THRESHOLD)
    feedback = result.get("feedback", "").strip()

    if passed or not feedback:
        return {
            "originality_score": score,
            "originality_feedback": "",
            "originality_rewrites": rewrites,
        }

    return {
        "originality_score": score,
        "originality_feedback": feedback,
        "originality_rewrites": rewrites + 1,
    }
