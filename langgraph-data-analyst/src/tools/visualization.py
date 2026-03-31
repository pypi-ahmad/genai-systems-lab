"""Visualization utilities for chart generation and figure management.

Provides helpers to save open *matplotlib* figures, apply a consistent
default style, auto-generate summary charts for a DataFrame, and safely
execute user-supplied plotting code via :func:`generate_plot`.
"""

from __future__ import annotations

import logging
import re
import tempfile
import uuid
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
import seaborn as sns  # noqa: E402

from src.config.settings import settings  # noqa: E402

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Safety patterns – block dangerous constructs in user plotting code
# ---------------------------------------------------------------------------
_DANGEROUS_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\bopen\s*\(.*['\"]w['\"]", re.IGNORECASE),
    re.compile(r"\bos\.remove\b"),
    re.compile(r"\bos\.unlink\b"),
    re.compile(r"\bos\.rmdir\b"),
    re.compile(r"\bshutil\b"),
    re.compile(r"\bos\.system\b"),
    re.compile(r"\bsubprocess\b"),
    re.compile(r"\bsocket\b"),
    re.compile(r"\bhttp\.server\b"),
    re.compile(r"\bctypes\b"),
    re.compile(r"\bmultiprocessing\b"),
    re.compile(r"\b__import__\b"),
    re.compile(r"\beval\s*\("),
    re.compile(r"\bexec\s*\("),
    re.compile(r"\bplt\.show\s*\("),
]


def _check_plot_code(code: str) -> str | None:
    """Return a rejection reason if *code* contains a blocked pattern."""
    for pattern in _DANGEROUS_PATTERNS:
        match = pattern.search(code)
        if match:
            return f"Blocked: code contains disallowed pattern '{match.group()}'"
    return None


def generate_plot(code: str, df: pd.DataFrame) -> str:
    """Execute user-supplied plotting code and save the resulting figure.

    The code runs with *df*, *plt*, *pd*, and *sns* (seaborn) available in
    its namespace.  Any open matplotlib figures are saved to a temporary PNG
    file and the path is returned.

    Args:
        code: Python source that creates a matplotlib/seaborn plot.
        df: The DataFrame to visualize.

    Returns:
        Absolute path to the saved PNG image.

    Raises:
        ValueError: If *code* is empty or contains a blocked pattern.
        RuntimeError: If execution fails or produces no figure.
    """
    if not code or not code.strip():
        raise ValueError("No plotting code provided")

    reason = _check_plot_code(code)
    if reason:
        raise ValueError(reason)

    apply_default_style()

    # Close any lingering figures so we only capture what *code* creates.
    plt.close("all")

    namespace: dict = {
        "df": df,
        "plt": plt,
        "pd": pd,
        "sns": sns,
    }

    try:
        exec(compile(code, "<plot>", "exec"), namespace)  # noqa: S102
    except Exception as exc:
        plt.close("all")
        raise RuntimeError(f"Plot code execution failed: {exc}") from exc

    fig_nums = plt.get_fignums()
    if not fig_nums:
        raise RuntimeError("No figure produced by plot code")

    # Save the last figure (most likely the intended output).
    fig = plt.figure(fig_nums[-1])
    tmp = tempfile.NamedTemporaryFile(
        suffix=".png", prefix="plot_", delete=False,
    )
    tmp.close()
    fig.savefig(tmp.name, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close("all")

    logger.info("Plot saved → %s", tmp.name)
    return tmp.name


def save_open_figures(output_dir: Path | None = None) -> list[str]:
    """Persist every currently open *matplotlib* figure to disk.

    Args:
        output_dir: Target directory.  Defaults to ``settings.output_dir``.

    Returns:
        List of file paths for the saved PNG images.
    """
    target = output_dir or settings.output_dir
    target.mkdir(parents=True, exist_ok=True)

    fig_nums = plt.get_fignums()
    if not fig_nums:
        return []

    paths: list[str] = []
    for num in fig_nums:
        fig = plt.figure(num)
        fig_id = uuid.uuid4().hex[:8]
        path = target / f"figure_{fig_id}.png"
        fig.savefig(str(path), dpi=150, bbox_inches="tight", facecolor="white")
        paths.append(str(path))
        logger.debug("Saved figure %d → %s", num, path)

    plt.close("all")
    logger.info("Saved %d figure(s)", len(paths))
    return paths


def apply_default_style() -> None:
    """Apply a clean, presentation-ready *matplotlib* style.

    Safe to call repeatedly — simply overwrites ``rcParams``.
    """
    plt.style.use("seaborn-v0_8-whitegrid")
    plt.rcParams.update(
        {
            "figure.figsize": (10, 6),
            "font.size": 11,
            "axes.titlesize": 14,
            "axes.labelsize": 12,
            "lines.linewidth": 2,
            "figure.dpi": 100,
        }
    )


def generate_summary_charts(
    df: pd.DataFrame,
    output_dir: Path | None = None,
) -> list[str]:
    """Auto-generate overview charts for *df*.

    Creates:
    * A histogram grid for the first few numeric columns.
    * Horizontal bar charts for low-cardinality categorical columns.

    Args:
        df: Source DataFrame.
        output_dir: Where to save the PNGs.

    Returns:
        List of saved file paths.
    """
    apply_default_style()
    target = output_dir or settings.output_dir
    target.mkdir(parents=True, exist_ok=True)
    paths: list[str] = []

    # ── Numeric distributions ─────────────────────────────────────
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    if numeric_cols:
        n = min(len(numeric_cols), 4)
        fig, axes = plt.subplots(1, n, figsize=(5 * n, 4))
        if n == 1:
            axes = [axes]
        for ax, col in zip(axes, numeric_cols[:n]):
            df[col].dropna().hist(ax=ax, bins=30, edgecolor="black", alpha=0.7)
            ax.set_title(col)
            ax.set_xlabel(col)
            ax.set_ylabel("Frequency")
        fig.suptitle("Numeric Distributions", fontsize=14, y=1.02)
        fig.tight_layout()
        path = target / f"distributions_{uuid.uuid4().hex[:8]}.png"
        fig.savefig(str(path), dpi=150, bbox_inches="tight", facecolor="white")
        paths.append(str(path))
        plt.close(fig)

    # ── Categorical bar charts ────────────────────────────────────
    cat_cols = [
        c
        for c in df.select_dtypes(include=["object", "category"]).columns
        if df[c].nunique() <= 20
    ]
    for col in cat_cols[:3]:
        fig, ax = plt.subplots(figsize=(8, 4))
        counts = df[col].value_counts().head(15)
        counts.plot(kind="barh", ax=ax, color="steelblue", edgecolor="black")
        ax.set_title(f"Top values — {col}")
        ax.set_xlabel("Count")
        fig.tight_layout()
        path = target / f"bar_{col}_{uuid.uuid4().hex[:8]}.png"
        fig.savefig(str(path), dpi=150, bbox_inches="tight", facecolor="white")
        paths.append(str(path))
        plt.close(fig)

    logger.info("Generated %d summary chart(s)", len(paths))
    return paths
