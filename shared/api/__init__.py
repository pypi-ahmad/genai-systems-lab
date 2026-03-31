"""Shared FastAPI application factory and utilities.

Exports are resolved lazily so importing ``shared.api.runner`` does not
eagerly initialize the FastAPI app and database.
"""

from __future__ import annotations

__all__ = ["create_app", "get_settings_dep", "get_llm_client_dep", "get_logger_dep"]


def __getattr__(name: str):
	if name == "create_app":
		from .app import create_app

		return create_app
	if name == "get_settings_dep":
		from .dependencies import get_settings_dep

		return get_settings_dep
	if name == "get_llm_client_dep":
		from .dependencies import get_llm_client_dep

		return get_llm_client_dep
	if name == "get_logger_dep":
		from .dependencies import get_logger_dep

		return get_logger_dep
	raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
