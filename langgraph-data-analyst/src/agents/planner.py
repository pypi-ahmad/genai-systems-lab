"""Planner agent node — creates a structured, executable analysis plan.

The planner takes the user's natural-language query and produces a
deterministic, step-by-step plan that downstream nodes can execute.
"""

from __future__ import annotations

import json
import logging

from src.llm.client import generate_pro
from src.schemas.state import AnalystState

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are a senior data analyst.  Given a user query, produce a JSON array of \
concrete analysis steps that a Python executor can carry out on a pandas \
DataFrame called `df`.

Rules:
- Return ONLY a JSON array of strings — no markdown, no commentary.
- Each step must be a concrete, executable instruction (e.g. \
  "Compute the mean of column 'revenue' grouped by 'region'").
- Do NOT include vague steps like "Explore the data" or "Think about it".
- Every step must reference specific operations (filter, group, aggregate, \
  sort, merge, plot, etc.) or specific column names when known.
- 2–6 steps maximum.
- Order steps logically: data cleaning → computation → interpretation.
- If the query is unclear, plan a basic descriptive-statistics summary.

Example output:
["Filter rows where status == 'active'", \
"Group by region and compute sum of revenue", \
"Sort results by revenue descending", \
"Create a horizontal bar chart of revenue by region"]
"""


def plan_analysis(state: AnalystState) -> dict:
    """Generate a structured analysis plan from the user query.

    Reads:
        ``user_query``, ``error``, ``retry_count``

    Writes:
        ``plan``
    """
    query: str = state.get("user_query", "")
    retry_count: int = state.get("retry_count", 0)
    previous_error: str | None = state.get("error")

    logger.info(
        "Planning analysis (attempt %d): %.120s", retry_count + 1, query,
    )

    prompt = f"{SYSTEM_PROMPT}\n\nUser query: {query}"
    if previous_error and retry_count > 0:
        prompt += (
            f"\n\nThe previous attempt failed with this error:\n"
            f"{previous_error}\n"
            "Adjust the plan to avoid this failure."
        )

    raw = generate_pro(prompt)
    plan = _parse_plan(raw, query)

    logger.info("Plan created with %d step(s)", len(plan))

    return {"plan": "\n".join(f"{i}. {step}" for i, step in enumerate(plan, 1))}


def _parse_plan(raw: str, query: str) -> list[str]:
    """Extract a list of step strings from the LLM response.

    Falls back to a safe default plan when parsing fails.
    """
    text = raw.strip()

    # Strip markdown fences if present.
    if text.startswith("```"):
        text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

    try:
        steps = json.loads(text)
        if isinstance(steps, list) and all(isinstance(s, str) for s in steps):
            valid = [s.strip() for s in steps if s.strip()]
            if valid:
                return valid
    except (json.JSONDecodeError, TypeError):
        pass

    logger.warning("Failed to parse plan from LLM response; using fallback")
    return [
        "Load and inspect the DataFrame (shape, dtypes, missing values)",
        "Compute descriptive statistics for numeric columns",
        f"Summarise findings relevant to: {query}" if query else "Summarise findings",
    ]
