"""SQL execution module."""

from __future__ import annotations

import importlib.util
import logging
from pathlib import Path

import duckdb
import pandas as pd


def _load_symbol(module_name: str, symbol_name: str):
	try:
		module = __import__(f"{__package__}.{module_name}", fromlist=[symbol_name])
		return getattr(module, symbol_name)
	except (ImportError, AttributeError, TypeError):
		module_path = Path(__file__).with_name(f"{module_name}.py")
		spec = importlib.util.spec_from_file_location(f"nl2sql_{module_name}", module_path)
		if spec is None or spec.loader is None:
			raise RuntimeError(f"Unable to load module '{module_name}'.")

		module = importlib.util.module_from_spec(spec)
		spec.loader.exec_module(module)
		return getattr(module, symbol_name)


LOGGER = logging.getLogger("nl2sql_agent.executor")
get_connection = _load_symbol("schema", "get_connection")
validate_sql = _load_symbol("validator", "validate_sql")
MAX_RESULT_ROWS = 100


def execute_sql(sql: str) -> pd.DataFrame:
	if not validate_sql(sql):
		raise ValueError("SQL query failed security validation.")

	# The complete statement passed deny-by-default DuckDB AST validation above;
	# this wrapper only caps returned rows and cannot introduce new SQL tokens.
	bounded_sql = f"SELECT * FROM ({sql.strip().rstrip(';')}) AS safe_query LIMIT {MAX_RESULT_ROWS}"  # nosec B608
	try:
		return get_connection().execute(bounded_sql).fetchdf()
	except duckdb.Error as exc:
		LOGGER.warning("DuckDB query execution failed: %s", exc)
		raise RuntimeError(f"SQL execution failed: {exc}") from exc


__all__ = ["execute_sql"]
