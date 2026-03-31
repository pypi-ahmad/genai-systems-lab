from __future__ import annotations

from app.knowledge_base import search
from app.state import RETRIEVAL_TOP_K, RELEVANCE_THRESHOLD, SupportState


def retriever_node(state: SupportState) -> dict:
    query = state.get("query", "")
    intent = state.get("intent", "")
    docs = search(query, intent=intent, top_k=RETRIEVAL_TOP_K, threshold=RELEVANCE_THRESHOLD)
    return {"retrieved_docs": docs}