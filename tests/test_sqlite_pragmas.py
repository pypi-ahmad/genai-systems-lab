"""Regression tests for SQLite connection-level pragmas.

The audit flagged missing foreign-key enforcement, WAL journal mode, busy
timeout, and synchronous tuning.  ``shared.api.db`` installs a ``connect``
event listener that applies all of these on every new DB-API connection.
These tests pin that behaviour down so a future refactor cannot silently
revert to SQLite's (unsafe) defaults.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import create_engine, event, text

# Import the module so the ``connect`` listener is registered against the
# live engine; we do not use the shared engine itself for isolation.
from shared.api import db as shared_db  # noqa: F401


def _make_file_engine(tmp_path: Path):
    """Create a fresh file-backed SQLite engine wired to the same listener."""
    url = f"sqlite:///{(tmp_path / 'pragma-probe.db').as_posix()}"
    engine = create_engine(url, future=True)

    # Mirror the production listener onto this probe engine so we exercise
    # the real function and fail if its contents drift.
    event.listen(engine, "connect", shared_db._apply_sqlite_pragmas)
    return engine


def test_foreign_keys_are_enforced(tmp_path: Path) -> None:
    engine = _make_file_engine(tmp_path)
    with engine.connect() as conn:
        assert conn.exec_driver_sql("PRAGMA foreign_keys").scalar() == 1


def test_journal_mode_is_wal_for_file_backed_sqlite(tmp_path: Path) -> None:
    engine = _make_file_engine(tmp_path)
    with engine.connect() as conn:
        mode = conn.exec_driver_sql("PRAGMA journal_mode").scalar()
    assert isinstance(mode, str)
    assert mode.lower() == "wal", f"expected WAL journal mode, got {mode!r}"


def test_busy_timeout_is_at_least_five_seconds(tmp_path: Path) -> None:
    engine = _make_file_engine(tmp_path)
    with engine.connect() as conn:
        timeout_ms = conn.exec_driver_sql("PRAGMA busy_timeout").scalar()
    assert isinstance(timeout_ms, int)
    assert timeout_ms >= 5000, f"busy_timeout must be >= 5000 ms, got {timeout_ms}"


def test_synchronous_mode_is_normal(tmp_path: Path) -> None:
    # ``PRAGMA synchronous`` returns an int: 0=OFF, 1=NORMAL, 2=FULL, 3=EXTRA.
    engine = _make_file_engine(tmp_path)
    with engine.connect() as conn:
        sync = conn.exec_driver_sql("PRAGMA synchronous").scalar()
    assert sync == 1, f"expected synchronous=NORMAL (1), got {sync}"


def test_temp_store_is_memory(tmp_path: Path) -> None:
    # ``PRAGMA temp_store`` returns an int: 0=DEFAULT, 1=FILE, 2=MEMORY.
    engine = _make_file_engine(tmp_path)
    with engine.connect() as conn:
        store = conn.exec_driver_sql("PRAGMA temp_store").scalar()
    assert store == 2, f"expected temp_store=MEMORY (2), got {store}"


def test_foreign_key_violation_is_rejected(tmp_path: Path) -> None:
    """End-to-end sanity: with FK enforcement ON, an invalid insert fails."""
    engine = _make_file_engine(tmp_path)
    with engine.begin() as conn:
        conn.exec_driver_sql(
            "CREATE TABLE parent (id INTEGER PRIMARY KEY)"
        )
        conn.exec_driver_sql(
            "CREATE TABLE child ("
            "  id INTEGER PRIMARY KEY,"
            "  parent_id INTEGER NOT NULL REFERENCES parent(id)"
            ")"
        )

    with pytest.raises(Exception) as excinfo:
        with engine.begin() as conn:
            conn.execute(text("INSERT INTO child (id, parent_id) VALUES (1, 999)"))
    # SQLite surfaces this as ``IntegrityError``/``OperationalError`` depending
    # on the driver version — match on the message instead of the class.
    assert "FOREIGN KEY" in str(excinfo.value).upper()
