"""Deny-by-default validation for model-generated DuckDB queries."""

from __future__ import annotations

import json
from typing import Any

import duckdb

ALLOWED_TABLES = {"customers", "orders"}
ALLOWED_EXPRESSION_CLASSES = {
	"BETWEEN",
	"CASE",
	"CAST",
	"COLUMN_REF",
	"COMPARISON",
	"CONJUNCTION",
	"CONSTANT",
	"FUNCTION",
	"OPERATOR",
	"STAR",
}
ALLOWED_FUNCTIONS = {
	"add",
	"avg",
	"coalesce",
	"count",
	"count_star",
	"date_trunc",
	"day",
	"divide",
	"length",
	"lower",
	"max",
	"min",
	"month",
	"multiply",
	"round",
	"subtract",
	"sum",
	"upper",
	"year",
}
FORBIDDEN_NODE_TYPES = {
	"PIVOT",
	"SUBQUERY",
	"TABLE_FUNCTION",
	"TABLE_IN_OUT_FUNCTION",
}
PARSER_CONFIG = {
	"enable_external_access": "false",
	"autoinstall_known_extensions": "false",
	"autoload_known_extensions": "false",
	"threads": "1",
	"memory_limit": "128MB",
}


def _is_safe_ast(value: Any, tables: set[str]) -> bool:
	if isinstance(value, list):
		return all(_is_safe_ast(item, tables) for item in value)
	if not isinstance(value, dict):
		return True

	expression_class = value.get("class")
	if expression_class is not None and expression_class not in ALLOWED_EXPRESSION_CLASSES:
		return False

	node_type = value.get("type")
	if isinstance(node_type, str) and node_type in FORBIDDEN_NODE_TYPES:
		return False

	function_name = value.get("function_name")
	if function_name is not None and str(function_name).lower() not in ALLOWED_FUNCTIONS:
		return False

	table_name = value.get("table_name")
	if table_name:
		table = str(table_name).lower()
		if table not in ALLOWED_TABLES:
			return False
		tables.add(table)

	if value.get("schema_name") not in (None, "", "main"):
		return False
	if value.get("catalog_name") not in (None, ""):
		return False

	cte_map = value.get("cte_map")
	if isinstance(cte_map, dict) and cte_map.get("map"):
		return False

	return all(_is_safe_ast(child, tables) for child in value.values())


def validate_sql(sql: str) -> bool:
	"""Accept one bounded analytics SELECT over the two in-memory demo tables."""
	candidate = sql.strip()
	if not candidate:
		return False

	try:
		with duckdb.connect(database=":memory:", config=PARSER_CONFIG) as connection:
			serialized = connection.execute(
				"SELECT json_serialize_sql(?)",
				[candidate],
			).fetchone()
		payload = json.loads(serialized[0]) if serialized else None
	except (duckdb.Error, json.JSONDecodeError, TypeError, ValueError):
		return False

	if not isinstance(payload, dict) or payload.get("error") is not False:
		return False
	statements = payload.get("statements")
	if not isinstance(statements, list) or len(statements) != 1:
		return False

	node = statements[0].get("node") if isinstance(statements[0], dict) else None
	if not isinstance(node, dict) or node.get("type") != "SELECT_NODE":
		return False

	tables: set[str] = set()
	return _is_safe_ast(node, tables) and bool(tables)


__all__ = ["validate_sql"]
