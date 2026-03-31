"""Per-request step event emission for streaming project runs."""

from __future__ import annotations

from contextvars import ContextVar, Token
from typing import Callable

StepEmitter = Callable[[str, str], None]

_STEP_EMITTER: ContextVar[StepEmitter | None] = ContextVar("step_emitter", default=None)


def bind_step_emitter(emitter: StepEmitter | None) -> Token:
    """Bind an emitter for the current execution context."""
    return _STEP_EMITTER.set(emitter)



def reset_step_emitter(token: Token) -> None:
    """Restore the previous emitter binding."""
    _STEP_EMITTER.reset(token)



def emit_step(step: str, status: str) -> None:
    """Emit a step status if a request-scoped emitter is active."""
    emitter = _STEP_EMITTER.get()
    if emitter is None:
        return
    emitter(step, status)
