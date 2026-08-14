from __future__ import annotations

import json
import os
from typing import Any, Literal, NotRequired, TypedDict, cast
from urllib.parse import urlparse

import httpx

ProviderId = Literal["gemini", "openai", "anthropic", "xai", "ollama"]


class PricingSpec(TypedDict):
    input_per_million_usd: float
    output_per_million_usd: float
    as_of: str
    details: str
    cached_input_per_million_usd: NotRequired[float]
    batch_input_per_million_usd: NotRequired[float]
    batch_output_per_million_usd: NotRequired[float]
    long_context_threshold_tokens: NotRequired[int]
    long_context_input_per_million_usd: NotRequired[float]
    long_context_output_per_million_usd: NotRequired[float]
    fast_input_per_million_usd: NotRequired[float]
    fast_output_per_million_usd: NotRequired[float]
    promotion_ends_on: NotRequired[str]


class ModelSpec(TypedDict):
    id: str
    label: str
    provider: ProviderId
    effort_options: list[str]
    pricing: PricingSpec | None


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
            {
                "id": "gemini-3.7-flash",
                "label": "Gemini Flash 3.7",
                "provider": "gemini",
                "effort_options": ["low", "medium", "high"],
                "pricing": {
                    "input_per_million_usd": 0.75,
                    "output_per_million_usd": 3.75,
                    "as_of": "2026-08-14",
                    "promotion_ends_on": "2026-12-31",
                    "details": "Promotional rate through December 31, 2026.",
                },
            },
            {
                "id": "gemini-3.5-flash-lite",
                "label": "Gemini 3.5 Flash Lite",
                "provider": "gemini",
                "effort_options": ["minimal", "low", "medium", "high"],
                "pricing": {
                    "input_per_million_usd": 0.30,
                    "output_per_million_usd": 2.50,
                    "batch_input_per_million_usd": 0.15,
                    "batch_output_per_million_usd": 1.25,
                    "as_of": "2026-08-14",
                    "details": "Batch processing is $0.15 input / $1.25 output per 1M tokens.",
                },
            },
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
            {
                "id": "gpt-5.6-luna",
                "label": "GPT-5.6 Luna",
                "provider": "openai",
                "effort_options": ["none", "low", "medium", "high", "xhigh", "max"],
                "pricing": {
                    "input_per_million_usd": 0.20,
                    "cached_input_per_million_usd": 0.02,
                    "output_per_million_usd": 1.20,
                    "as_of": "2026-08-14",
                    "details": "Cached prompt reads cost $0.02 per 1M tokens.",
                },
            },
            {
                "id": "gpt-5.6-terra",
                "label": "GPT-5.6 Terra",
                "provider": "openai",
                "effort_options": ["none", "low", "medium", "high", "xhigh", "max"],
                "pricing": {
                    "input_per_million_usd": 2.00,
                    "output_per_million_usd": 12.00,
                    "long_context_threshold_tokens": 272_000,
                    "long_context_input_per_million_usd": 4.00,
                    "long_context_output_per_million_usd": 24.00,
                    "as_of": "2026-08-14",
                    "details": "Requests above 272k input tokens use the $4 input / $24 output long-context rate.",
                },
            },
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
            {
                "id": "claude-sonnet-5",
                "label": "Claude Sonnet 5",
                "provider": "anthropic",
                "effort_options": ["low", "medium", "high", "xhigh", "max"],
                "pricing": {
                    "input_per_million_usd": 2.00,
                    "output_per_million_usd": 10.00,
                    "batch_input_per_million_usd": 1.00,
                    "batch_output_per_million_usd": 5.00,
                    "as_of": "2026-08-14",
                    "details": "The Batch API provides a 50% discount ($1 input / $5 output per 1M tokens).",
                },
            },
        ],
    },
    {
        "id": "xai",
        "label": "xAI",
        "requires_api_key": True,
        "api_key_label": "xAI API key",
        "api_key_help_url": "https://console.x.ai/",
        "api_key_placeholder": "xai-...",
        "models": [
            {
                "id": "grok-4.6",
                "label": "Grok 4.6",
                "provider": "xai",
                "effort_options": [],
                "pricing": {
                    "input_per_million_usd": 2.00,
                    "output_per_million_usd": 6.00,
                    "long_context_threshold_tokens": 200_000,
                    "long_context_input_per_million_usd": 4.00,
                    "long_context_output_per_million_usd": 12.00,
                    "fast_input_per_million_usd": 4.00,
                    "fast_output_per_million_usd": 12.00,
                    "as_of": "2026-08-14",
                    "details": "Fast mode or requests above 200k input tokens cost $4 input / $12 output per 1M tokens.",
                },
            },
        ],
    },
)

