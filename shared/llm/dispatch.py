from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any

from shared.config import get_effective_model, get_request_provider
from shared.observability.langfuse import trace_llm_call as _trace_llm

from . import gemini_provider
from .catalog import calculate_model_cost, default_model, gemini_embedding_model, infer_provider
from .exceptions import LLMGenerationError
from .providers import (
    anthropic_generate_structured,
    anthropic_generate_text,
    anthropic_generate_text_from_image,
    anthropic_stream_text,
    agnes_generate_structured,
    agnes_generate_text,
    agnes_generate_text_from_image,
    agnes_stream_text,
    local_hash_embeddings,
    ollama_embed_texts,
    ollama_generate_structured,
    ollama_generate_text,
    ollama_generate_text_from_image,
    ollama_stream_text,
    openai_embed_texts,
    openai_generate_structured,
    openai_generate_text,
    openai_generate_text_from_image,
    openai_stream_text,
    xai_generate_structured,
    xai_generate_text,
    xai_generate_text_from_image,
    xai_stream_text,
)
from .telemetry import clear_llm_call_metadata, consume_llm_call_metadata, record_llm_run_call
from .token_events import emit_token


@dataclass
class CompatEmbedding:
    values: list[float]


@dataclass
class CompatEmbedContentResponse:
    embeddings: list[CompatEmbedding]


@dataclass
class CompatGenerateContentResponse:
    text: str | None
    parsed: dict[str, Any] | None = None


def _resolved_model(model: str | None) -> str:
    fallback = model.strip() if isinstance(model, str) and model.strip() else default_model()
    return get_effective_model(fallback)


def _resolved_provider(model: str | None) -> str:
    provider = get_request_provider()
    if provider:
        return provider
    return infer_provider(_resolved_model(model))


def _extract_temperature(config: Any) -> float | None:
    if config is None:
        return None
    value = getattr(config, "temperature", None)
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _extract_schema(config: Any) -> dict[str, Any] | None:
    if config is None:
        return None
    mime_type = getattr(config, "response_mime_type", None) or getattr(config, "responseMimeType", None)
    schema = getattr(config, "response_schema", None) or getattr(config, "responseSchema", None)
    if mime_type != "application/json":
        return None
    if isinstance(schema, dict):
        return schema
    return None


def _requests_audio(config: Any, unsupported_kind: str | None) -> bool:
    if unsupported_kind == "audio":
        return True
    modalities = getattr(config, "response_modalities", None)
    if modalities is None and isinstance(config, dict):
        modalities = config.get("response_modalities") or config.get("responseModalities")
    return isinstance(modalities, (list, tuple)) and any(
        str(modality).upper() == "AUDIO" for modality in modalities
    )


def _normalize_contents(contents: Any) -> tuple[str, bytes | None, str | None]:
    if isinstance(contents, str):
        return contents, None, None

    if not isinstance(contents, list):
        return str(contents), None, None

    text_parts: list[str] = []
    image_bytes: bytes | None = None
    audio_detected = False

    for item in contents:
        if isinstance(item, str):
            text_parts.append(item)
            continue

        inline_data = getattr(item, "inline_data", None)
        if inline_data is not None:
            mime_type = getattr(inline_data, "mime_type", "") or ""
            data = getattr(inline_data, "data", None)
            if isinstance(data, bytes):
                if str(mime_type).startswith("audio/"):
                    audio_detected = True
                elif str(mime_type).startswith("image/"):
                    image_bytes = data
            continue

        if isinstance(item, dict) and isinstance(item.get("text"), str):
            text_parts.append(item["text"])

    prompt = "\n".join(part for part in text_parts if part.strip()).strip()
    if audio_detected:
        return prompt, image_bytes, "audio"
    return prompt, image_bytes, None


def _consume_trace_details() -> tuple[dict[str, int] | None, dict[str, float] | None, dict[str, Any] | None]:
    call_metadata = consume_llm_call_metadata() or {}
    usage_details = call_metadata.get("usage_details")
    cost_details = call_metadata.get("cost_details")
    metadata = {
        key: value for key, value in call_metadata.items()
        if key not in {"usage_details", "cost_details", "metadata"}
    }
    if isinstance(call_metadata.get("metadata"), dict):
        metadata.update(call_metadata["metadata"])

    normalized_usage = usage_details if isinstance(usage_details, dict) else None
    normalized_cost = cost_details if isinstance(cost_details, dict) else None
    normalized_metadata = metadata or None
    return normalized_usage, normalized_cost, normalized_metadata


