import re

from app.embedder import generate_embedding
from app.vector_store import VectorStore


_store: VectorStore | None = None

SEMANTIC_WEIGHT = 0.7
KEYWORD_WEIGHT = 0.3


def init_store(store: VectorStore) -> None:
    global _store
    _store = store


def _tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def _keyword_score(query_tokens: set[str], text: str) -> float:
    if not query_tokens:
        return 0.0
    text_tokens = _tokenize(text)
    matches = query_tokens & text_tokens
    return len(matches) / len(query_tokens)


def retrieve(query: str, top_k: int = 5) -> list[dict]:
    if not _store:
        raise RuntimeError("Vector store not initialized. Call init_store() first.")
    query_embedding = generate_embedding(query)
    semantic_results = _store.search(query_embedding, top_k=top_k * 3)

    query_tokens = _tokenize(query)

    scored = []
    for result in semantic_results:
        kw_score = _keyword_score(query_tokens, result["text"])
        combined = SEMANTIC_WEIGHT * result["score"] + KEYWORD_WEIGHT * kw_score
        scored.append({
            "text": result["text"],
            "score": combined,
            "semantic_score": result["score"],
            "keyword_score": kw_score,
            "metadata": result["metadata"],
        })

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_k]