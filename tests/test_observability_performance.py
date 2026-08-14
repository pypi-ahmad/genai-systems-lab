"""Performance contracts for shared observability."""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

import pytest

from shared.observability import langfuse


class _Observation:
    def update(self, **_kwargs: Any) -> None:
        pass


class _Client:
    @contextmanager
    def start_as_current_observation(
        self, **_kwargs: Any
    ) -> Generator[_Observation]:
        yield _Observation()


def test_trace_context_does_not_flush_synchronously(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Trace completion must leave network delivery to the runner worker."""
    flush_calls = 0

    def record_flush() -> None:
        nonlocal flush_calls
        flush_calls += 1

    monkeypatch.setattr(langfuse, "get_client", lambda: _Client())
    monkeypatch.setattr(langfuse, "flush", record_flush)

    with langfuse.trace_context("performance-contract") as trace:
        assert trace is not None

    assert flush_calls == 0
