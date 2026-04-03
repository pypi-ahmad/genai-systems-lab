from __future__ import annotations

import json
import threading
import time
from typing import Any

from google import genai
from google.genai import errors, types

from shared.config import get_effective_api_key
from shared.logging import get_logger

from .exceptions import LLMGenerationError, LLMTimeoutError
from .telemetry import record_llm_call_metadata


SUPPORTED_MODELS = {
    "gemini-3-flash-preview",
    "gemini-3.1-pro-preview",
}
MAX_RETRY_ATTEMPTS = 3
BASE_BACKOFF_SECONDS = 1.0
REQUEST_TIMEOUT_SECONDS = 120


def _record_usage_metadata(response: types.GenerateContentResponse) -> None:
    usage_metadata = getattr(response, "usage_metadata", None)
    if usage_metadata is None:
        record_llm_call_metadata(None)
        return

    usage_details: dict[str, int] = {}
    attribute_map = {
        "prompt_token_count": "input",
        "candidates_token_count": "output",
        "total_token_count": "total",
        "cached_content_token_count": "input_cached_tokens",
        "thoughts_token_count": "output_reasoning_tokens",
    }

    for attribute_name, target_name in attribute_map.items():
        value = getattr(usage_metadata, attribute_name, None)
        if isinstance(value, int):
            usage_details[target_name] = value

    record_llm_call_metadata({"usage_details": usage_details} if usage_details else None)

MODEL_FALLBACK: dict[str, str] = {
    "gemini-3.1-pro-preview": "gemini-3-flash-preview",
}

LOGGER = get_logger("shared.llm.gemini")

_client_cache: dict[str, genai.Client] = {}
_client_lock = threading.Lock()


def _get_client() -> genai.Client:
    key = get_effective_api_key()
    client = _client_cache.get(key)
    if client is not None:
        return client
    with _client_lock:
        client = _client_cache.get(key)
        if client is None:
            client = genai.Client(api_key=key)
            _client_cache[key] = client
        return client


def _validate_model(model: str) -> None:
    if model not in SUPPORTED_MODELS:
        raise ValueError(
            f"Unsupported Gemini model '{model}'. Expected one of: {sorted(SUPPORTED_MODELS)}"
        )


def _should_retry(exc: Exception) -> bool:
    if isinstance(exc, errors.ServerError):
        return True
    if isinstance(exc, errors.ClientError):
        return exc.code == 429
    if isinstance(exc, errors.APIError):
        return True
    return False


def _sleep_for_attempt(attempt: int) -> None:
    time.sleep(BASE_BACKOFF_SECONDS * (2 ** (attempt - 1)))


def _request_content_single(
    *, prompt: str, model: str, config: types.GenerateContentConfig | None = None
) -> types.GenerateContentResponse:
    _validate_model(model)
    last_error: Exception | None = None

    for attempt in range(1, MAX_RETRY_ATTEMPTS + 1):
        try:
            LOGGER.info(
                "Gemini request started: model=%s attempt=%s prompt_chars=%s",
                model,
                attempt,
                len(prompt),
            )
            start = time.monotonic()
            response = _get_client().models.generate_content(
                model=model,
                contents=prompt,
                config=config,
            )
            elapsed = time.monotonic() - start
            if elapsed > REQUEST_TIMEOUT_SECONDS:
                raise LLMTimeoutError(
                    f"Gemini response received after {elapsed:.1f}s "
                    f"(timeout={REQUEST_TIMEOUT_SECONDS}s)"
                )
            LOGGER.info(
                "Gemini request succeeded: model=%s attempt=%s elapsed=%.1fs",
                model,
                attempt,
                elapsed,
            )
            return response
        except LLMTimeoutError:
            LOGGER.warning("Gemini request timed out: model=%s attempt=%s", model, attempt)
            raise
        except (errors.APIError, ValueError) as exc:
            last_error = exc
            LOGGER.warning(
                "Gemini request failed: model=%s attempt=%s error=%s",
                model,
                attempt,
                exc,
            )
            if attempt >= MAX_RETRY_ATTEMPTS or not _should_retry(exc):
                break
            _sleep_for_attempt(attempt)
        except Exception as exc:
            LOGGER.exception(
                "Unexpected Gemini request failure: model=%s attempt=%s",
                model,
                attempt,
            )
            raise LLMGenerationError("Unexpected Gemini request failure.") from exc

    raise LLMGenerationError(
        f"Gemini request failed after {MAX_RETRY_ATTEMPTS} attempts for model '{model}'."
    ) from last_error


