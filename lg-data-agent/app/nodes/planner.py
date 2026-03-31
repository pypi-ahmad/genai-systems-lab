from __future__ import annotations

from app.data_loader import get_metadata, load_data
from app.state import (
    MAX_PLAN_STEPS,
    REASONING_MODEL,
    SUPPORTED_OPERATIONS,
    AnalysisState,
)
from shared.llm.gemini import generate_structured

PLAN_SCHEMA = {
    "type": "object",
    "properties": {
        "steps": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "description": "One of: " + ", ".join(SUPPORTED_OPERATIONS),
                    },
                    "column": {
                        "type": "string",
                        "description": "Target column name.",
                    },
                    "metric": {
                        "type": "string",
                        "description": "Aggregation metric (sum, mean, count, min, max). Only for group_by / aggregate.",
                    },
                    "target": {
                        "type": "string",
                        "description": "Column to aggregate. Only for group_by / aggregate.",
                    },
                    "condition": {
                        "type": "string",
                        "description": "Comparison operator (==, !=, >, <, >=, <=). Only for filter.",
                    },
                    "value": {
                        "type": "string",
                        "description": "Value for filter condition or rename target.",
                    },
                    "order": {
                        "type": "string",
                        "description": "Sort order: ascending or descending. Only for sort.",
                    },
                },
                "required": ["operation", "column"],
            },
            "description": "Ordered list of data operations.",
        },
    },
    "required": ["steps"],
}

FALLBACK_PLAN = [{"operation": "aggregate", "column": "*", "metric": "describe"}]


def _build_prompt(query: str, metadata: dict, error: str | None = None) -> str:
    ops = ", ".join(SUPPORTED_OPERATIONS)
    lines = [
        "You are a data analysis planner. Given a user query and dataset metadata, "
        "produce an ordered list of structured data operations to answer the query.",
        "Steps execute sequentially — each step receives the output of the previous step.",
        "Use multiple steps when the query requires filtering, grouping, sorting, or "
        "combining transformations.",
        "",
        "Rules:",
        f"- Each step uses exactly one operation from: {ops}.",
        f"- Maximum {MAX_PLAN_STEPS} steps.",
        "- Only reference columns that exist in the dataset (or produced by a prior step).",
        "- Do NOT generate free-form code, SQL, or Python — only structured operation dicts.",
        "- For group_by/aggregate, include metric (sum/mean/count/min/max) and target column.",
        "- For filter, include condition (==, !=, >, <, >=, <=) and value.",
        "- For sort, include order (ascending or descending).",
        "- Prefer multi-step plans over single catch-all steps.",
        "",
        "Common multi-step patterns:",
        "  filter → group_by → sort    (e.g. revenue by region for 2024, sorted desc)",
        "  filter → aggregate           (e.g. average revenue for North region)",
        "  group_by → sort              (e.g. total revenue by region, highest first)",
        "  select → filter → aggregate  (e.g. pick columns, filter rows, then summarize)",
        "  group_by → filter → sort     (e.g. regions with revenue > 1000, sorted)",
        "",
        f"Dataset columns: {metadata['columns']}",
        f"Column types: {metadata['dtypes']}",
        f"Shape: {metadata['shape'][0]} rows × {metadata['shape'][1]} columns",
        f"Sample rows: {metadata['sample']}",
        "",
        f"Query: {query}",
    ]

    if error:
        lines += [
            "",
            "The previous plan failed with the following error. "
            "Revise the plan to avoid this issue:",
            error,
        ]

    return "\n".join(lines)


def _validate_step(step: dict) -> bool:
    """Return True if the step has a valid operation and a column field."""
    op = step.get("operation", "")
    col = step.get("column", "")
    return bool(op in SUPPORTED_OPERATIONS and col)


def planner_node(state: AnalysisState) -> dict:
    query = state.get("query", "")
    if not query.strip():
        return {"plan": list(FALLBACK_PLAN)}

    df = load_data()
    metadata = get_metadata(df)

    error = state.get("execution_result", {}).get("error")

    result = generate_structured(
        prompt=_build_prompt(query, metadata, error),
        model=REASONING_MODEL,
        schema=PLAN_SCHEMA,
    )

    steps = [s for s in result.get("steps", []) if _validate_step(s)]

    if not steps:
        return {"plan": list(FALLBACK_PLAN)}

    return {"plan": steps[:MAX_PLAN_STEPS]}