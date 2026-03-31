from __future__ import annotations

import csv
import io
from collections import defaultdict

TOOL_DESCRIPTION = (
    "analysis_tool — Compute metrics, parse structured data, and perform "
    "analytical operations. Use for any step that involves computing statistics, "
    "identifying trends, aggregating data, or generating analytical insights."
)


def run(action: str, data: str = "", params: str = "") -> str:
    if action == "summarize":
        return _summarize(data)
    if action == "average":
        return _average(data, column=params)
    if action == "trends":
        return _trends(data, column=params)
    if action == "group_by":
        parts = params.split(",", 1)
        group_col = parts[0].strip() if parts else ""
        value_col = parts[1].strip() if len(parts) > 1 else ""
        return _group_by(data, group_col, value_col)
    if action == "min_max":
        return _min_max(data, column=params)
    return f"Unknown action: {action}"


def _parse_csv(data: str) -> list[dict]:
    clean = data.strip()
    if "\n" not in clean:
        return []
    lines = clean.splitlines()
    # Skip "Loaded N rows..." header line if present
    for i, line in enumerate(lines):
        if not line.startswith("Loaded"):
            reader = csv.DictReader(lines[i:])
            return list(reader)
    return []


def _numeric_values(rows: list[dict], column: str) -> list[float]:
    values = []
    for row in rows:
        raw = row.get(column, "")
        try:
            values.append(float(raw))
        except (ValueError, TypeError):
            continue
    return values


def _summarize(data: str) -> str:
    rows = _parse_csv(data)
    if not rows:
        return "No data to summarize."

    columns = list(rows[0].keys())
    parts = [f"Rows: {len(rows)}", f"Columns: {columns}"]

    for col in columns:
        vals = _numeric_values(rows, col)
        if vals:
            avg = sum(vals) / len(vals)
            parts.append(f"  {col}: min={min(vals):.2f}, max={max(vals):.2f}, avg={avg:.2f}, count={len(vals)}")

    return "\n".join(parts)


def _average(data: str, column: str) -> str:
    rows = _parse_csv(data)
    if not rows:
        return "No data."
    if not column:
        return "Error: column parameter required for average."

    vals = _numeric_values(rows, column)
    if not vals:
        return f"No numeric values in column '{column}'."

    avg = sum(vals) / len(vals)
    return f"Average of '{column}': {avg:.2f} (from {len(vals)} values)"


def _trends(data: str, column: str) -> str:
    rows = _parse_csv(data)
    if not rows:
        return "No data."
    if not column:
        return "Error: column parameter required for trends."

    vals = _numeric_values(rows, column)
    if len(vals) < 2:
        return f"Not enough data points for trend analysis in '{column}'."

    changes = [vals[i] - vals[i - 1] for i in range(1, len(vals))]
    avg_change = sum(changes) / len(changes)
    direction = "increasing" if avg_change > 0 else "decreasing" if avg_change < 0 else "flat"
    pct = (vals[-1] - vals[0]) / vals[0] * 100 if vals[0] != 0 else 0

    return (
        f"Trend for '{column}': {direction}\n"
        f"  Start: {vals[0]:.2f}, End: {vals[-1]:.2f}\n"
        f"  Change: {pct:+.1f}%\n"
        f"  Avg step change: {avg_change:+.2f}\n"
        f"  Data points: {len(vals)}"
    )


def _group_by(data: str, group_col: str, value_col: str) -> str:
    rows = _parse_csv(data)
    if not rows:
        return "No data."
    if not group_col or not value_col:
        return "Error: group_by requires params='group_column,value_column'."

    groups: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        key = row.get(group_col, "")
        try:
            groups[key].append(float(row.get(value_col, "")))
        except (ValueError, TypeError):
            continue

    if not groups:
        return f"No numeric values found for grouping '{group_col}' by '{value_col}'."

    lines = [f"Group by '{group_col}', values from '{value_col}':"]
    for key in sorted(groups):
        vals = groups[key]
        total = sum(vals)
        avg = total / len(vals)
        lines.append(f"  {key}: sum={total:.2f}, avg={avg:.2f}, count={len(vals)}")

    return "\n".join(lines)


def _min_max(data: str, column: str) -> str:
    rows = _parse_csv(data)
    if not rows:
        return "No data."
    if not column:
        return "Error: column parameter required for min_max."

    vals = _numeric_values(rows, column)
    if not vals:
        return f"No numeric values in column '{column}'."

    return f"Min of '{column}': {min(vals):.2f}, Max: {max(vals):.2f}"
