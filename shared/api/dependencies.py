"""FastAPI dependency providers for shared services."""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any

from shared.config import Settings, get_settings
from shared.llm.gemini import _get_client
from shared.logging import get_logger


def get_settings_dep() -> Settings:
    """FastAPI dependency that loads and returns the shared settings singleton."""
    return get_settings()


def get_llm_client_dep() -> Any:
    """FastAPI dependency that returns a cached Gemini client for the per-request API key."""
    return _get_client()


@lru_cache(maxsize=None)
def _logger(name: str) -> logging.Logger:
    return get_logger(name)


def get_logger_dep(name: str = "shared.api") -> logging.Logger:
    """FastAPI dependency that returns a named shared logger instance."""
    return _logger(name)
