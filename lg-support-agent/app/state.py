from __future__ import annotations

from typing import TypedDict

CONFIDENCE_THRESHOLD = 0.7
RETRIEVAL_TOP_K = 5
RELEVANCE_THRESHOLD = 0.3
CLASSIFICATION_MODEL = "gemini-3.1-pro-preview"
RESPONSE_MODEL = "gemini-3-flash-preview"
INTENT_LABELS = ["billing", "technical", "account", "returns", "general", "unknown"]


class SupportState(TypedDict, total=False):
    query: str
    intent: str
    retrieved_docs: list[str]
    response: str
    confidence: float
    escalate: bool
    conversation_history: list[dict[str, str]]
    ticket_summary: dict[str, str]


def initial_state(query: str, conversation_history: list[dict[str, str]] | None = None) -> SupportState:
    return SupportState(
        query=query,
        intent="",
        retrieved_docs=[],
        response="",
        confidence=0.0,
        escalate=False,
        conversation_history=conversation_history or [],
        ticket_summary={},
    )