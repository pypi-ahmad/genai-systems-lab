"""Agent orchestration module."""

from __future__ import annotations

import importlib.util
import logging
from pathlib import Path
from typing import Any

import pandas as pd

from shared.llm.gemini import generate_text


MAX_SQL_ATTEMPTS = 3
SUMMARY_MODEL = "gemini-3-flash-preview"
LOGGER = logging.getLogger("nl2sql_agent.agent")


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


get_schema_description = _load_symbol("schema", "get_schema_description")
generate_sql = _load_symbol("sql_generator", "generate_sql")
validate_sql = _load_symbol("validator", "validate_sql")
execute_sql = _load_symbol("executor", "execute_sql")


def _build_summary_prompt(nl_query: str, sql: str, result: pd.DataFrame) -> str:
	preview_records = result.to_dict(orient="records")
	return f"""
You are summarizing the result of a DuckDB query for a user.

User question:
{nl_query}

Executed SQL:
{sql}

Result rows:
{preview_records}

Rules:
- Write a concise factual summary grounded only in the result rows.
- Do not mention information that is not present in the data.
- If the result is empty, say that no matching records were found.
""".strip()


def run_agent(nl_query: str) -> dict[str, Any]:
	LOGGER.info("Agent run started")

	LOGGER.info("Loading schema description")
	schema = get_schema_description()

	sql = ""
	for attempt in range(1, MAX_SQL_ATTEMPTS + 1):
		LOGGER.info("Generating SQL attempt %s/%s", attempt, MAX_SQL_ATTEMPTS)
		try:
			sql = generate_sql(nl_query=nl_query, schema=schema)
		except ValueError as exc:
			LOGGER.warning("Generated SQL was invalid on attempt %s: %s", attempt, exc)
			if attempt >= MAX_SQL_ATTEMPTS:
				raise RuntimeError("Failed to generate valid SQL after maximum retries.") from exc
			continue

		LOGGER.info("Validating generated SQL")
		if validate_sql(sql):
			break

		LOGGER.warning("SQL validation failed on attempt %s", attempt)
		if attempt >= MAX_SQL_ATTEMPTS:
			raise RuntimeError("Failed to generate valid SQL after maximum retries.")
	else:
		raise RuntimeError("Failed to generate valid SQL after maximum retries.")

	LOGGER.info("Executing SQL")
	result = execute_sql(sql)

	LOGGER.info("Summarizing result with Gemini Flash")
	summary = generate_text(
		prompt=_build_summary_prompt(nl_query=nl_query, sql=sql, result=result),
		model=SUMMARY_MODEL,
	)

	LOGGER.info("Agent run completed")
	return {
		"sql": sql,
		"result": result,
		"summary": summary,
	}


__all__ = ["run_agent"]