def _record_run_usage(provider: str, requested_model: str, usage: dict[str, int] | None, metadata: dict[str, Any] | None) -> None:
    if not usage:
        return
    model_used = str((metadata or {}).get("model_used") or requested_model)
    input_tokens = int(usage.get("input") or usage.get("input_tokens") or usage.get("prompt_tokens") or 0)
    output_tokens = int(usage.get("output") or usage.get("output_tokens") or usage.get("completion_tokens") or 0)
    cached_input_tokens = int(usage.get("input_cached_tokens") or usage.get("input_cache_read_tokens") or 0)
    cost_breakdown = calculate_model_cost(
        model_used,
        input_tokens,
        output_tokens,
        cached_input_tokens=cached_input_tokens,
    )
    record_llm_run_call({
        "provider": provider,
        "model_requested": requested_model,
        "model_used": model_used,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
        "estimated_cost_usd": cost_breakdown["estimated_cost_usd"] if cost_breakdown else None,
        "cost_breakdown": cost_breakdown,
    })


def generate_text(prompt: str, model: str, *, temperature: float | None = None) -> str:
    resolved_model = _resolved_model(model)
    provider = _resolved_provider(resolved_model)
    clear_llm_call_metadata()
    _start = time.perf_counter()
    if provider == "gemini":
        result = gemini_provider.generate_text(prompt=prompt, model=resolved_model)
    elif provider == "openai":
        result = openai_generate_text(prompt=prompt, model=resolved_model, temperature=temperature)
    elif provider == "anthropic":
        result = anthropic_generate_text(prompt=prompt, model=resolved_model, temperature=temperature)
    elif provider == "xai":
        result = xai_generate_text(prompt=prompt, model=resolved_model, temperature=temperature)
    elif provider == "agnes":
        result = agnes_generate_text(prompt=prompt, model=resolved_model, temperature=temperature)
    else:
        result = ollama_generate_text(prompt=prompt, model=resolved_model, temperature=temperature)
    _elapsed = (time.perf_counter() - _start) * 1000
    _usage, _cost, _metadata = _consume_trace_details()
    _record_run_usage(provider, resolved_model, _usage, _metadata)
    _trace_llm(
        name="generate_text",
        model=resolved_model,
        input=prompt[:500],
        output=result[:500],
        usage=_usage,
        cost_details=_cost,
        latency_ms=_elapsed,
        metadata={"provider": provider, **(_metadata or {})},
    )
    return result


def generate_text_streaming(prompt: str, model: str) -> str:
    """Use provider-native streaming for a user-visible final text stage."""
    resolved_model = _resolved_model(model)
    provider = _resolved_provider(resolved_model)
    clear_llm_call_metadata()
    start = time.perf_counter()
    if provider == "gemini":
        result = gemini_provider.stream_text(prompt, resolved_model, emit_token)
    elif provider == "openai":
        result = openai_stream_text(prompt, resolved_model, emit_token)
    elif provider == "anthropic":
        result = anthropic_stream_text(prompt, resolved_model, emit_token)
    elif provider == "xai":
        result = xai_stream_text(prompt, resolved_model, emit_token)
    elif provider == "agnes":
        result = agnes_stream_text(prompt, resolved_model, emit_token)
    else:
        result = ollama_stream_text(prompt, resolved_model, emit_token)
    elapsed = (time.perf_counter() - start) * 1000
    usage, cost, metadata = _consume_trace_details()
    _record_run_usage(provider, resolved_model, usage, metadata)
    _trace_llm(
        name="generate_text_streaming", model=resolved_model, input=prompt[:500], output=result[:500],
        usage=usage, cost_details=cost, latency_ms=elapsed,
        metadata={"provider": provider, "native_stream": True, **(metadata or {})},
    )
    return result


def generate_structured(prompt: str, model: str, schema: dict[str, Any]) -> dict[str, Any]:
    resolved_model = _resolved_model(model)
    provider = _resolved_provider(resolved_model)
    clear_llm_call_metadata()
    _start = time.perf_counter()
    if provider == "gemini":
        result = gemini_provider.generate_structured(prompt=prompt, model=resolved_model, schema=schema)
    elif provider == "openai":
        result = openai_generate_structured(prompt=prompt, model=resolved_model, schema=schema)
    elif provider == "anthropic":
        result = anthropic_generate_structured(prompt=prompt, model=resolved_model, schema=schema)
    elif provider == "xai":
        result = xai_generate_structured(prompt=prompt, model=resolved_model, schema=schema)
    elif provider == "agnes":
        result = agnes_generate_structured(prompt=prompt, model=resolved_model, schema=schema)
    else:
        result = ollama_generate_structured(prompt=prompt, model=resolved_model, schema=schema)
    _elapsed = (time.perf_counter() - _start) * 1000
    _usage, _cost, _metadata = _consume_trace_details()
    _record_run_usage(provider, resolved_model, _usage, _metadata)
    _trace_llm(
        name="generate_structured",
        model=resolved_model,
        input=prompt[:500],
        output=str(result)[:500],
        usage=_usage,
        cost_details=_cost,
        latency_ms=_elapsed,
        metadata={"provider": provider, "schema": str(schema)[:200], **(_metadata or {})},
    )
    return result


