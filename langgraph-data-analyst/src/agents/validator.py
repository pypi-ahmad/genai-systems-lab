"""Validator agent node — checks execution results against the analysis plan.

Uses :func:`generate_pro` to review whether the output logically satisfies
the user's query and the planned steps.  Detects logical errors,
inconsistencies, and missing results — not just syntax problems.
"""

from __future__ import annotations

import json
import logging

from src.llm.client import generate_pro
from src.schemas.state import AnalystState

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are a senior data-analysis quality reviewer.  You will receive:

1. The user's original query.
2. The step-by-step analysis plan.
3. The Python code that was executed.
4. The execution output (stdout).

Your job is to decide whether the output **correctly and completely** \
answers the user's query according to the plan.

Check for:
- Logical errors (wrong column used, incorrect aggregation, bad filter).
- Missing steps (plan step not reflected in output).
- Inconsistent numbers or conclusions.
- Empty or meaningless output.
- Runtime errors or tracebacks in the output.

Reply with ONLY a JSON object — no markdown, no commentary:

If the results are correct:
  {"passed": true, "reason": "Results correctly address the query."}

If there is a problem:
  {"passed": false, "reason": "<specific explanation of what is wrong>", \
"suggestion": "<concrete fix>"}
"""


def validate_output(state: AnalystState) -> dict:
    """Validate that execution results properly answer the user's query.

    Reads:
        ``user_query``, ``plan``, ``code``, ``execution_result``,
        ``error``, ``retry_count``

    Writes:
        ``validation_result``, ``validation_passed``, ``error``,
        ``retry_count``
    """
    error: str | None = state.get("error")
    retry_count: int = state.get("retry_count", 0)

    # Fast-path: execution already failed — skip LLM validation.
    if error:
        logger.info("Skipping LLM validation — execution error present")
        return {
            "validation_result": f"Execution failed: {error}",
            "validation_passed": False,
            "retry_count": retry_count + 1,
        }

    query: str = state.get("user_query", "")
    plan: str = state.get("plan", "")
    code: str = state.get("code", "")
    execution_result: str = state.get("execution_result", "")

    if not execution_result.strip():
        logger.info("Empty execution output — marking as failed")
        return {
            "validation_result": "Execution produced no output.",
            "validation_passed": False,
            "error": "Execution produced no output.",
            "retry_count": retry_count + 1,
        }

    logger.info("Validating results for query: %.100s", query)

    prompt = (
        f"{SYSTEM_PROMPT}\n\n"
        f"User query: {query}\n\n"
        f"Plan:\n{plan}\n\n"
        f"Code:\n```python\n{code}\n```\n\n"
        f"Execution output:\n{execution_result}"
    )

    raw = generate_pro(prompt)
    verdict = _parse_verdict(raw)

    if verdict["passed"]:
        logger.info("Validation PASSED: %s", verdict["reason"])
        return {
            "validation_result": verdict["reason"],
            "validation_passed": True,
        }

    reason = verdict["reason"]
    suggestion = verdict.get("suggestion", "")
    full_msg = f"{reason} Suggestion: {suggestion}" if suggestion else reason

    logger.info("Validation FAILED: %s", full_msg)
    return {
        "validation_result": full_msg,
        "validation_passed": False,
        "error": full_msg,
        "retry_count": retry_count + 1,
    }


# Keep old name as alias so workflow.py import doesn't break.
validate_results = validate_output


def _parse_verdict(raw: str) -> dict:
    """Extract the structured verdict from the LLM response.

    Returns a dict with at least ``passed`` (bool) and ``reason`` (str).
    Falls back to heuristic parsing on JSON failure.
    """
    text = raw.strip()

    # Strip markdown fences if present.
    if text.startswith("```"):
        text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

    try:
        obj = json.loads(text)
        if isinstance(obj, dict) and "passed" in obj:
            return {
                "passed": bool(obj["passed"]),
                "reason": str(obj.get("reason", "")),
                "suggestion": str(obj.get("suggestion", "")),
            }
    except (json.JSONDecodeError, TypeError):
        pass

    # Heuristic fallback: look for PASS / FAIL keywords.
    upper = text.upper()
    if upper.startswith("PASS"):
        return {"passed": True, "reason": text}
    if upper.startswith("FAIL"):
        reason = text.split(":", 1)[1].strip() if ":" in text else text
        return {"passed": False, "reason": reason}

    logger.warning("Could not parse validator response; assuming FAIL")
    return {"passed": False, "reason": text or "Validation response was empty."}
