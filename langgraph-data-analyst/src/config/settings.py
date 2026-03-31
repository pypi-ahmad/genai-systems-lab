"""Application configuration and structured logging setup.

All settings are loaded from environment variables (or a ``.env`` file) using
*python-dotenv* and *pydantic* ``BaseSettings``.  A module-level ``settings``
singleton is exported for convenient import across the codebase.
"""

import logging
import sys
from pathlib import Path

from dotenv import load_dotenv
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()

# ── Model constants ──────────────────────────────────────────────────────
MODEL_FAST = "gemini-3-flash-preview"
MODEL_PRO = "gemini-3.1-pro-preview"


class Settings(BaseSettings):
    """Centralised application settings.

    Values are read from environment variables and, optionally, from a
    ``.env`` file in the project root.  Field names are **case-insensitive**
    when matched against env-var names.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── LLM ──────────────────────────────────────────
    model_fast: str = MODEL_FAST
    model_pro: str = MODEL_PRO
    temperature: float = 0.0

    # ── Execution sandbox ────────────────────────────
    code_execution_timeout_seconds: int = 30
    max_retries: int = 3

    # ── Storage ──────────────────────────────────────
    upload_dir: Path = Path("uploads")
    output_dir: Path = Path("outputs")
    max_upload_size_mb: int = 100

    # ── API ──────────────────────────────────────────
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # ── Logging ──────────────────────────────────────
    log_level: str = "INFO"
    log_format: str = (
        "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s"
    )

settings = Settings()


def setup_logging() -> None:
    """Configure application-wide logging with a structured formatter.

    Idempotent — safe to call multiple times.  Noisy third-party loggers
    are silenced to ``WARNING``.
    """
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    root = logging.getLogger()
    root.setLevel(level)

    if not root.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        handler.setFormatter(logging.Formatter(settings.log_format))
        root.addHandler(handler)

    for name in ("httpcore", "httpx", "urllib3"):
        logging.getLogger(name).setLevel(logging.WARNING)


def ensure_directories() -> None:
    """Create the upload and output directories if they don't yet exist."""
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    settings.output_dir.mkdir(parents=True, exist_ok=True)