def generate_text_from_image(prompt: str, image: bytes, model: str) -> str:
    resolved_model = _resolved_model(model)
    provider = _resolved_provider(resolved_model)
    clear_llm_call_metadata()
    _start = time.perf_counter()
    if provider == "gemini":
        result = gemini_provider.generate_text_from_image(prompt=prompt, image=image, model=resolved_model)
    elif provider == "openai":
        result = openai_generate_text_from_image(prompt=prompt, image=image, model=resolved_model)
    elif provider == "anthropic":
        result = anthropic_generate_text_from_image(prompt=prompt, image=image, model=resolved_model)
    elif provider == "xai":
        result = xai_generate_text_from_image(prompt=prompt, image=image, model=resolved_model)
    elif provider == "agnes":
        result = agnes_generate_text_from_image(prompt=prompt, image=image, model=resolved_model)
    else:
        result = ollama_generate_text_from_image(prompt=prompt, image=image, model=resolved_model)
    _elapsed = (time.perf_counter() - _start) * 1000
    _usage, _cost, _metadata = _consume_trace_details()
    _record_run_usage(provider, resolved_model, _usage, _metadata)
    _trace_llm(
        name="generate_text_from_image",
        model=resolved_model,
        input=prompt[:500],
        output=result[:500],
        usage=_usage,
        cost_details=_cost,
        latency_ms=_elapsed,
        metadata={"provider": provider, "image_bytes": len(image), **(_metadata or {})},
    )
    return result


def generate_embeddings(texts: list[str], *, model: str | None = None) -> list[list[float]]:
    resolved_model = _resolved_model(model)
    provider = _resolved_provider(resolved_model)
    if provider == "gemini":
        response = gemini_provider._get_client().models.embed_content(
            model=gemini_embedding_model(),
            contents=texts,
        )
        return [list(item.values or []) for item in response.embeddings]
    if provider == "openai":
        return openai_embed_texts(texts)
    if provider in {"anthropic", "xai", "agnes"}:
        return local_hash_embeddings(texts)
    try:
        return ollama_embed_texts(texts, selected_model=resolved_model)
    except Exception:
        return local_hash_embeddings(texts)


class _CompatModels:
    def generate_content(self, *, model: str, contents: Any, config: Any = None) -> CompatGenerateContentResponse:
        resolved_model = _resolved_model(model)
        provider = _resolved_provider(resolved_model)
        prompt, image, unsupported_kind = _normalize_contents(contents)
        if provider == "gemini" and _requests_audio(config, unsupported_kind):
            return gemini_provider._get_client().models.generate_content(
                model=resolved_model,
                contents=contents,
                config=config,
            )
        if unsupported_kind == "audio":
            raise LLMGenerationError("The selected provider does not support Gemini audio generation APIs.")

        schema = _extract_schema(config)
        if image is not None:
            text = generate_text_from_image(prompt=prompt, image=image, model=resolved_model)
            return CompatGenerateContentResponse(text=text)
        if schema is not None:
            parsed = generate_structured(prompt=prompt, model=resolved_model, schema=schema)
            return CompatGenerateContentResponse(text=json.dumps(parsed), parsed=parsed)

        text = generate_text(prompt=prompt, model=resolved_model, temperature=_extract_temperature(config))
        return CompatGenerateContentResponse(text=text)

    def embed_content(self, *, model: str, contents: Any, config: Any = None) -> CompatEmbedContentResponse:
        resolved_model = _resolved_model(model)
        provider = _resolved_provider(resolved_model)
        if provider == "gemini":
            return gemini_provider._get_client().models.embed_content(model=model, contents=contents, config=config)

        if isinstance(contents, str):
            texts = [contents]
        elif isinstance(contents, list):
            texts = [str(item) for item in contents]
        else:
            texts = [str(contents)]

        vectors = generate_embeddings(texts, model=resolved_model)
        return CompatEmbedContentResponse(embeddings=[CompatEmbedding(values=vector) for vector in vectors])


class CompatClient:
    def __init__(self) -> None:
        self.models = _CompatModels()


def get_client_adapter() -> Any:
    return CompatClient()
