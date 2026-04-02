from __future__ import annotations

from typing import Any

from .dispatch import generate_structured as _dispatch_generate_structured
from .dispatch import generate_text as _dispatch_generate_text
from .dispatch import generate_text_from_image as _dispatch_generate_text_from_image
from .dispatch import get_client_adapter
from .exceptions import GeminiGenerationError, GeminiTimeoutError


def _get_client() -> Any:
    return get_client_adapter()


def generate_text(prompt: str, model: str) -> str:
    return _dispatch_generate_text(prompt=prompt, model=model)


def generate_structured(prompt: str, model: str, schema: dict[str, Any]) -> dict[str, Any]:
    return _dispatch_generate_structured(prompt=prompt, model=model, schema=schema)


def generate_text_from_image(prompt: str, image: bytes, model: str) -> str:
    return _dispatch_generate_text_from_image(prompt=prompt, image=image, model=model)


__all__ = [
    "_get_client",
    "generate_text",
    "generate_structured",
    "generate_text_from_image",
    "GeminiGenerationError",
    "GeminiTimeoutError",
]