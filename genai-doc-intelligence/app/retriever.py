import re

from app.embedder import generate_embedding
from app.vector_store import VectorStore
from shared.llm.gemini import generate_text


_store: VectorStore | None = None

SEMANTIC_WEIGHT = 0.5
KEYWORD_WEIGHT = 0.2
RERANK_WEIGHT = 0.3

_RERANK_PROMPT = """You are a relevance scoring system.
Given a QUERY and a PASSAGE, rate how relevant the passage is to answering the query.
Return ONLY a single number between 0 and 10, where 0 means completely irrelevant and 10 means perfectly relevant.
Do not return any other text.

QUERY: {query}

PASSAGE: {passage}"""


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


def _parse_rerank_score(response: str) -> float:
    match = re.search(r"(\d+(?:\.\d+)?)", response.strip())
    if match:
        return min(float(match.group(1)) / 10.0, 1.0)
    return 0.5


def _rerank_score(query: str, text: str) -> float:
    try:
        prompt = _RERANK_PROMPT.format(query=query, passage=text[:1000])
        response = generate_text(prompt, model="gemini-3-flash-preview")
        return _parse_rerank_score(response)
    except Exception:
        return 0.5


def retrieve(query: str, top_k: int = 5, rerank: bool = True) -> list[dict]:
    if _store is None:
        raise RuntimeError("Vector store not initialized. Call init_store() first.")
    query_embedding = generate_embedding(query)
    semantic_results = _store.search(query_embedding, top_k=top_k * 3)

    query_tokens = _tokenize(query)

    candidates = []
    for result in semantic_results:
        kw_score = _keyword_score(query_tokens, result["text"])
        candidates.append({
            "text": result["text"],
            "semantic_score": result["score"],
            "keyword_score": kw_score,
            "metadata": result["metadata"],
        })

    if rerank:
        for candidate in candidates:
            candidate["rerank_score"] = _rerank_score(query, candidate["text"])
            candidate["score"] = (
                SEMANTIC_WEIGHT * candidate["semantic_score"]
                + KEYWORD_WEIGHT * candidate["keyword_score"]
                + RERANK_WEIGHT * candidate["rerank_score"]
            )
    else:
        for candidate in candidates:
            candidate["rerank_score"] = 0.0
            candidate["score"] = (
                SEMANTIC_WEIGHT * candidate["semantic_score"]
                + KEYWORD_WEIGHT * candidate["keyword_score"]
            )

    candidates.sort(key=lambda x: x["score"], reverse=True)
    return candidates[:top_k]
