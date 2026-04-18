from __future__ import annotations

import base64
import copy
import hashlib
import json
import logging
import math
import random
import threading
import time
from typing import Any
from urllib.parse import urlparse

try:
    import httpx  # type: ignore[import-not-found]
    _HTTPX_AVAILABLE = True
except ImportError:  # pragma: no cover — graceful degradation
    httpx = None  # type: ignore[assignment]
    _HTTPX_AVAILABLE = False

from shared.config import get_effective_api_key

from .catalog import ollama_base_url, ollama_embedding_model, openai_embedding_model
from .exceptions import LLMGenerationError, LLMTimeoutError
from .telemetry import record_llm_call_metadata


REQUEST_TIMEOUT_SECONDS = 120
MAX_RETRY_ATTEMPTS = 3
BASE_BACKOFF_SECONDS = 1.0
# Max jittered backoff to avoid every client retrying in lock-step.
MAX_BACKOFF_SECONDS = 30.0

_LOGGER = logging.getLogger(__name__)

# Shared httpx.Client for keepalive/connection-pool reuse across LLM calls.
# urllib's ``urlopen`` opens a fresh TCP+TLS connection for every request, so
# switching to httpx saves ~30–80 ms/call per provider.  Falls back to urllib
# when httpx is unavailable so installations without the optional dep still
# work.
_HTTP_CLIENT_LOCK = threading.Lock()
_HTTP_CLIENT: Any | None = None


def _http_client() -> Any | None:
    global _HTTP_CLIENT
    if not _HTTPX_AVAILABLE:
        return None
    if _HTTP_CLIENT is not None:
        return _HTTP_CLIENT
    with _HTTP_CLIENT_LOCK:
        if _HTTP_CLIENT is None:
            _HTTP_CLIENT = httpx.Client(
                timeout=httpx.Timeout(REQUEST_TIMEOUT_SECONDS, connect=10.0),
                limits=httpx.Limits(
                    max_keepalive_connections=20,
                    max_connections=100,
                    keepalive_expiry=30.0,
                ),
                http2=False,
                follow_redirects=False,
            )
    return _HTTP_CLIENT


# Ollama is hosted locally; when ``OLLAMA_BASE_URL`` is user-controllable via
# environment, this is still a potential SSRF sink.  We only allow the schemes
# we actually use.
_ALLOWED_SCHEMES = frozenset({"http", "https"})


def _validate_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in _ALLOWED_SCHEMES:
        raise LLMGenerationError(f"Refusing to call LLM endpoint with scheme '{parsed.scheme}'.")
    if not parsed.netloc:
        raise LLMGenerationError("LLM endpoint URL is missing a host.")


def _coerce_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return int(value)
    return None


def _flatten_usage_details(prefix: str, payload: Any, usage_details: dict[str, int]) -> None:
    if not isinstance(payload, dict):
        return
    for key, value in payload.items():
        coerced = _coerce_int(value)
        if coerced is not None:
            usage_details[f"{prefix}_{key}"] = coerced


def _record_openai_usage(response: dict[str, Any]) -> None:
    usage_payload = response.get("usage")
    if not isinstance(usage_payload, dict):
        record_llm_call_metadata(None)
        return

    usage_details: dict[str, int] = {}

    input_tokens = _coerce_int(usage_payload.get("input_tokens"))
    if input_tokens is not None:
        usage_details["input"] = input_tokens

    output_tokens = _coerce_int(usage_payload.get("output_tokens"))
    if output_tokens is not None:
        usage_details["output"] = output_tokens

    total_tokens = _coerce_int(usage_payload.get("total_tokens"))
    if total_tokens is not None:
        usage_details["total"] = total_tokens

    _flatten_usage_details("input", usage_payload.get("input_tokens_details"), usage_details)
    _flatten_usage_details("output", usage_payload.get("output_tokens_details"), usage_details)

    record_llm_call_metadata({"usage_details": usage_details} if usage_details else None)


