from __future__ import annotations

import csv
import io
import os

TOOL_DESCRIPTION = (
    "file_tool — Read files, write files, list directories, and load CSV data. "
    "Use for any step that involves loading data from disk, saving outputs, "
    "or inspecting file structures."
)

SAMPLE_DATA = [
    {"date": "2024-01-01", "revenue": "1200", "region": "North"},
    {"date": "2024-02-01", "revenue": "1500", "region": "North"},
    {"date": "2024-03-01", "revenue": "1350", "region": "North"},
    {"date": "2024-04-01", "revenue": "1600", "region": "North"},
    {"date": "2024-01-01", "revenue": "900", "region": "South"},
    {"date": "2024-02-01", "revenue": "1100", "region": "South"},
    {"date": "2024-03-01", "revenue": "1050", "region": "South"},
    {"date": "2024-04-01", "revenue": "1300", "region": "South"},
]


def run(action: str, path: str = "", content: str = "") -> str:
    if action == "read":
        if not path:
            return "Error: path is required for read."
        if not os.path.isfile(path):
            return f"Error: file not found: {path}"
        with open(path, encoding="utf-8") as f:
            return f.read()

    if action == "write":
        if not path:
            return "Error: path is required for write."
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Written {len(content)} chars to {path}"

    if action == "list":
        target = path or "."
        if not os.path.isdir(target):
            return f"Error: directory not found: {target}"
        entries = sorted(os.listdir(target))
        return "\n".join(entries) if entries else "(empty directory)"

    if action == "load_csv":
        if path and os.path.isfile(path):
            return _read_csv(path)
        return _format_rows(SAMPLE_DATA)

    if action == "sample":
        return _format_rows(SAMPLE_DATA)

    return f"Unknown action: {action}"


def _read_csv(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    if not rows:
        return "Loaded 0 rows."
    return _format_rows(rows)


def _format_rows(rows: list[dict]) -> str:
    if not rows:
        return "No data."
    columns = list(rows[0].keys())
    header = ",".join(columns)
    lines = [header]
    for row in rows:
        lines.append(",".join(str(row.get(c, "")) for c in columns))
    return f"Loaded {len(rows)} rows, columns: {columns}\n" + "\n".join(lines)