def _request_content(
    *, prompt: str, model: str, config: types.GenerateContentConfig | None = None
) -> types.GenerateContentResponse:
    try:
        return _request_content_single(prompt=prompt, model=model, config=config)
    except (LLMGenerationError, LLMTimeoutError) as primary_err:
        fallback = MODEL_FALLBACK.get(model)
        if not fallback or fallback == model:
            raise
        LOGGER.warning("Falling back from %s to %s after error: %s", model, fallback, primary_err)
        return _request_content_single(prompt=prompt, model=fallback, config=config)


def generate_text(prompt: str, model: str) -> str:
    response = _request_content(prompt=prompt, model=model)
    _record_usage_metadata(response)
    text = (response.text or "").strip()
    if not text:
        raise LLMGenerationError("Gemini returned an empty text response.")
    return text


def generate_structured(prompt: str, model: str, schema: dict[str, Any]) -> dict[str, Any]:
    response = _request_content(
        prompt=prompt,
        model=model,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=schema,
        ),
    )
    _record_usage_metadata(response)

    if isinstance(response.parsed, dict):
        return response.parsed

    if response.parsed is not None and hasattr(response.parsed, "model_dump"):
        return response.parsed.model_dump()

    if response.text:
        parsed = json.loads(response.text)
        if isinstance(parsed, dict):
            return parsed

    raise LLMGenerationError("Gemini returned an invalid structured response.")


def _vision_request_single(
    *, prompt: str, image: bytes, model: str,
) -> types.GenerateContentResponse:
    _validate_model(model)
    last_error: Exception | None = None

    for attempt in range(1, MAX_RETRY_ATTEMPTS + 1):
        try:
            LOGGER.info(
                "Gemini vision request started: model=%s attempt=%s image_bytes=%s",
                model,
                attempt,
                len(image),
            )
            start = time.monotonic()
            response = _get_client().models.generate_content(
                model=model,
                contents=[
                    types.Part.from_bytes(data=image, mime_type="image/png"),
                    prompt,
                ],
            )
            elapsed = time.monotonic() - start
            if elapsed > REQUEST_TIMEOUT_SECONDS:
                raise LLMTimeoutError(
                    f"Vision response received after {elapsed:.1f}s "
                    f"(timeout={REQUEST_TIMEOUT_SECONDS}s)"
                )
            LOGGER.info(
                "Gemini vision request succeeded: model=%s attempt=%s elapsed=%.1fs",
                model,
                attempt,
                elapsed,
            )
            return response
        except LLMTimeoutError:
            LOGGER.warning("Gemini vision request timed out: model=%s attempt=%s", model, attempt)
            raise
        except (errors.APIError, ValueError) as exc:
            last_error = exc
            LOGGER.warning(
                "Gemini vision request failed: model=%s attempt=%s error=%s",
                model,
                attempt,
                exc,
            )
            if attempt >= MAX_RETRY_ATTEMPTS or not _should_retry(exc):
                break
            _sleep_for_attempt(attempt)
        except LLMGenerationError:
            raise
        except Exception as exc:
            LOGGER.exception(
                "Unexpected Gemini vision failure: model=%s attempt=%s",
                model,
                attempt,
            )
            raise LLMGenerationError("Unexpected Gemini vision failure.") from exc

    raise LLMGenerationError(
        f"Gemini vision request failed after {MAX_RETRY_ATTEMPTS} attempts for model '{model}'."
    ) from last_error


def generate_text_from_image(prompt: str, image: bytes, model: str) -> str:
    try:
        response = _vision_request_single(prompt=prompt, image=image, model=model)
    except (LLMGenerationError, LLMTimeoutError) as primary_err:
        fallback = MODEL_FALLBACK.get(model)
        if not fallback or fallback == model:
            raise
        LOGGER.warning("Vision falling back from %s to %s after error: %s", model, fallback, primary_err)
        response = _vision_request_single(prompt=prompt, image=image, model=fallback)

    _record_usage_metadata(response)
    text = (response.text or "").strip()
    if not text:
        raise LLMGenerationError("Gemini returned an empty vision response.")
    return text