def _record_anthropic_usage(response: dict[str, Any]) -> None:
    usage_payload = response.get("usage")
    if not isinstance(usage_payload, dict):
        record_llm_call_metadata(None)
        return

    usage_details: dict[str, int] = {}

    input_tokens = _coerce_int(usage_payload.get("input_tokens"))
    if input_tokens is not None:
        usage_details["input"] = input_tokens

    output_tokens = _coerce_int(usage_payload.get("output_tokens"))
    if output_tokens is not None:
        usage_details["output"] = output_tokens

    cache_creation_tokens = _coerce_int(usage_payload.get("cache_creation_input_tokens"))
    if cache_creation_tokens is not None:
        usage_details["input_cache_write_tokens"] = cache_creation_tokens

    cache_read_tokens = _coerce_int(usage_payload.get("cache_read_input_tokens"))
    if cache_read_tokens is not None:
        usage_details["input_cache_read_tokens"] = cache_read_tokens

    if usage_details and "total" not in usage_details:
        usage_details["total"] = sum(usage_details.values())

    record_llm_call_metadata({"usage_details": usage_details} if usage_details else None)


def _sleep_for_attempt(attempt: int, *, retry_after: float | None = None) -> None:
    """Exponential backoff with jitter.

    Honours a server-provided ``Retry-After`` hint when present — OpenAI and
    Anthropic both return it on 429.  Adds ±20% jitter to avoid thundering
    herd when many clients share the same rate limit.
    """
    base = float(retry_after) if retry_after and retry_after > 0 else BASE_BACKOFF_SECONDS * (2 ** (attempt - 1))
    base = min(base, MAX_BACKOFF_SECONDS)
    jitter = 1.0 + random.uniform(-0.2, 0.2)
    time.sleep(max(0.1, base * jitter))


def _should_retry_status(status_code: int) -> bool:
    # 408 (request timeout) and 425 (too early) are also safe to retry.
    return status_code in {408, 425, 429} or 500 <= status_code < 600


def _parse_retry_after(raw: str | None) -> float | None:
    if not raw:
        return None
    try:
        return float(raw.strip())
    except ValueError:
        return None


