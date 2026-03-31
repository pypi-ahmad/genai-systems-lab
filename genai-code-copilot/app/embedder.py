from __future__ import annotations

import time
from functools import lru_cache

from google.genai import errors, types

from shared.llm.gemini import _get_client


EMBEDDING_MODEL = "gemini-embedding-2-preview"
DEFAULT_BATCH_SIZE = 32
MAX_RETRY_ATTEMPTS = 3
BASE_BACKOFF_SECONDS = 1.0
DEFAULT_TASK_TYPE = "RETRIEVAL_DOCUMENT"


class EmbeddingGenerationError(RuntimeError):
	"""Raised when embedding generation fails."""


def _should_retry(exc: Exception) -> bool:
	if isinstance(exc, errors.ServerError):
		return True

	if isinstance(exc, errors.ClientError):
		return exc.code == 429

	return isinstance(exc, errors.APIError)


def _sleep_for_attempt(attempt: int) -> None:
	time.sleep(BASE_BACKOFF_SECONDS * (2 ** (attempt - 1)))


def _normalize_text(text: str) -> str:
	normalized = text.strip()
	if not normalized:
		raise ValueError("Text to embed must not be empty.")
	return normalized


def _extract_embedding_values(response: types.EmbedContentResponse) -> list[list[float]]:
	embeddings = response.embeddings or []
	values = [list(embedding.values or []) for embedding in embeddings]

	if not values or any(not embedding for embedding in values):
		raise EmbeddingGenerationError("Embedding response did not include vector values.")

	return values


def _embed_batch(texts: list[str]) -> list[list[float]]:
	normalized_texts = [_normalize_text(text) for text in texts]
	last_error: Exception | None = None

	for attempt in range(1, MAX_RETRY_ATTEMPTS + 1):
		try:
			response = _get_client().models.embed_content(
				model=EMBEDDING_MODEL,
				contents=normalized_texts,
				config=types.EmbedContentConfig(task_type=DEFAULT_TASK_TYPE),
			)
			return _extract_embedding_values(response)
		except (errors.APIError, ValueError) as exc:
			last_error = exc
			if attempt >= MAX_RETRY_ATTEMPTS or not _should_retry(exc):
				break
			_sleep_for_attempt(attempt)
		except Exception as exc:
			raise EmbeddingGenerationError("Unexpected embedding generation failure.") from exc

	raise EmbeddingGenerationError(
		f"Embedding generation failed after {MAX_RETRY_ATTEMPTS} attempts."
	) from last_error


def generate_embedding(text: str) -> list[float]:
	embeddings = _embed_batch([text])
	return embeddings[0]


def generate_embeddings_batch(texts: list[str]) -> list[list[float]]:
	if not texts:
		return []

	all_embeddings: list[list[float]] = []

	for start_index in range(0, len(texts), DEFAULT_BATCH_SIZE):
		batch = texts[start_index : start_index + DEFAULT_BATCH_SIZE]
		all_embeddings.extend(_embed_batch(batch))

	return all_embeddings


__all__ = [
	"EmbeddingGenerationError",
	"EMBEDDING_MODEL",
	"generate_embedding",
	"generate_embeddings_batch",
]
