"""Database configuration for shared API persistence."""

from __future__ import annotations

from collections.abc import Generator
import logging
import os
from pathlib import Path
import warnings

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

_LOGGER = logging.getLogger(__name__)


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
        _LOGGER.warning(
            "SQLite data directory fell back to %s — persisted data is ephemeral "
            "on serverless/read-only filesystems.",
            fallback,
        )
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
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


# ---------------------------------------------------------------------------
# SQLite hardening pragmas — applied per-connection.
#
# ``foreign_keys``     : the ForeignKey declarations in models.py are declarative
#                       only unless this is ``ON``; SQLite ignores them by default.
# ``journal_mode=WAL`` : readers no longer block writers (and vice versa) — required
#                       for concurrent batch/stream requests to coexist.
# ``synchronous=NORMAL``: safe with WAL and materially faster than the default FULL.
# ``busy_timeout=5000``: retry up to 5 s on SQLITE_BUSY instead of failing fast.
# ``temp_store=MEMORY`` : avoid writing tmp files under ``/tmp`` on serverless hosts.
#
# An ``:memory:`` database (used in tests) does not support WAL — skip it.
# ---------------------------------------------------------------------------

@event.listens_for(engine, "connect")
def _apply_sqlite_pragmas(dbapi_connection, connection_record):  # noqa: ANN001
    if not IS_SQLITE:
        return
    try:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        # WAL is persistent-file-only; in-memory engines silently no-op.
        if ":memory:" not in DATABASE_URL:
            cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.execute("PRAGMA temp_store=MEMORY")
        cursor.close()
    except Exception as exc:  # pragma: no cover — defensive only
        _LOGGER.warning("Failed to apply SQLite pragmas: %s", exc)


if os.getenv("APP_ENV", "dev").strip().lower() == "prod" and IS_SQLITE:
    warnings.warn(
        "APP_ENV=prod is using SQLite. Set GENAI_SYSTEMS_LAB_DATABASE_URL to a "
        "Postgres/MySQL URL for production persistence; SQLite is acceptable "
        "only for single-process deployments on a writable filesystem.",
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
    # Token / cost accounting — added to support per-run cost attribution.
    _ensure_run_column("prompt_tokens", "INTEGER DEFAULT NULL")
    _ensure_run_column("completion_tokens", "INTEGER DEFAULT NULL")
    _ensure_run_column("total_tokens", "INTEGER DEFAULT NULL")
    _ensure_run_column("cost_usd", "FLOAT DEFAULT NULL")
    _ensure_run_column("model_used", "VARCHAR(120) DEFAULT NULL")


def get_db_session() -> Generator[Session, None, None]:
    """Yield a scoped SQLAlchemy session for request handlers."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()