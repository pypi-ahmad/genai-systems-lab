import time
from functools import lru_cache

from google.genai import errors, types

from shared.llm.gemini import _get_client


EMBEDDING_MODEL = "gemini-embedding-2-preview"
BATCH_SIZE = 32
MAX_RETRIES = 3
BASE_BACKOFF = 1.0


def _should_retry(exc: Exception) -> bool:
    if isinstance(exc, errors.ServerError):
        return True
    if isinstance(exc, errors.ClientError):
        return exc.code == 429
    return False


def _embed_batch(texts: list[str]) -> list[list[float]]:
    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = _get_client().models.embed_content(
                model=EMBEDDING_MODEL,
                contents=texts,
                config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT"),
            )
            return [list(e.values) for e in response.embeddings]
        except (errors.APIError, ValueError) as exc:
            last_error = exc
            if attempt >= MAX_RETRIES or not _should_retry(exc):
                break
            time.sleep(BASE_BACKOFF * (2 ** (attempt - 1)))
    raise RuntimeError(f"Embedding failed after {MAX_RETRIES} attempts.") from last_error


def generate_embedding(text: str) -> list[float]:
    return _embed_batch([text])[0]


def batch_embeddings(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    results = []
    for i in range(0, len(texts), BATCH_SIZE):
        results.extend(_embed_batch(texts[i : i + BATCH_SIZE]))
    return results