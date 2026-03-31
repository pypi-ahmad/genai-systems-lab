"""Generic helper functions reusable across all projects."""

from __future__ import annotations

import functools
import time
from typing import Any, Callable, TypeVar

T = TypeVar("T")


def chunk_text(text: str, max_chars: int = 2000, overlap: int = 200) -> list[str]:
    """Split *text* into overlapping chunks of up to *max_chars* characters.

    Tries to break on newlines or sentence boundaries when possible.
    """
    if len(text) <= max_chars:
        return [text]

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = start + max_chars
        if end < len(text):
            # Try to find a clean break point
            for sep in ("\n\n", "\n", ". ", " "):
                pos = text.rfind(sep, start + max_chars // 2, end)
                if pos != -1:
                    end = pos + len(sep)
                    break
        chunks.append(text[start:end])
        start = end - overlap if end < len(text) else end
    return chunks


def retry(
    attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple[type[BaseException], ...] = (Exception,),
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator that retries a function with exponential backoff.

    Usage::

        @retry(attempts=3, delay=1.0)
        def flaky_call():
            ...
    """

    def decorator(fn: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exc: BaseException | None = None
            for attempt in range(1, attempts + 1):
                try:
                    return fn(*args, **kwargs)
                except exceptions as exc:
                    last_exc = exc
                    if attempt < attempts:
                        time.sleep(delay * (backoff ** (attempt - 1)))
            raise last_exc  # type: ignore[misc]

        return wrapper

    return decorator


class Timer:
    """Context-manager for timing blocks of code.

    Usage::

        with Timer() as t:
            do_work()
        print(f"took {t.elapsed_ms:.1f}ms")
    """

    def __init__(self) -> None:
        self.elapsed_ms: float = 0.0
        self._start: float = 0.0

    def __enter__(self) -> Timer:
        self._start = time.perf_counter()
        return self

    def __exit__(self, *_: Any) -> None:
        self.elapsed_ms = (time.perf_counter() - self._start) * 1000
