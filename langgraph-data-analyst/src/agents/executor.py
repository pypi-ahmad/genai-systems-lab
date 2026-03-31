"""Executor agent node — converts the analysis plan into runnable code and executes it.

Uses :func:`generate_fast` to translate the plan into Python, then
delegates to :func:`execute_code` for sandboxed subprocess execution.
"""

from __future__ import annotations

import logging

from src.llm.client import generate_fast
from src.schemas.state import AnalystState
from src.tools.python_executor import execute_code

logger = logging.getLogger(__name__)

CODE_PROMPT = """\
You are a Python data-analysis code generator.

Given an analysis plan and a dataframe file path, write a single Python \
script that implements every step of the plan.

Rules:
- The script must start by importing pandas and loading the data:
    import pandas as pd
    df = pd.read_csv("{dataframe_path}")  # or pd.read_excel for .xlsx/.xls
- You may also import numpy, matplotlib.pyplot, and seaborn if needed.
- Print all key results with `print()` so they appear in stdout.
- If creating charts, use `plt.savefig('/tmp/chart.png')` and then
  `print('Chart saved to /tmp/chart.png')`. Do NOT call `plt.show()`.
- Handle missing values gracefully (e.g. `dropna()` or `fillna()`).
- Keep the code concise and well-commented.
- Do NOT use `eval()`, `exec()`, `subprocess`, `os.system`, or network calls.
- Return ONLY the Python code — no markdown fences, no commentary.

Plan:
{plan}

Data file: {dataframe_path}
"""


def execute_plan(state: AnalystState) -> dict:
    """Convert the analysis plan into Python code, execute it, and capture results.

    Reads:
        ``plan``, ``dataframe_path``, ``error``, ``retry_count``

    Writes:
        ``code``, ``execution_result``, ``error``
    """
    plan: str = state.get("plan", "")
    dataframe_path: str = state.get("dataframe_path", "")
    retry_count: int = state.get("retry_count", 0)
    previous_error: str | None = state.get("error")

    if not plan:
        logger.warning("No plan provided — skipping execution")
        return {
            "code": "",
            "execution_result": "",
            "error": "No analysis plan was provided.",
        }

    logger.info("Generating code from plan (attempt %d)", retry_count + 1)

    # ── Generate code from the plan ───────────────────────────────
    prompt = CODE_PROMPT.format(
        plan=plan,
        dataframe_path=dataframe_path.replace("\\", "\\\\"),
    )
    if previous_error and retry_count > 0:
        prompt += (
            f"\n\nThe previous code failed with this error:\n"
            f"{previous_error}\n"
            "Fix the code to avoid this failure."
        )

    raw = generate_fast(prompt)
    code = _extract_code(raw)

    if not code:
        logger.warning("LLM returned no usable code")
        return {
            "code": "",
            "execution_result": "",
            "error": "Code generation produced empty output.",
        }

    logger.info("Executing generated code (%d chars)", len(code))

    # ── Execute in sandbox ────────────────────────────────────────
    result = execute_code(code)

    if result.success:
        logger.info("Execution succeeded (%d chars output)", len(result.output))
        return {
            "code": code,
            "execution_result": result.output,
            "error": None,
        }

    logger.warning("Execution failed: %.200s", result.error)
    return {
        "code": code,
        "execution_result": result.output,
        "error": result.error,
    }


# Keep the old name as an alias so workflow.py doesn't break.
execute_analysis = execute_plan


def _extract_code(raw: str) -> str:
    """Strip markdown fences if present and return clean Python code."""
    text = raw.strip()

    # Remove ```python ... ``` wrapping
    if text.startswith("```"):
        text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

    return text
