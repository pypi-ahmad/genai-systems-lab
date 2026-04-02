"""Database configuration for shared API persistence."""

from __future__ import annotations

from collections.abc import Generator
import os
from pathlib import Path
import warnings

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _resolve_data_dir() -> Path:
    """Return a writable directory for the SQLite database.

    On read-only filesystems (e.g. Vercel serverless) fall back to ``/tmp``.
    """
    primary = REPO_ROOT / ".data"
    try:
        primary.mkdir(parents=True, exist_ok=True)
        return primary
    except OSError:
        fallback = Path("/tmp/.data")
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback


DATA_DIR = _resolve_data_dir()
DEFAULT_SQLITE_DATABASE_URL = f"sqlite:///{(DATA_DIR / 'genai_systems_lab.db').as_posix()}"
DATABASE_URL = (
    os.getenv("GENAI_SYSTEMS_LAB_DATABASE_URL")
    or os.getenv("DATABASE_URL")
    or DEFAULT_SQLITE_DATABASE_URL
).strip()
IS_SQLITE = DATABASE_URL.startswith("sqlite")


class Base(DeclarativeBase):
    """Base class for ORM models."""


engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if IS_SQLITE else {},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)

if os.getenv("APP_ENV", "dev").strip().lower() == "prod" and IS_SQLITE:
    warnings.warn(
        "APP_ENV=prod is using SQLite. Set GENAI_SYSTEMS_LAB_DATABASE_URL for a shared production database.",
        RuntimeWarning,
        stacklevel=2,
    )


def _ensure_run_json_column(column_name: str) -> None:
    """Add a JSON-backed text column to ``runs`` for existing SQLite databases."""
    if not IS_SQLITE:
        return

    with engine.begin() as connection:
        tables = {
            row[0]
            for row in connection.exec_driver_sql(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        if "runs" not in tables:
            return

        columns = {
            row[1]
            for row in connection.exec_driver_sql("PRAGMA table_info(runs)")
        }
        if column_name in columns:
            return

        connection.exec_driver_sql(
            f"ALTER TABLE runs ADD COLUMN {column_name} TEXT NOT NULL DEFAULT '[]'"
        )


def _ensure_run_column(column_name: str, column_def: str) -> None:
    """Add a column to ``runs`` if it does not already exist."""
    if not IS_SQLITE:
        return

    with engine.begin() as connection:
        tables = {
            row[0]
            for row in connection.exec_driver_sql(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        if "runs" not in tables:
            return

        columns = {
            row[1]
            for row in connection.exec_driver_sql("PRAGMA table_info(runs)")
        }
        if column_name in columns:
            return

        connection.exec_driver_sql(
            f"ALTER TABLE runs ADD COLUMN {column_name} {column_def}"
        )


def init_db() -> None:
    """Create database tables on startup."""
    from . import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _ensure_run_column("confidence", "FLOAT NOT NULL DEFAULT 0")
    _ensure_run_column("success", "BOOLEAN NOT NULL DEFAULT 1")
    _ensure_run_column("session_id", "INTEGER DEFAULT NULL")
    _ensure_run_json_column("memory")
    _ensure_run_json_column("timeline")
    _ensure_run_column("share_token", "VARCHAR(64) DEFAULT NULL")
    _ensure_run_column("is_public", "BOOLEAN NOT NULL DEFAULT 0")
    _ensure_run_column("expires_at", "DATETIME DEFAULT NULL")


def get_db_session() -> Generator[Session, None, None]:
    """Yield a scoped SQLAlchemy session for request handlers."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()