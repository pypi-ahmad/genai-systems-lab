"""Matplotlib chart generation from execution results."""

from __future__ import annotations

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


CHART_TYPES = ("bar", "line", "pie")
DEFAULT_CHART_TYPE = "bar"


def _infer_chart_type(df: pd.DataFrame) -> str:
    if len(df.columns) < 2:
        return "bar"

    first_col = df.iloc[:, 0]
    if pd.api.types.is_datetime64_any_dtype(first_col):
        return "line"

    try:
        pd.to_datetime(first_col)
        return "line"
    except (ValueError, TypeError):
        pass

    if len(df) <= 6 and len(df.columns) == 2:
        return "pie"

    return "bar"


def generate_chart(
    execution_result: dict,
    output_path: str,
    chart_type: str | None = None,
) -> str | None:
    """Generate a chart from execution_result and save to output_path.

    Returns the path on success, None on failure.
    """
    data = execution_result.get("data")
    if not data:
        return None

    columns = execution_result.get("columns", [])
    if len(columns) < 2:
        return None

    try:
        df = pd.DataFrame(data)
    except Exception:
        return None

    if df.empty:
        return None

    if chart_type and chart_type in CHART_TYPES:
        ctype = chart_type
    else:
        ctype = _infer_chart_type(df)

    label_col = columns[0]
    value_col = columns[1]

    if not pd.api.types.is_numeric_dtype(df[value_col]):
        for col in columns[1:]:
            if pd.api.types.is_numeric_dtype(df[col]):
                value_col = col
                break
        else:
            return None

    try:
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

        fig, ax = plt.subplots(figsize=(8, 5))

        if ctype == "line":
            ax.plot(df[label_col], df[value_col], marker="o")
            ax.set_xlabel(label_col)
            ax.set_ylabel(value_col)
            plt.xticks(rotation=45, ha="right")
        elif ctype == "pie":
            ax.pie(df[value_col], labels=df[label_col], autopct="%1.1f%%")
            ax.set_ylabel("")
        else:  # bar
            ax.bar(df[label_col].astype(str), df[value_col])
            ax.set_xlabel(label_col)
            ax.set_ylabel(value_col)
            plt.xticks(rotation=45, ha="right")

        ax.set_title(f"{value_col} by {label_col}")
        fig.tight_layout()
        fig.savefig(output_path, dpi=100)
        plt.close(fig)
        return output_path
    except Exception:
        plt.close("all")
        return None
