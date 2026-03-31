"""Reporter agent node — converts analysis results into insight-driven Markdown."""

from __future__ import annotations

import logging

from src.llm.client import generate_pro
from src.schemas.state import AnalystState

logger = logging.getLogger(__name__)

REPORT_PROMPT = """\
You are a senior data analyst. Given the query, plan, code, and execution
output below, produce a concise Markdown report with ONLY these sections:

## Key Findings
Numbered list of concrete, data-backed insights. Use exact numbers.

## Anomalies
Anything unexpected, suspicious, or inconsistent in the data/results.
Write "None detected." if nothing stands out.

## Recommendations
Actionable next steps grounded in the findings.

Rules:
- No filler, no fluff, no boilerplate introductions.
- Every sentence must convey information or an insight.
- If the analysis had errors or incomplete results, state limitations plainly.
- Use Markdown tables where they add clarity.

---

User query: {user_query}

Analysis plan:
{plan}

Code:
```python
{code}
```

Execution output:
{execution_result}

Validation: {validation_result}
"""


def generate_report(state: AnalystState) -> dict:
    """Convert execution results into an insight-driven Markdown report.

    Reads ``user_query``, ``plan``, ``code``, ``execution_result``,
    ``validation_result``, ``error``.

    Returns a dict with ``final_report``.
    """
    user_query = state.get("user_query", "")
    plan = state.get("plan", "")
    code = state.get("code", "")
    execution_result = state.get("execution_result", "")
    validation_result = state.get("validation_result", "")
    error = state.get("error", "")

    if error:
        validation_result = f"{validation_result}\nError: {error}".strip()

    prompt = REPORT_PROMPT.format(
        user_query=user_query,
        plan=plan,
        code=code,
        execution_result=execution_result,
        validation_result=validation_result,
    )

    logger.info("Generating report for query: %.100s", user_query)

    report = generate_pro(prompt)

    logger.info("Report generated: %d chars", len(report))

    return {"final_report": report}
