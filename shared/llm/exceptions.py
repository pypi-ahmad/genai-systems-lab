from __future__ import annotations


class LLMGenerationError(RuntimeError):
    """Raised when a provider request fails."""


class LLMTimeoutError(LLMGenerationError):
    """Raised when a provider request exceeds the timeout budget."""


GeminiGenerationError = LLMGenerationError
GeminiTimeoutError = LLMTimeoutError