def _extract_error_message(raw: bytes) -> str:
    try:
        payload = json.loads(raw.decode("utf-8"))
    except Exception:
        return raw.decode("utf-8", errors="ignore") or "Unknown provider error."

    if isinstance(payload, dict):
        error_payload = payload.get("error")
        if isinstance(error_payload, dict):
            for key in ("message", "detail", "error"):
                value = error_payload.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()
        for key in ("detail", "message", "error"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()

    return raw.decode("utf-8", errors="ignore") or "Unknown provider error."


def _request_json(
    *,
    url: str,
    headers: dict[str, str],
    payload: dict[str, Any] | None = None,
    method: str = "POST",
    timeout: float = REQUEST_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    _validate_url(url)
    body = None if payload is None else json.dumps(payload).encode("utf-8")

    client = _http_client()
    if client is None:
        # httpx is a hard requirement — a urllib fallback subtly changes error
        # shapes, loses HTTP/2 + keepalive, and re-opens a TCP+TLS connection
        # on every request under pressure.  Fail fast with a clear message.
        raise LLMGenerationError(
            "httpx is required for LLM provider requests but is not installed. "
            "Install it via `pip install httpx`."
        )

    return _request_json_httpx(
        client=client,
        url=url,
        headers=headers,
        body=body,
        method=method,
        timeout=timeout,
    )


def _request_json_httpx(
    *,
    client: Any,
    url: str,
    headers: dict[str, str],
    body: bytes | None,
    method: str,
    timeout: float,
) -> dict[str, Any]:
    """httpx implementation — shared keepalive pool, real Retry-After honouring."""
    last_error: Exception | None = None
    for attempt in range(1, MAX_RETRY_ATTEMPTS + 1):
        try:
            response = client.request(
                method=method,
                url=url,
                headers=headers,
                content=body,
                timeout=timeout,
            )
        except httpx.TimeoutException as exc:  # type: ignore[union-attr]
            last_error = LLMTimeoutError(f"Provider request timed out: {exc}")
            if attempt >= MAX_RETRY_ATTEMPTS:
                raise last_error from exc
            _sleep_for_attempt(attempt)
            continue
        except httpx.HTTPError as exc:  # type: ignore[union-attr]
            last_error = LLMGenerationError(f"Provider transport error: {exc}")
            if attempt >= MAX_RETRY_ATTEMPTS:
                raise last_error from exc
            _sleep_for_attempt(attempt)
            continue

        if response.status_code >= 400:
            message = _extract_error_message(response.content)
            retry_after = _parse_retry_after(response.headers.get("Retry-After"))
            if not _should_retry_status(response.status_code) or attempt >= MAX_RETRY_ATTEMPTS:
                raise LLMGenerationError(message)
            _sleep_for_attempt(attempt, retry_after=retry_after)
            last_error = LLMGenerationError(message)
            continue

        try:
            parsed = response.json()
        except ValueError as exc:
            raise LLMGenerationError("Provider returned malformed JSON.") from exc
        if not isinstance(parsed, dict):
            raise LLMGenerationError("Provider returned an invalid JSON payload.")
        return parsed

    raise LLMGenerationError("Provider request failed.") from last_error


def _normalize_schema(schema: dict[str, Any]) -> dict[str, Any]:
    normalized = copy.deepcopy(schema)

    def walk(node: Any) -> Any:
        if isinstance(node, list):
            return [walk(item) for item in node]
        if not isinstance(node, dict):
            return node

        transformed = {key: walk(value) for key, value in node.items()}
        node_type = transformed.get("type")
        type_values = node_type if isinstance(node_type, list) else [node_type]
        is_object = "object" in type_values

        if "properties" in transformed and isinstance(transformed["properties"], dict):
            transformed["properties"] = {
                key: walk(value)
                for key, value in transformed["properties"].items()
            }

        if is_object:
            properties = transformed.get("properties")
            if isinstance(properties, dict):
                transformed.setdefault("required", list(properties.keys()))
            transformed.setdefault("additionalProperties", False)

        if "items" in transformed:
            transformed["items"] = walk(transformed["items"])
        if "$defs" in transformed and isinstance(transformed["$defs"], dict):
            transformed["$defs"] = {key: walk(value) for key, value in transformed["$defs"].items()}
        if "definitions" in transformed and isinstance(transformed["definitions"], dict):
            transformed["definitions"] = {key: walk(value) for key, value in transformed["definitions"].items()}
        if "anyOf" in transformed and isinstance(transformed["anyOf"], list):
            transformed["anyOf"] = [walk(item) for item in transformed["anyOf"]]

        return transformed

    result = walk(normalized)
    if not isinstance(result, dict):
        raise LLMGenerationError("Structured output schema must be a JSON object schema.")
    return result


def _data_url(image: bytes, mime_type: str = "image/png") -> str:
    encoded = base64.b64encode(image).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def _extract_openai_text(payload: dict[str, Any]) -> str:
    text = payload.get("output_text")
    if isinstance(text, str) and text.strip():
        return text.strip()

    output = payload.get("output")
    if isinstance(output, list):
        for item in output:
            if not isinstance(item, dict):
                continue
            content = item.get("content")
            if isinstance(content, list):
                fragments: list[str] = []
                for block in content:
                    if not isinstance(block, dict):
                        continue
                    refusal = block.get("refusal")
                    if isinstance(refusal, str) and refusal.strip():
                        raise LLMGenerationError(refusal.strip())
                    block_text = block.get("text")
                    if isinstance(block_text, str):
                        fragments.append(block_text)
                if fragments:
                    return "".join(fragments).strip()

    raise LLMGenerationError("OpenAI returned an empty text response.")


def openai_generate_text(prompt: str, model: str, *, temperature: float | None = None) -> str:
    headers = {
        "Authorization": f"Bearer {get_effective_api_key()}",
        "Content-Type": "application/json",
    }
    payload: dict[str, Any] = {
        "model": model,
        "input": prompt,
    }
    if temperature is not None:
        payload["temperature"] = temperature
    response = _request_json(url="https://api.openai.com/v1/responses", headers=headers, payload=payload)
    _record_openai_usage(response)
    return _extract_openai_text(response)


def openai_generate_structured(prompt: str, model: str, schema: dict[str, Any]) -> dict[str, Any]:
    headers = {
        "Authorization": f"Bearer {get_effective_api_key()}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "input": prompt,
        "text": {
            "format": {
                "type": "json_schema",
                "name": "structured_response",
                "strict": True,
                "schema": _normalize_schema(schema),
            }
        },
    }
    response = _request_json(url="https://api.openai.com/v1/responses", headers=headers, payload=payload)
    _record_openai_usage(response)
    text = _extract_openai_text(response)
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise LLMGenerationError("OpenAI returned invalid structured JSON.") from exc
    if not isinstance(parsed, dict):
        raise LLMGenerationError("OpenAI structured output must be a JSON object.")
    return parsed


def openai_generate_text_from_image(prompt: str, image: bytes, model: str) -> str:
    headers = {
        "Authorization": f"Bearer {get_effective_api_key()}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "input": [
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": prompt},
                    {"type": "input_image", "image_url": _data_url(image), "detail": "auto"},
                ],
            }
        ],
    }
    response = _request_json(url="https://api.openai.com/v1/responses", headers=headers, payload=payload)
    _record_openai_usage(response)
    return _extract_openai_text(response)


