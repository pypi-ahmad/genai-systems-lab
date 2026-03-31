"""SQL execution module."""

from __future__ import annotations

import importlib.util
import logging
from pathlib import Path

import duckdb
import pandas as pd


def _load_get_connection():
	try:
		from .schema import get_connection

		return get_connection
	except ImportError:
		schema_path = Path(__file__).with_name("schema.py")
		spec = importlib.util.spec_from_file_location("nl2sql_schema", schema_path)
		if spec is None or spec.loader is None:
			raise RuntimeError("Unable to load schema module.")

		module = importlib.util.module_from_spec(spec)
		spec.loader.exec_module(module)
		return module.get_connection


LOGGER = logging.getLogger("nl2sql_agent.executor")
get_connection = _load_get_connection()


def execute_sql(sql: str) -> pd.DataFrame:
	try:
		return get_connection().execute(sql).fetchdf()
	except duckdb.Error as exc:
		LOGGER.warning("DuckDB query execution failed: %s", exc)
		raise RuntimeError(f"SQL execution failed: {exc}") from exc


__all__ = ["execute_sql"]