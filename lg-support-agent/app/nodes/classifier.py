from __future__ import annotations

from app.state import CLASSIFICATION_MODEL, INTENT_LABELS, SupportState
from shared.llm.gemini import generate_structured

INTENT_SCHEMA = {
    "type": "object",
    "properties": {
        "intent": {
            "type": "string",
            "description": "The classified intent label for the customer query.",
        },
    },
    "required": ["intent"],
}


def _format_history(history: list[dict[str, str]]) -> str:
    if not history:
        return ""
    lines = []
    for turn in history:
        lines.append(f"Customer: {turn.get('query', '')}")
        lines.append(f"Agent: {turn.get('response', '')}")
    return (
        "Conversation so far:\n"
        + "\n".join(lines)
        + "\n\n"
    )


def _build_prompt(query: str, history: list[dict[str, str]] | None = None) -> str:
    labels = ", ".join(INTENT_LABELS)
    history_block = _format_history(history or [])
    return (
        "You are a customer support classifier. Classify the following "
        "customer query into exactly one intent label.\n\n"
        f"Allowed labels: {labels}\n\n"
        "Rules:\n"
        "- Return exactly one label from the allowed list.\n"
        "- Use 'unknown' only if the query is unintelligible or fits no other label.\n"
        "- Consider the primary concern, not secondary details.\n"
        "- Use conversation history (if any) to disambiguate the query.\n\n"
        f"{history_block}"
        f"Customer query:\n{query}"
    )


def classifier_node(state: SupportState) -> dict:
    query = state.get("query", "")
    if not query.strip():
        return {"intent": "unknown"}

    history = state.get("conversation_history", [])

    result = generate_structured(
        prompt=_build_prompt(query, history),
        model=CLASSIFICATION_MODEL,
        schema=INTENT_SCHEMA,
    )

    intent = result.get("intent", "unknown").strip().lower()
    if intent not in INTENT_LABELS:
        intent = "unknown"

    return {"intent": intent}