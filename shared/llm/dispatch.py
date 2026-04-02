from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from shared.config import get_effective_model, get_request_provider

from . import gemini_provider
from .catalog import default_model, gemini_embedding_model, infer_provider
from .exceptions import LLMGenerationError
from .providers import (
    anthropic_generate_structured,
    anthropic_generate_text,
    anthropic_generate_text_from_image,
    local_hash_embeddings,
    ollama_embed_texts,
    ollama_generate_structured,
    ollama_generate_text,
    ollama_generate_text_from_image,
    openai_embed_texts,
    openai_generate_structured,
    openai_generate_text,
    openai_generate_text_from_image,
)


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


def generate_text(prompt: str, model: str, *, temperature: float | None = None) -> str:
    resolved_model = _resolved_model(model)
    provider = _resolved_provider(resolved_model)
    if provider == "gemini":
        return gemini_provider.generate_text(prompt=prompt, model=resolved_model)
    if provider == "openai":
        return openai_generate_text(prompt=prompt, model=resolved_model, temperature=temperature)
    if provider == "anthropic":
        return anthropic_generate_text(prompt=prompt, model=resolved_model, temperature=temperature)
    return ollama_generate_text(prompt=prompt, model=resolved_model, temperature=temperature)


def generate_structured(prompt: str, model: str, schema: dict[str, Any]) -> dict[str, Any]:
    resolved_model = _resolved_model(model)
    provider = _resolved_provider(resolved_model)
    if provider == "gemini":
        return gemini_provider.generate_structured(prompt=prompt, model=resolved_model, schema=schema)
    if provider == "openai":
        return openai_generate_structured(prompt=prompt, model=resolved_model, schema=schema)
    if provider == "anthropic":
        return anthropic_generate_structured(prompt=prompt, model=resolved_model, schema=schema)
    return ollama_generate_structured(prompt=prompt, model=resolved_model, schema=schema)


def generate_text_from_image(prompt: str, image: bytes, model: str) -> str:
    resolved_model = _resolved_model(model)
    provider = _resolved_provider(resolved_model)
    if provider == "gemini":
        return gemini_provider.generate_text_from_image(prompt=prompt, image=image, model=resolved_model)
    if provider == "openai":
        return openai_generate_text_from_image(prompt=prompt, image=image, model=resolved_model)
    if provider == "anthropic":
        return anthropic_generate_text_from_image(prompt=prompt, image=image, model=resolved_model)
    return ollama_generate_text_from_image(prompt=prompt, image=image, model=resolved_model)


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
    if provider == "anthropic":
        return local_hash_embeddings(texts)
    try:
        return ollama_embed_texts(texts, selected_model=resolved_model)
    except Exception:
        return local_hash_embeddings(texts)


class _CompatModels:
    def generate_content(self, *, model: str, contents: Any, config: Any = None) -> CompatGenerateContentResponse:
        resolved_model = _resolved_model(model)
        provider = _resolved_provider(resolved_model)
        if provider == "gemini":
            return gemini_provider._get_client().models.generate_content(model=resolved_model, contents=contents, config=config)

        prompt, image, unsupported_kind = _normalize_contents(contents)
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
    resolved_provider = _resolved_provider(None)
    if resolved_provider == "gemini":
        return gemini_provider._get_client()
    return CompatClient()
