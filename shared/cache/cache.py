"""In-memory prompt-keyed cache for LLM responses and embeddings."""

from __future__ import annotations

import hashlib
import time
from typing import Any, Callable

from shared.logging import get_logger

LOGGER = get_logger("shared.cache")


def _hash_key(*parts: str) -> str:
    """Deterministic cache key: SHA-256 of ``|``-joined parts, truncated to 16 hex chars."""
    raw = "|".join(parts)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


class Cache:
    """Simple in-memory TTL cache keyed by hash(prompt).

    Usage::

        cache = Cache(ttl=300)
        key = cache.make_key("generate_text", prompt, model)
        hit = cache.get(key)
        if hit is None:
            result = call_llm(prompt, model)
            cache.set(key, result)
    """

    def __init__(self, *, ttl: int = 300) -> None:
        self._ttl = ttl
        self._store: dict[str, tuple[float, Any]] = {}

    # -- public API ------------------------------------------------------------

    @staticmethod
    def make_key(*parts: str) -> str:
        """Produce a deterministic cache key from arbitrary strings."""
        return _hash_key(*parts)

    def get(self, key: str) -> Any | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        expires, value = entry
        if time.time() > expires:
            del self._store[key]
            LOGGER.debug("cache expired: key=%s", key)
            return None
        LOGGER.debug("cache hit: key=%s", key)
        return value

    def set(self, key: str, value: Any) -> None:
        self._store[key] = (time.time() + self._ttl, value)
        LOGGER.debug("cache set: key=%s ttl=%s", key, self._ttl)

    def delete(self, key: str) -> bool:
        return self._store.pop(key, None) is not None

    def clear(self) -> None:
        self._store.clear()

    def has(self, key: str) -> bool:
        return self.get(key) is not None

    @property
    def size(self) -> int:
        self._evict()
        return len(self._store)

    def _evict(self) -> None:
        now = time.time()
        expired = [k for k, (exp, _) in self._store.items() if now > exp]
        for k in expired:
            del self._store[k]


# -- Global caches for LLM responses and embeddings ---------------------------

_llm_cache = Cache(ttl=600)
_embedding_cache = Cache(ttl=3600)


def cached_llm_call(
    fn: Callable[..., str],
    prompt: str,
    model: str,
    **kwargs: Any,
) -> str:
    """Call *fn(prompt, model, **kwargs)* with transparent prompt-keyed caching."""
    key = _llm_cache.make_key("llm", prompt, model)
    hit = _llm_cache.get(key)
    if hit is not None:
        return hit
    result = fn(prompt, model, **kwargs)
    _llm_cache.set(key, result)
    return result


def cached_embedding(
    fn: Callable[..., Any],
    text: str,
    **kwargs: Any,
) -> Any:
    """Call *fn(text, **kwargs)* with transparent text-keyed caching."""
    key = _embedding_cache.make_key("emb", text)
    hit = _embedding_cache.get(key)
    if hit is not None:
        return hit
    result = fn(text, **kwargs)
    _embedding_cache.set(key, result)
    return result


def get_llm_cache() -> Cache:
    """Return the global LLM response cache."""
    return _llm_cache


def get_embedding_cache() -> Cache:
    """Return the global embedding cache."""
    return _embedding_cache
