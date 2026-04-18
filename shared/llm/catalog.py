from __future__ import annotations

import json
import os
from typing import Any, Literal, TypedDict, cast
import httpx
from urllib.parse import urlparse


ProviderId = Literal["gemini", "openai", "anthropic", "ollama"]


class ModelSpec(TypedDict):
    id: str
    label: str
    provider: ProviderId


class ProviderSpec(TypedDict, total=False):
    id: ProviderId
    label: str
    requires_api_key: bool
    api_key_label: str
    api_key_help_url: str | None
    api_key_placeholder: str
    available: bool
    unavailable_reason: str | None
    models: list[ModelSpec]


STATIC_PROVIDERS: tuple[ProviderSpec, ...] = (
    {
        "id": "gemini",
        "label": "Google Gemini",
        "requires_api_key": True,
        "api_key_label": "Google API key",
        "api_key_help_url": "https://aistudio.google.com/apikey",
        "api_key_placeholder": "AIza...",
        "models": [
            {"id": "gemini-3-flash-preview", "label": "Gemini 3 Flash Preview", "provider": "gemini"},
            {"id": "gemini-3.1-pro-preview", "label": "Gemini 3.1 Pro Preview", "provider": "gemini"},
        ],
    },
    {
        "id": "openai",
        "label": "OpenAI",
        "requires_api_key": True,
        "api_key_label": "OpenAI API key",
        "api_key_help_url": "https://platform.openai.com/api-keys",
        "api_key_placeholder": "sk-...",
        "models": [
            {"id": "gpt-5.4", "label": "GPT-5.4", "provider": "openai"},
            {"id": "gpt-5.4-mini", "label": "GPT-5.4 mini", "provider": "openai"},
        ],
    },
    {
        "id": "anthropic",
        "label": "Anthropic Claude",
        "requires_api_key": True,
        "api_key_label": "Anthropic API key",
        "api_key_help_url": "https://console.anthropic.com/settings/keys",
        "api_key_placeholder": "sk-ant-...",
        "models": [
            {"id": "claude-sonnet-4-6", "label": "Claude Sonnet 4.6", "provider": "anthropic"},
            {"id": "claude-opus-4-6", "label": "Claude Opus 4.6", "provider": "anthropic"},
        ],
    },
)

STATIC_MODEL_SPECS: dict[str, ModelSpec] = {
    model["id"]: model
    for provider in STATIC_PROVIDERS
    for model in provider["models"]
}


def default_model() -> str:
    return "gemini-3-flash-preview"


def ollama_base_url() -> str:
    raw = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").strip()
    return raw.rstrip("/") or "http://127.0.0.1:11434"


def _validated_ollama_tags_url() -> str:
    url = f"{ollama_base_url()}/api/tags"
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError(f"Invalid Ollama URL scheme: {parsed.scheme!r}")
    if not parsed.netloc:
        raise ValueError("OLLAMA_BASE_URL is missing a host.")
    return url


def openai_embedding_model() -> str:
    return os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small").strip() or "text-embedding-3-small"


def gemini_embedding_model() -> str:
    return os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-2-preview").strip() or "gemini-embedding-2-preview"


def ollama_embedding_model(selected_model: str | None = None) -> str:
    configured = os.getenv("OLLAMA_EMBEDDING_MODEL", "").strip()
    if configured:
        return configured
    if selected_model and selected_model.startswith("embedding"):
        return selected_model
    return "embeddinggemma"


def infer_provider(model: str | None) -> ProviderId:
    model_name = (model or "").strip()
    if not model_name:
        return cast(ProviderId, STATIC_MODEL_SPECS[default_model()]["provider"])
    static_match = STATIC_MODEL_SPECS.get(model_name)
    if static_match is not None:
        return cast(ProviderId, static_match["provider"])
    lowered = model_name.lower()
    if lowered.startswith("gemini"):
        return "gemini"
    if lowered.startswith("gpt") or lowered.startswith("o1") or lowered.startswith("o3"):
        return "openai"
    if lowered.startswith("claude"):
        return "anthropic"
    return "ollama"


def get_model_spec(model: str | None) -> ModelSpec:
    model_name = (model or default_model()).strip() or default_model()
    static_match = STATIC_MODEL_SPECS.get(model_name)
    if static_match is not None:
        return static_match
    return {
        "id": model_name,
        "label": model_name,
        "provider": "ollama",
    }


def provider_requires_api_key(provider: ProviderId) -> bool:
    return provider != "ollama"


def _fetch_ollama_tags(timeout_seconds: float = 1.0) -> dict[str, Any]:
    url = _validated_ollama_tags_url()
    response = httpx.get(url, timeout=timeout_seconds, follow_redirects=False)
    response.raise_for_status()
    payload = response.text
    parsed = json.loads(payload)
    if not isinstance(parsed, dict):
        raise ValueError("Invalid Ollama tags payload.")
    return parsed


def list_ollama_models(timeout_seconds: float = 1.0) -> tuple[list[ModelSpec], str | None]:
    try:
        payload = _fetch_ollama_tags(timeout_seconds=timeout_seconds)
    except httpx.HTTPError:
        reason = (
            f"Unable to reach Ollama at {ollama_base_url()}. "
            "Local Ollama only works when the backend can reach that host."
        )
        return [], reason
    except Exception as exc:
        return [], f"Unable to load Ollama models: {exc}"

    models = payload.get("models")
    if not isinstance(models, list):
        return [], "Ollama returned an unexpected model catalog payload."

    discovered: list[ModelSpec] = []
    for item in models:
        if not isinstance(item, dict):
            continue
        name = str(item.get("model") or item.get("name") or "").strip()
        if not name:
            continue
        discovered.append({
            "id": name,
            "label": name,
            "provider": "ollama",
        })

    discovered.sort(key=lambda model: model["label"].lower())
    if not discovered:
        return [], "Ollama is reachable, but no local models are installed."
    return discovered, None


def build_provider_catalog() -> dict[str, Any]:
    providers: list[ProviderSpec] = [
        {
            **provider,
            "available": True,
            "unavailable_reason": None,
            "models": list(provider["models"]),
        }
        for provider in STATIC_PROVIDERS
    ]

    ollama_models, ollama_error = list_ollama_models()
    providers.append(
        {
            "id": "ollama",
            "label": "Local Ollama",
            "requires_api_key": False,
            "api_key_label": "No API key required",
            "api_key_help_url": "https://ollama.com/download",
            "api_key_placeholder": "",
            "available": ollama_error is None,
            "unavailable_reason": ollama_error,
            "models": ollama_models,
        }
    )

    return {
        "default_model": default_model(),
        "providers": providers,
    }
