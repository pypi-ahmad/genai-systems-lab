"""SQL generation module."""

from __future__ import annotations

import re

from shared.llm.gemini import generate_text


MODEL_NAME = "gemini-3.1-pro-preview"
DISALLOWED_SQL_PATTERNS = (
	r"\bINSERT\b",
	r"\bUPDATE\b",
	r"\bDELETE\b",
	r"\bDROP\b",
	r"\bALTER\b",
	r"\bTRUNCATE\b",
	r"\bCREATE\b",
	r"\bMERGE\b",
)


def _build_prompt(nl_query: str, schema: str) -> str:
	return f"""
You are generating DuckDB SQL from a natural language request.

Schema:
{schema}

User request:
{nl_query}

Rules:
- Return only valid DuckDB SQL.
- Return exactly one SQL statement.
- Return only a SELECT query.
- Do not use INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, CREATE, or MERGE.
- Do not include explanations, comments, markdown, or code fences.
- Use only tables and columns present in the schema.
""".strip()


def _clean_sql(sql: str) -> str:
	cleaned = sql.strip()

	if cleaned.startswith("```"):
		cleaned = re.sub(r"^```[a-zA-Z]*\s*", "", cleaned)
		cleaned = re.sub(r"\s*```$", "", cleaned)

	return cleaned.strip().rstrip(";") + ";"


def _validate_generated_sql(sql: str) -> None:
	if not sql.strip():
		raise ValueError("Generated SQL is empty.")

	if ";" in sql[:-1]:
		raise ValueError("Generated SQL must contain exactly one statement.")

	if not re.match(r"^SELECT\b", sql, flags=re.IGNORECASE | re.DOTALL):
		raise ValueError("Generated SQL must start with SELECT.")

	for pattern in DISALLOWED_SQL_PATTERNS:
		if re.search(pattern, sql, flags=re.IGNORECASE):
			raise ValueError("Generated SQL contains a disallowed statement.")


def generate_sql(nl_query: str, schema: str) -> str:
	prompt = _build_prompt(nl_query=nl_query, schema=schema)
	sql = _clean_sql(generate_text(prompt=prompt, model=MODEL_NAME))
	_validate_generated_sql(sql)
	return sql


__all__ = ["generate_sql"]