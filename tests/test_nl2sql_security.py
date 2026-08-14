"""Security regression tests for the model-generated NL2SQL boundary."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

PROJECT_APP = Path(__file__).resolve().parents[1] / "genai-nl2sql-agent" / "app"


def _load_module(name: str):
    spec = importlib.util.spec_from_file_location(f"nl2sql_test_{name}", PROJECT_APP / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


validator = _load_module("validator")
executor = _load_module("executor")


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT name, country FROM customers ORDER BY name LIMIT 5",
        (
            "SELECT c.name, SUM(o.amount) AS revenue "
            "FROM customers AS c JOIN orders AS o ON c.id = o.customer_id "
            "GROUP BY c.name ORDER BY revenue DESC LIMIT 3"
        ),
        "SELECT AVG(amount) AS average_amount FROM orders WHERE amount >= 100",
    ],
)
def test_valid_analytics_queries_remain_allowed(sql: str) -> None:
    assert validator.validate_sql(sql) is True
    assert len(executor.execute_sql(sql)) <= executor.MAX_RESULT_ROWS


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT content FROM read_text('README.md')",
        "SELECT * FROM read_csv_auto('data.csv')",
        "SELECT * FROM read_blob('README.md')",
        "SELECT * FROM range(1000000000)",
        "SELECT * FROM customers, read_text('README.md')",
        "WITH stolen AS (SELECT * FROM read_text('README.md')) SELECT * FROM stolen",
        "SELECT * FROM information_schema.tables",
        "ATTACH 'other.db' AS other",
        "COPY customers TO 'customers.csv'",
        "INSTALL httpfs",
        "LOAD httpfs",
        "PRAGMA database_list",
        "SELECT * FROM customers; SELECT * FROM orders",
    ],
)
def test_unsafe_queries_are_rejected_at_validator_and_sink(sql: str) -> None:
    assert validator.validate_sql(sql) is False
    with pytest.raises(ValueError, match="security validation"):
        executor.execute_sql(sql)


def test_executor_caps_result_rows() -> None:
    result = executor.execute_sql(
        "SELECT c.name FROM customers AS c JOIN orders AS o ON c.id = o.customer_id"
    )
    assert len(result) <= executor.MAX_RESULT_ROWS