def openai_embed_texts(texts: list[str]) -> list[list[float]]:
    headers = {
        "Authorization": f"Bearer {get_effective_api_key()}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": openai_embedding_model(),
        "input": texts,
    }
    response = _request_json(url="https://api.openai.com/v1/embeddings", headers=headers, payload=payload)
    data = response.get("data")
    if not isinstance(data, list):
        raise LLMGenerationError("OpenAI embeddings response did not include vectors.")
    vectors: list[list[float]] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        embedding = item.get("embedding")
        if isinstance(embedding, list) and embedding:
            vectors.append([float(value) for value in embedding])
    if len(vectors) != len(texts):
        raise LLMGenerationError("OpenAI embeddings response count did not match the request.")
    return vectors


def _extract_anthropic_text(payload: dict[str, Any]) -> str:
    content = payload.get("content")
    if not isinstance(content, list):
        raise LLMGenerationError("Anthropic returned an invalid content payload.")

    fragments: list[str] = []
    for block in content:
        if not isinstance(block, dict):
            continue
        text = block.get("text")
        if isinstance(text, str):
            fragments.append(text)

    result = "".join(fragments).strip()
    if not result:
        raise LLMGenerationError("Anthropic returned an empty text response.")
    return result


def anthropic_generate_text(prompt: str, model: str, *, temperature: float | None = None) -> str:
    headers = {
        "x-api-key": get_effective_api_key(),
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    payload: dict[str, Any] = {
        "model": model,
        "max_tokens": 8192,
        "messages": [{"role": "user", "content": prompt}],
    }
    if temperature is not None:
        payload["temperature"] = temperature
    response = _request_json(url="https://api.anthropic.com/v1/messages", headers=headers, payload=payload)
    _record_anthropic_usage(response)
    return _extract_anthropic_text(response)


def anthropic_generate_structured(prompt: str, model: str, schema: dict[str, Any]) -> dict[str, Any]:
    headers = {
        "x-api-key": get_effective_api_key(),
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    payload = {
        "model": model,
        "max_tokens": 8192,
        "messages": [{"role": "user", "content": prompt}],
        "output_config": {
            "format": {
                "type": "json_schema",
                "schema": _normalize_schema(schema),
            }
        },
    }
    response = _request_json(url="https://api.anthropic.com/v1/messages", headers=headers, payload=payload)
    _record_anthropic_usage(response)
    text = _extract_anthropic_text(response)
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise LLMGenerationError("Anthropic returned invalid structured JSON.") from exc
    if not isinstance(parsed, dict):
        raise LLMGenerationError("Anthropic structured output must be a JSON object.")
    return parsed


def anthropic_generate_text_from_image(prompt: str, image: bytes, model: str) -> str:
    headers = {
        "x-api-key": get_effective_api_key(),
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    payload = {
        "model": model,
        "max_tokens": 4096,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": base64.b64encode(image).decode("ascii"),
                        },
                    },
                    {"type": "text", "text": prompt},
                ],
            }
        ],
    }
    response = _request_json(url="https://api.anthropic.com/v1/messages", headers=headers, payload=payload)
    _record_anthropic_usage(response)
    return _extract_anthropic_text(response)