STATIC_MODEL_SPECS: dict[str, ModelSpec] = {
    model["id"]: model
    for provider in STATIC_PROVIDERS
    for model in provider["models"]
}


def default_model() -> str:
    return "gemini-3.7-flash"


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
    if lowered.startswith("grok"):
        return "xai"
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
        "effort_options": [],
        "pricing": None,
    }


def validate_model_effort(model: str, effort: str | None) -> str | None:
    normalized = (effort or "").strip().lower()
    if not normalized or normalized == "default":
        return None
    options = get_model_spec(model).get("effort_options", [])
    if normalized not in options:
        allowed = ", ".join(options) if options else "provider default only"
        raise ValueError(f"Unsupported effort '{normalized}' for model '{model}'. Expected: {allowed}.")
    return normalized


def calculate_model_cost(
    model: str,
    input_tokens: int,
    output_tokens: int,
    *,
    cached_input_tokens: int = 0,
) -> dict[str, Any] | None:
    pricing = get_model_spec(model).get("pricing")
    if not pricing:
        return None

    input_count = max(0, int(input_tokens))
    output_count = max(0, int(output_tokens))
    cached_count = min(input_count, max(0, int(cached_input_tokens)))
    threshold = int(pricing.get("long_context_threshold_tokens", 0))
    long_context = bool(threshold and input_count > threshold)
    input_rate = float(
        pricing["long_context_input_per_million_usd"]
        if long_context
        else pricing["input_per_million_usd"]
    )
    output_rate = float(
        pricing["long_context_output_per_million_usd"]
        if long_context
        else pricing["output_per_million_usd"]
    )
    cached_rate_value = pricing.get("cached_input_per_million_usd") if not long_context else None
    cached_rate = float(cached_rate_value) if cached_rate_value is not None else None
    uncached_count = input_count - cached_count if cached_rate is not None else input_count
    billable_cached_count = cached_count if cached_rate is not None else 0
    input_cost = (
        uncached_count * input_rate
        + billable_cached_count * (cached_rate or 0.0)
    ) / 1_000_000
    output_cost = output_count * output_rate / 1_000_000
    total_cost = input_cost + output_cost

    return {
        "model": model,
        "pricing_tier": "long_context" if long_context else "standard",
        "input_tokens": input_count,
        "cached_input_tokens": billable_cached_count,
        "output_tokens": output_count,
        "input_rate_per_million_usd": input_rate,
        "cached_input_rate_per_million_usd": cached_rate,
        "output_rate_per_million_usd": output_rate,
        "input_cost_usd": round(input_cost, 8),
        "output_cost_usd": round(output_cost, 8),
        "estimated_cost_usd": round(total_cost, 8),
    }


def estimate_model_cost(
    model: str,
    input_tokens: int,
    output_tokens: int,
    *,
    cached_input_tokens: int = 0,
) -> float | None:
    breakdown = calculate_model_cost(
        model,
        input_tokens,
        output_tokens,
        cached_input_tokens=cached_input_tokens,
    )
    return None if breakdown is None else float(breakdown["estimated_cost_usd"])


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
            "effort_options": [],
            "pricing": None,
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
