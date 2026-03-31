"""LLM client using the Google Gen AI SDK.

Provides ``generate_fast`` and ``generate_pro`` helpers that call
Gemini models via :pypi:`google-genai` using the shared cached client
bound to the current request's ``x-api-key`` header.
"""

import logging
import time

from google import genai
from google.genai import errors, types

from shared.llm.gemini import _get_client
from src.config.settings import settings

logger = logging.getLogger(__name__)


def _client() -> genai.Client:
    """Return a cached Gemini client from the per-request API key."""
    return _get_client()

MAX_RETRIES = 3
RETRY_BACKOFF = 1.0  # seconds; doubles each retry


def _generate(prompt: str, *, model: str) -> str:
    """Call ``generate_content`` with retry logic.

    Args:
        prompt: The user prompt.
        model: Gemini model name.

    Returns:
        The model's text response.

    Raises:
        errors.APIError: After all retries are exhausted.
    """
    last_error: Exception | None = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.debug(
                "generate_content attempt=%d model=%s prompt_len=%d",
                attempt,
                model,
                len(prompt),
            )
            response = _client().models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=settings.temperature,
                ),
            )
            text = response.text or ""
            logger.debug("response len=%d", len(text))
            return text

        except errors.APIError as exc:
            last_error = exc
            logger.warning(
                "API error on attempt %d/%d (model=%s): [%s] %s",
                attempt,
                MAX_RETRIES,
                model,
                exc.code,
                exc.message,
            )
        except Exception as exc:
            last_error = exc
            logger.warning(
                "Unexpected error on attempt %d/%d (model=%s): %s",
                attempt,
                MAX_RETRIES,
                model,
                exc,
            )

        if attempt < MAX_RETRIES:
            wait = RETRY_BACKOFF * (2 ** (attempt - 1))
            logger.info("Retrying in %.1fs …", wait)
            time.sleep(wait)

    raise last_error  # type: ignore[misc]


def generate_fast(prompt: str) -> str:
    """Generate a response using the fast model (``gemini-3-flash-preview``)."""
    return _generate(prompt, model=settings.model_fast)


def generate_pro(prompt: str) -> str:
    """Generate a response using the pro model (``gemini-3.1-pro-preview``)."""
    return _generate(prompt, model=settings.model_pro)
