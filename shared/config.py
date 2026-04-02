from __future__ import annotations

import json
import os
from contextvars import ContextVar, Token
from functools import lru_cache
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

# ── Request-scoped runtime context ────────────────────────────

_BYOK_API_KEY: ContextVar[str | None] = ContextVar("byok_api_key", default=None)
_REQUEST_MODEL: ContextVar[str | None] = ContextVar("request_model", default=None)
_REQUEST_PROVIDER: ContextVar[str | None] = ContextVar("request_provider", default=None)


def set_byok_api_key(key: str | None) -> Token[str | None]:
    """Bind a per-request Google API key for the current execution context."""
    return _BYOK_API_KEY.set(key)


def reset_byok_api_key(token: Token[str | None]) -> None:
    """Restore the previous BYOK binding."""
    _BYOK_API_KEY.reset(token)


def set_request_model(model: str | None) -> Token[str | None]:
    """Bind a request-scoped model override for the current execution context."""
    return _REQUEST_MODEL.set((model or "").strip() or None)


def reset_request_model(token: Token[str | None]) -> None:
    """Restore the previous request-model binding."""
    _REQUEST_MODEL.reset(token)


def get_request_model() -> str | None:
    """Return the request-scoped model override, if present."""
    return _REQUEST_MODEL.get()


def set_request_provider(provider: str | None) -> Token[str | None]:
    """Bind a request-scoped provider override for the current execution context."""
    return _REQUEST_PROVIDER.set((provider or "").strip().lower() or None)


def reset_request_provider(token: Token[str | None]) -> None:
    """Restore the previous request-provider binding."""
    _REQUEST_PROVIDER.reset(token)


def get_request_provider() -> str | None:
    """Return the request-scoped provider override, if present."""
    return _REQUEST_PROVIDER.get()


def get_effective_api_key(*, required: bool = True) -> str:
    """Return the per-request BYOK key from the ``x-api-key`` header.

    Raises ``RuntimeError`` when no key was provided for this request.
    """
    byok = _BYOK_API_KEY.get()
    if byok:
        return byok
    if not required:
        return ""
    raise RuntimeError(
        "No API key available. "
        "Provide one via the x-api-key request header."
    )


def get_effective_model(fallback_model: str) -> str:
    """Return the request-scoped model override, or the provided fallback."""
    request_model = _REQUEST_MODEL.get()
    if request_model:
        return request_model
    return fallback_model.strip()


ROOT_ENV_FILE = Path(__file__).resolve().parents[1] / ".env"


load_dotenv(dotenv_path=ROOT_ENV_FILE)


DEFAULT_DEV_MODEL = "gemini-3-flash-preview"
DEFAULT_PROD_MODEL = "gemini-3.1-pro-preview"


class Settings(BaseModel):
    model_config = ConfigDict(frozen=True)

    environment: Literal["dev", "prod"] = "dev"
    default_model_dev: str = DEFAULT_DEV_MODEL
    default_model_prod: str = DEFAULT_PROD_MODEL
    project_models: dict[str, str] = Field(default_factory=dict)

    @field_validator("environment", mode="before")
    @classmethod
    def normalize_environment(cls, value: str | None) -> str:
        normalized = (value or "dev").strip().lower()
        if normalized not in {"dev", "prod"}:
            raise ValueError("APP_ENV must be either 'dev' or 'prod'.")
        return normalized

    @field_validator("default_model_dev", "default_model_prod")
    @classmethod
    def validate_default_model(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("Default model values must not be empty.")
        return value.strip()

    @field_validator("project_models", mode="before")
    @classmethod
    def parse_project_models(cls, value: object) -> dict[str, str]:
        if value in (None, ""):
            return {}
        if isinstance(value, str):
            parsed = json.loads(value)
        else:
            parsed = value

        if not isinstance(parsed, dict):
            raise ValueError("PROJECT_MODELS_JSON must decode to an object mapping project names to models.")

        models: dict[str, str] = {}
        for project_name, model_name in parsed.items():
            if not isinstance(project_name, str) or not isinstance(model_name, str):
                raise ValueError("PROJECT_MODELS_JSON must contain only string keys and string values.")
            models[_normalize_project_name(project_name)] = model_name.strip()
        return models

    def default_model(self, environment: str | None = None) -> str:
        target = (environment or self.environment).strip().lower()
        if target == "prod":
            return self.default_model_prod
        return self.default_model_dev


def _normalize_project_name(project_name: str) -> str:
    normalized = project_name.strip().lower().replace("_", "-").replace(" ", "-")
    while "--" in normalized:
        normalized = normalized.replace("--", "-")
    return normalized


def _project_env_key(project_name: str) -> str:
    normalized = _normalize_project_name(project_name)
    characters: list[str] = []
    for char in normalized:
        if char.isalnum():
            characters.append(char.upper())
        else:
            characters.append("_")
    return "".join(characters)


def _read_project_model_override(project_name: str, environment: str) -> str | None:
    project_key = _project_env_key(project_name)
    candidates = (
        f"MODEL_{environment.upper()}_{project_key}",
        f"MODEL_{project_key}",
    )
    for env_var in candidates:
        value = os.getenv(env_var, "").strip()
        if value:
            return value
    return None


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    try:
        return Settings(
            environment=os.getenv("APP_ENV", "dev"),
            default_model_dev=os.getenv("MODEL_DEFAULT_DEV", DEFAULT_DEV_MODEL),
            default_model_prod=os.getenv("MODEL_DEFAULT_PROD", DEFAULT_PROD_MODEL),
            project_models=os.getenv("PROJECT_MODELS_JSON", "{}"),
        )
    except ValidationError as exc:
        raise RuntimeError("Invalid application configuration.") from exc


def get_environment() -> str:
    return get_settings().environment


def get_model(project_name: str, *, environment: str | None = None) -> str:
    request_model = get_request_model()
    if request_model:
        return request_model

    settings = get_settings()
    target_environment = (environment or settings.environment).strip().lower()
    normalized_project = _normalize_project_name(project_name)

    env_override = _read_project_model_override(normalized_project, target_environment)
    if env_override:
        return env_override

    configured_model = settings.project_models.get(normalized_project)
    if configured_model:
        return configured_model

    return settings.default_model(target_environment)