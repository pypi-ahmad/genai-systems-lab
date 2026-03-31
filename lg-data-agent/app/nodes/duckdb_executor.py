"""Execute structured plan steps via DuckDB SQL instead of pandas."""

from __future__ import annotations

import duckdb
import pandas as pd

from app.data_loader import load_data
from app.state import AnalysisState

METRICS = {"sum", "mean", "count", "min", "max"}

COMPARE_OPS = {"==": "=", "!=": "!=", ">": ">", "<": "<", ">=": ">=", "<=": "<="}

TABLE = "analysis_data"


def _result(con: duckdb.DuckDBPyConnection, sql: str) -> dict:
    """Run final SQL and return a result dict matching the pandas executor format."""
    df = con.execute(sql).fetchdf()
    return {
        "data": df.to_dict(orient="records"),
        "columns": df.columns.tolist(),
        "shape": list(df.shape),
        "error": None,
    }


def _error(msg: str) -> dict:
    return {"data": None, "columns": [], "shape": [], "error": msg}


def _quote(identifier: str) -> str:
    """Quote a column/table identifier for DuckDB."""
    return '"' + identifier.replace('"', '""') + '"'


def _step_to_sql(prev: str, step: dict) -> str:
    """Translate a single plan step dict into a SQL query wrapping *prev*."""
    op = step.get("operation", "")
    col = step.get("column", "")

    if op == "filter":
        cond = step.get("condition", "==")
        sql_op = COMPARE_OPS.get(cond)
        if sql_op is None:
            raise ValueError(f"Unsupported filter condition: '{cond}'")
        value = step.get("value", "")
        # Try numeric literal first, fall back to string
        try:
            float(value)
            literal = value
        except (ValueError, TypeError):
            literal = "'" + str(value).replace("'", "''") + "'"
        return f"SELECT * FROM ({prev}) AS _t WHERE {_quote(col)} {sql_op} {literal}"

    if op == "group_by":
        target = step.get("target", "")
        metric = step.get("metric", "sum")
        if metric not in METRICS:
            metric = "sum"
        if target:
            agg = f"{metric}({_quote(target)}) AS {_quote(target)}"
        else:
            agg = f"{metric}(*) AS agg"
        return f"SELECT {_quote(col)}, {agg} FROM ({prev}) AS _t GROUP BY {_quote(col)}"

    if op == "sort":
        order = "ASC" if step.get("order", "ascending") != "descending" else "DESC"
        return f"SELECT * FROM ({prev}) AS _t ORDER BY {_quote(col)} {order}"

    if op == "aggregate":
        metric = step.get("metric", "mean")
        if metric == "describe" or metric not in METRICS:
            metric = "mean"
        if col == "*":
            return (
                f"SELECT {metric}(COLUMNS(*)) FROM ({prev}) AS _t"
                if metric in ("sum", "mean", "count", "min", "max")
                else f"SELECT * FROM ({prev}) AS _t"
            )
        return f"SELECT {metric}({_quote(col)}) AS {_quote(col)} FROM ({prev}) AS _t"

    if op == "select":
        cols = [_quote(c.strip()) for c in col.split(",")]
        return f"SELECT {', '.join(cols)} FROM ({prev}) AS _t"

    if op == "drop":
        cols_to_drop = {c.strip() for c in col.split(",")}
        return (
            f"SELECT * EXCLUDE ({', '.join(_quote(c) for c in cols_to_drop)}) "
            f"FROM ({prev}) AS _t"
        )

    if op == "rename":
        new_name = step.get("value", col)
        safe_col = col.replace("'", "''")
        return (
            f"SELECT COLUMNS(c -> c != '{safe_col}'), "
            f"{_quote(col)} AS {_quote(new_name)} FROM ({prev}) AS _t"
        )

    if op == "pivot":
        target = step.get("target", "")
        metric = step.get("metric", "sum")
        if metric not in METRICS:
            metric = "sum"
        return (
            f"PIVOT ({prev}) ON {_quote(col)} "
            f"USING {metric}({_quote(target) if target else '*'})"
        )

    raise ValueError(f"Unsupported operation: '{op}'")


def duckdb_executor_node(state: AnalysisState) -> dict:
    """Execute plan steps by compiling them into chained DuckDB SQL."""
    plan = state.get("plan", [])
    if not plan:
        return {"execution_result": _error("Empty plan")}

    try:
        df = load_data()
    except Exception as exc:
        return {"execution_result": _error(f"Failed to load data: {exc}")}

    con = duckdb.connect()
    try:
        con.register(TABLE, df)
        sql = f"SELECT * FROM {TABLE}"

        for i, step in enumerate(plan):
            op = step.get("operation", "")
            try:
                sql = _step_to_sql(sql, step)
            except ValueError as exc:
                return {"execution_result": _error(f"Step {i} ({op}): {exc}")}

        try:
            return {"execution_result": _result(con, sql)}
        except duckdb.Error as exc:
            return {"execution_result": _error(f"DuckDB query failed: {exc}")}
    finally:
        con.close()
