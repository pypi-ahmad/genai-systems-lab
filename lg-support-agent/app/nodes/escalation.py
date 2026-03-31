from __future__ import annotations

from app.state import CLASSIFICATION_MODEL, SupportState
from shared.llm.gemini import generate_structured

TICKET_SCHEMA = {
    "type": "object",
    "properties": {
        "subject": {
            "type": "string",
            "description": "A short one-line ticket subject.",
        },
        "priority": {
            "type": "string",
            "description": "Ticket priority: low, medium, high, or urgent.",
        },
        "category": {
            "type": "string",
            "description": "Support category (e.g. billing, technical, account).",
        },
        "summary": {
            "type": "string",
            "description": "A concise summary of the customer's issue and what has been tried so far.",
        },
        "suggested_action": {
            "type": "string",
            "description": "Recommended next step for the human agent.",
        },
    },
    "required": ["subject", "priority", "category", "summary", "suggested_action"],
}

VALID_PRIORITIES = {"low", "medium", "high", "urgent"}


def _format_history(history: list[dict[str, str]]) -> str:
    if not history:
        return ""
    lines = []
    for turn in history:
        lines.append(f"Customer: {turn.get('query', '')}")
        lines.append(f"Agent: {turn.get('response', '')}")
    return "Conversation history:\n" + "\n".join(lines) + "\n\n"


def _build_prompt(state: SupportState) -> str:
    query = state.get("query", "")
    intent = state.get("intent", "")
    response = state.get("response", "")
    confidence = state.get("confidence", 0.0)
    history = state.get("conversation_history", [])

    history_block = _format_history(history)
    return (
        "You are a support ticket writer. Generate a structured escalation ticket "
        "for a human agent.\n\n"
        "Rules:\n"
        "- subject: a brief one-line description of the issue.\n"
        "- priority: one of low, medium, high, urgent. Base it on severity and customer impact.\n"
        "- category: the support category (billing, technical, account, returns, general).\n"
        "- summary: concise paragraph covering the issue, what was attempted, and why it's escalated.\n"
        "- suggested_action: concrete next step the human agent should take.\n\n"
        f"{history_block}"
        f"Customer query:\n{query}\n\n"
        f"Classified intent: {intent}\n"
        f"Confidence score: {confidence}\n\n"
        f"Draft automated response (low confidence):\n{response}"
    )


def escalation_node(state: SupportState) -> dict:
    try:
        ticket = generate_structured(
            prompt=_build_prompt(state),
            model=CLASSIFICATION_MODEL,
            schema=TICKET_SCHEMA,
        )
    except Exception:
        return {
            "ticket_summary": {
                "subject": state.get("query", "")[:100],
                "priority": "high",
                "category": state.get("intent", "unknown"),
                "summary": f"Automated escalation — confidence {state.get('confidence', 0.0):.2f}.",
                "suggested_action": "Review query and respond manually.",
            }
        }

    # Normalise priority
    priority = ticket.get("priority", "medium").strip().lower()
    if priority not in VALID_PRIORITIES:
        priority = "medium"
    ticket["priority"] = priority

    return {"ticket_summary": ticket}
