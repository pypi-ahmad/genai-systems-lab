"""Helpers for emitting step events from LangGraph node execution."""

from __future__ import annotations

from typing import Any, Callable

from .step_events import emit_step


NodeFn = Callable[[Any], Any]



def instrument_node(name: str, node_fn: NodeFn) -> NodeFn:
    """Wrap a node function so it emits running/done step events."""

    def wrapped(state: Any) -> Any:
        emit_step(name, "running")
        try:
            result = node_fn(state)
        except Exception:
            emit_step(name, "error")
            raise
        else:
            emit_step(name, "done")
            return result

    return wrapped
