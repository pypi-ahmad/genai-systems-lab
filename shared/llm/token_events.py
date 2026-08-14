from __future__ import annotations

from collections.abc import Callable
from contextvars import ContextVar, Token

TokenEmitter = Callable[[str], None]
_TOKEN_EMITTER: ContextVar[TokenEmitter | None] = ContextVar("llm_token_emitter", default=None)


def bind_token_emitter(emitter: TokenEmitter | None) -> Token[TokenEmitter | None]:
    return _TOKEN_EMITTER.set(emitter)


def reset_token_emitter(token: Token[TokenEmitter | None]) -> None:
    _TOKEN_EMITTER.reset(token)


def emit_token(text: str) -> None:
    emitter = _TOKEN_EMITTER.get()
    if emitter is not None and text:
        emitter(text)
