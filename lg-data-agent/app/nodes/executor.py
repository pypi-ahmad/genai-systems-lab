from __future__ import annotations

import operator

import pandas as pd

from app.data_loader import load_data
from app.state import AnalysisState

COMPARE_OPS = {
    "==": operator.eq,
    "!=": operator.ne,
    ">": operator.gt,
    "<": operator.lt,
    ">=": operator.ge,
    "<=": operator.le,
}

METRICS = {"sum", "mean", "count", "min", "max", "describe"}


def _result(df: pd.DataFrame) -> dict:
    """Build a success result dict from a DataFrame (or Series)."""
    if isinstance(df, pd.Series):
        df = df.to_frame()
    return {
        "data": df.to_dict(orient="records"),
        "columns": df.columns.tolist(),
        "shape": list(df.shape),
        "error": None,
    }


def _error(msg: str) -> dict:
    return {"data": None, "columns": [], "shape": [], "error": msg}


def _check_column(df: pd.DataFrame, col: str) -> str | None:
    """Return error string if column missing, else None."""
    if col not in df.columns:
        return f"Column not found: '{col}' (available: {df.columns.tolist()})"
    return None


# ── Operation handlers ──────────────────────────────────────────────


def _apply_filter(df: pd.DataFrame, step: dict) -> pd.DataFrame | str:
    col = step["column"]
    err = _check_column(df, col)
    if err:
        return err

    cond = step.get("condition", "==")
    if cond not in COMPARE_OPS:
        return f"Unsupported filter condition: '{cond}'"

    raw_value = step.get("value", "")
    dtype = df[col].dtype

    try:
        if pd.api.types.is_numeric_dtype(dtype):
            value = float(raw_value)
        elif pd.api.types.is_datetime64_any_dtype(dtype):
            value = pd.to_datetime(raw_value)
        else:
            value = str(raw_value)
    except (ValueError, TypeError) as exc:
        return f"Cannot convert filter value '{raw_value}' for column '{col}': {exc}"

    mask = COMPARE_OPS[cond](df[col], value)
    return df.loc[mask].reset_index(drop=True)


def _apply_group_by(df: pd.DataFrame, step: dict) -> pd.DataFrame | str:
    col = step["column"]
    err = _check_column(df, col)
    if err:
        return err

    target = step.get("target", "")
    metric = step.get("metric", "sum")

    if target:
        err = _check_column(df, target)
        if err:
            return err
        grouped = df.groupby(col)[target]
    else:
        grouped = df.groupby(col)

    if metric not in METRICS or metric == "describe":
        metric = "sum"

    result = getattr(grouped, metric)()
    if isinstance(result, pd.Series):
        result = result.reset_index()
    else:
        result = result.reset_index()
    return result


def _apply_sort(df: pd.DataFrame, step: dict) -> pd.DataFrame | str:
    col = step["column"]
    err = _check_column(df, col)
    if err:
        return err
    ascending = step.get("order", "ascending") != "descending"
    return df.sort_values(col, ascending=ascending).reset_index(drop=True)


def _apply_aggregate(df: pd.DataFrame, step: dict) -> pd.DataFrame | str:
    col = step["column"]
    metric = step.get("metric", "describe")

    if col == "*":
        target = df.select_dtypes(include="number")
    else:
        err = _check_column(df, col)
        if err:
            return err
        target = df[[col]]

    if metric == "describe":
        return target.describe()

    if metric not in METRICS:
        return f"Unsupported metric: '{metric}'"

    result = getattr(target, metric)()
    if isinstance(result, pd.Series):
        result = result.to_frame(name=metric).T
    return result


def _apply_select(df: pd.DataFrame, step: dict) -> pd.DataFrame | str:
    cols = [c.strip() for c in step["column"].split(",")]
    for c in cols:
        err = _check_column(df, c)
        if err:
            return err
    return df[cols]


def _apply_drop(df: pd.DataFrame, step: dict) -> pd.DataFrame | str:
    cols = [c.strip() for c in step["column"].split(",")]
    for c in cols:
        err = _check_column(df, c)
        if err:
            return err
    return df.drop(columns=cols)


def _apply_rename(df: pd.DataFrame, step: dict) -> pd.DataFrame | str:
    col = step["column"]
    err = _check_column(df, col)
    if err:
        return err
    new_name = step.get("value", col)
    return df.rename(columns={col: new_name})


def _apply_pivot(df: pd.DataFrame, step: dict) -> pd.DataFrame | str:
    col = step["column"]
    err = _check_column(df, col)
    if err:
        return err
    target = step.get("target", "")
    if target:
        err = _check_column(df, target)
        if err:
            return err
    metric = step.get("metric", "sum")
    if metric not in METRICS or metric == "describe":
        metric = "sum"
    try:
        result = df.pivot_table(
            index=df.columns[0] if df.columns[0] != col else df.columns[1],
            columns=col,
            values=target or None,
            aggfunc=metric,
        )
        return result.reset_index()
    except Exception as exc:
        return f"Pivot failed: {exc}"


HANDLERS = {
    "filter": _apply_filter,
    "group_by": _apply_group_by,
    "sort": _apply_sort,
    "aggregate": _apply_aggregate,
    "select": _apply_select,
    "drop": _apply_drop,
    "rename": _apply_rename,
    "pivot": _apply_pivot,
}


# ── Node ────────────────────────────────────────────────────────────


def executor_node(state: AnalysisState) -> dict:
    plan = state.get("plan", [])
    if not plan:
        return {"execution_result": _error("Empty plan")}

    try:
        df = load_data()
    except Exception as exc:
        return {"execution_result": _error(f"Failed to load data: {exc}")}

    for i, step in enumerate(plan):
        op = step.get("operation", "")
        handler = HANDLERS.get(op)
        if handler is None:
            return {"execution_result": _error(f"Step {i}: unsupported operation '{op}'")}

        try:
            result = handler(df, step)
        except Exception as exc:
            return {"execution_result": _error(f"Step {i} ({op}): {exc}")}

        if isinstance(result, str):
            return {"execution_result": _error(f"Step {i} ({op}): {result}")}

        df = result

    return {"execution_result": _result(df)}