"""DataFrame loading and profiling utilities.

Supports CSV and Excel files.  Provides structured info and summary
statistics for LLM-driven analysis workflows.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

_LOADERS: dict[str, callable] = {
    ".csv": pd.read_csv,
    ".xlsx": pd.read_excel,
    ".xls": pd.read_excel,
}


def load_dataframe(path: str | Path) -> pd.DataFrame:
    """Load a CSV or Excel file into a DataFrame.

    Args:
        path: File path. Supported extensions: ``.csv``, ``.xlsx``, ``.xls``.

    Returns:
        The loaded DataFrame.

    Raises:
        FileNotFoundError: If *path* does not exist.
        ValueError: If the file extension is not supported.
        RuntimeError: If loading fails for any other reason.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    suffix = path.suffix.lower()
    loader = _LOADERS.get(suffix)
    if loader is None:
        raise ValueError(
            f"Unsupported format '{suffix}'. "
            f"Supported: {', '.join(sorted(_LOADERS))}"
        )

    try:
        df = loader(path)
    except Exception as exc:
        raise RuntimeError(f"Failed to load '{path.name}': {exc}") from exc

    logger.info("Loaded %s: %d rows × %d columns", path.name, *df.shape)
    return df


def get_basic_info(df: pd.DataFrame) -> dict:
    """Return basic metadata about a DataFrame.

    Returns:
        A dict with keys ``rows``, ``columns``, ``column_names``,
        ``dtypes``, ``missing``, and ``memory_mb``.
    """
    missing: dict[str, int] = {}
    for col in df.columns:
        n = int(df[col].isna().sum())
        if n > 0:
            missing[col] = n

    return {
        "rows": len(df),
        "columns": len(df.columns),
        "column_names": list(df.columns),
        "dtypes": {col: str(df[col].dtype) for col in df.columns},
        "missing": missing,
        "memory_mb": round(float(df.memory_usage(deep=True).sum()) / 1_048_576, 4),
    }


def get_summary_stats(df: pd.DataFrame) -> dict:
    """Return summary statistics for a DataFrame.

    Returns:
        A dict with keys ``numeric`` (per-column stats for numeric
        columns) and ``categorical`` (value counts for object/category
        columns).
    """
    numeric: dict[str, dict] = {}
    for col in df.select_dtypes(include="number").columns:
        s = df[col].dropna()
        numeric[col] = {
            "count": int(s.count()),
            "mean": round(float(s.mean()), 4),
            "std": round(float(s.std()), 4) if len(s) > 1 else 0.0,
            "min": float(s.min()),
            "max": float(s.max()),
            "median": float(s.median()),
        }

    categorical: dict[str, dict[str, int]] = {}
    for col in df.select_dtypes(include=["object", "category"]).columns:
        top = df[col].value_counts().head(10)
        categorical[col] = {str(k): int(v) for k, v in top.items()}

    return {"numeric": numeric, "categorical": categorical}


# ── Backward-compatible aliases used by other modules ─────────────
load_dataset = load_dataframe


def profile_dataset(df: pd.DataFrame) -> str:
    """Generate a text profile of *df* (legacy helper).

    Combines :func:`get_basic_info` and :func:`get_summary_stats` into a
    plain-text summary suitable for LLM context injection.
    """
    info = get_basic_info(df)
    stats = get_summary_stats(df)
    lines: list[str] = []

    lines.append(f"Shape: {info['rows']:,} rows × {info['columns']} columns")
    lines.append("")

    lines.append("Columns:")
    for col in info["column_names"]:
        miss = info["missing"].get(col, 0)
        pct = miss / info["rows"] * 100 if info["rows"] else 0.0
        lines.append(f"  {col}: {info['dtypes'][col]} | {miss} missing ({pct:.1f}%)")
    lines.append("")

    if stats["numeric"]:
        lines.append("Numeric statistics:")
        for col, s in stats["numeric"].items():
            lines.append(
                f"  {col}: mean={s['mean']}, std={s['std']}, "
                f"min={s['min']}, max={s['max']}, median={s['median']}"
            )
        lines.append("")

    if stats["categorical"]:
        lines.append("Categorical columns (top values):")
        for col, counts in stats["categorical"].items():
            vals = ", ".join(f"{k!r}: {v}" for k, v in counts.items())
            lines.append(f"  {col}: {vals}")
        lines.append("")

    sample_n = min(5, info["rows"])
    if sample_n > 0:
        lines.append(f"First {sample_n} rows:")
        for line in df.head(sample_n).to_string(max_colwidth=50).splitlines():
            lines.append(f"  {line}")

    return "\n".join(lines)