def ollama_generate_text(prompt: str, model: str, *, temperature: float | None = None) -> str:
    payload: dict[str, Any] = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
    }
    if temperature is not None:
        payload["options"] = {"temperature": temperature}
    response = _request_json(
        url=f"{ollama_base_url()}/api/chat",
        headers={"Content-Type": "application/json"},
        payload=payload,
    )
    message = response.get("message")
    if not isinstance(message, dict):
        raise LLMGenerationError("Ollama returned an invalid chat payload.")
    content = message.get("content")
    if not isinstance(content, str) or not content.strip():
        raise LLMGenerationError("Ollama returned an empty text response.")
    return content.strip()


def ollama_generate_structured(prompt: str, model: str, schema: dict[str, Any]) -> dict[str, Any]:
    response = _request_json(
        url=f"{ollama_base_url()}/api/chat",
        headers={"Content-Type": "application/json"},
        payload={
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "format": _normalize_schema(schema),
            "options": {"temperature": 0},
        },
    )
    message = response.get("message")
    if not isinstance(message, dict):
        raise LLMGenerationError("Ollama returned an invalid structured payload.")
    content = message.get("content")
    if not isinstance(content, str) or not content.strip():
        raise LLMGenerationError("Ollama returned an empty structured response.")
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as exc:
        raise LLMGenerationError("Ollama returned invalid structured JSON.") from exc
    if not isinstance(parsed, dict):
        raise LLMGenerationError("Ollama structured output must be a JSON object.")
    return parsed


def ollama_generate_text_from_image(prompt: str, image: bytes, model: str) -> str:
    response = _request_json(
        url=f"{ollama_base_url()}/api/chat",
        headers={"Content-Type": "application/json"},
        payload={
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                    "images": [base64.b64encode(image).decode("ascii")],
                }
            ],
            "stream": False,
        },
    )
    message = response.get("message")
    if not isinstance(message, dict):
        raise LLMGenerationError("Ollama returned an invalid vision payload.")
    content = message.get("content")
    if not isinstance(content, str) or not content.strip():
        raise LLMGenerationError("Ollama returned an empty vision response.")
    return content.strip()


def ollama_embed_texts(texts: list[str], *, selected_model: str | None = None) -> list[list[float]]:
    response = _request_json(
        url=f"{ollama_base_url()}/api/embed",
        headers={"Content-Type": "application/json"},
        payload={
            "model": ollama_embedding_model(selected_model),
            "input": texts,
        },
    )
    embeddings = response.get("embeddings")
    if not isinstance(embeddings, list) or len(embeddings) != len(texts):
        raise LLMGenerationError("Ollama embeddings response did not include the expected vectors.")
    vectors: list[list[float]] = []
    for embedding in embeddings:
        if not isinstance(embedding, list) or not embedding:
            raise LLMGenerationError("Ollama returned an invalid embedding vector.")
        vectors.append([float(value) for value in embedding])
    return vectors


def local_hash_embeddings(texts: list[str], *, dimensions: int = 256) -> list[list[float]]:
    vectors: list[list[float]] = []
    for text in texts:
        values = [0.0] * dimensions
        tokens = [token for token in text.lower().split() if token]
        if not tokens:
            vectors.append(values)
            continue
        for token in tokens:
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=16).digest()
            index = int.from_bytes(digest[:4], "big") % dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            values[index] += sign
        norm = math.sqrt(sum(value * value for value in values)) or 1.0
        vectors.append([value / norm for value in values])
    return vectors
