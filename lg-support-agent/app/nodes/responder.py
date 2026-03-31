from __future__ import annotations

from app.state import RESPONSE_MODEL, SupportState
from shared.llm.gemini import generate_text

FALLBACK_RESPONSE = (
    "Thank you for reaching out. I wasn't able to find specific information "
    "to address your question. A human agent will follow up with you shortly."
)


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


def _build_prompt(query: str, docs: list[str], history: list[dict[str, str]] | None = None) -> str:
    numbered = "\n".join(f"{i + 1}. {doc}" for i, doc in enumerate(docs))
    history_block = _format_history(history or [])
    return (
        "You are a professional customer support agent. Answer the customer's "
        "question using ONLY the reference articles below.\n\n"
        "Rules:\n"
        "- Be concise, empathetic, and professional.\n"
        "- Cite the relevant article number when referencing a solution.\n"
        "- If the articles do not fully cover the question, say so honestly.\n"
        "- Do NOT invent information beyond what the articles provide.\n"
        "- Use conversation history (if any) to maintain context and avoid repeating information.\n\n"
        f"{history_block}"
        f"Customer query:\n{query}\n\n"
        f"Reference articles:\n{numbered}"
    )


def responder_node(state: SupportState) -> dict:
    query = state.get("query", "")
    docs = state.get("retrieved_docs", [])
    history = state.get("conversation_history", [])

    if not docs:
        return {"response": FALLBACK_RESPONSE}

    response = generate_text(
        prompt=_build_prompt(query, docs, history),
        model=RESPONSE_MODEL,
    )

    return {"response": response}