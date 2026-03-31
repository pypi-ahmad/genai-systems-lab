from __future__ import annotations

from app.state import CLASSIFICATION_MODEL, SupportState
from shared.llm.gemini import generate_structured

EVAL_SCHEMA = {
    "type": "object",
    "properties": {
        "relevance": {
            "type": "number",
            "description": "How relevant the response is to the query (0.0–1.0).",
        },
        "completeness": {
            "type": "number",
            "description": "How completely the response addresses the query (0.0–1.0).",
        },
    },
    "required": ["relevance", "completeness"],
}

ESCALATION_THRESHOLD = 0.5


def _format_history(history: list[dict[str, str]]) -> str:
    if not history:
        return ""
    lines = []
    for turn in history:
        lines.append(f"Customer: {turn.get('query', '')}")
        lines.append(f"Agent: {turn.get('response', '')}")
    return (
        "Conversation history:\n"
        + "\n".join(lines)
        + "\n\n"
    )


def _build_prompt(query: str, response: str, docs: list[str], history: list[dict[str, str]] | None = None) -> str:
    doc_summary = "\n".join(f"- {doc[:120]}" for doc in docs[:5]) if docs else "(none)"
    history_block = _format_history(history or [])
    return (
        "You are a quality evaluator for customer support responses.\n\n"
        "Score the response on two dimensions (0.0 to 1.0 each):\n"
        "- relevance: Does the response directly address the customer's question?\n"
        "- completeness: Does the response fully resolve the issue with actionable steps?\n\n"
        "Consider conversation history when judging relevance and completeness.\n\n"
        f"{history_block}"
        f"Customer query:\n{query}\n\n"
        f"Available reference articles:\n{doc_summary}\n\n"
        f"Response to evaluate:\n{response}"
    )


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def evaluator_node(state: SupportState) -> dict:
    query = state.get("query", "")
    response = state.get("response", "")
    docs = state.get("retrieved_docs", [])
    history = state.get("conversation_history", [])

    if not response.strip():
        return {"confidence": 0.0, "escalate": True}

    try:
        result = generate_structured(
            prompt=_build_prompt(query, response, docs, history),
            model=CLASSIFICATION_MODEL,
            schema=EVAL_SCHEMA,
        )
        relevance = _clamp(float(result.get("relevance", 0.0)))
        completeness = _clamp(float(result.get("completeness", 0.0)))
    except Exception:
        return {"confidence": 0.0, "escalate": True}

    confidence = round(0.6 * relevance + 0.4 * completeness, 4)
    escalate = confidence < ESCALATION_THRESHOLD

    return {"confidence": confidence, "escalate": escalate}