"""Query validation module."""

from __future__ import annotations

import re


DISALLOWED_SQL_PATTERNS = (
	r"\bDROP\b",
	r"\bDELETE\b",
	r"\bUPDATE\b",
	r"\bINSERT\b",
	r"\bALTER\b",
)


def validate_sql(sql: str) -> bool:
	candidate = sql.strip()

	if not candidate:
		return False

	if ";" in candidate[:-1]:
		return False

	if not re.match(r"^SELECT\b", candidate, flags=re.IGNORECASE | re.DOTALL):
		return False

	for pattern in DISALLOWED_SQL_PATTERNS:
		if re.search(pattern, candidate, flags=re.IGNORECASE):
			return False

	return True


__all__ = ["validate_sql"]