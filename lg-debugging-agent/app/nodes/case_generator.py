from __future__ import annotations

import re

from app.state import REASONING_MODEL, DebugState
from shared.llm.gemini import generate_text


def _build_prompt(code: str, error: str, fixed_code: str) -> str:
    return (
        "You are an expert test engineer. Generate test cases for the fixed code below.\n\n"
        "Rules:\n"
        "- Return ONLY executable Python test code inside a single code block.\n"
        "- The tests must import nothing from external packages.\n"
        "- Use simple assert statements to verify correct behavior.\n"
        "- Cover the original bug scenario and at least one normal case.\n"
        "- Print 'ALL TESTS PASSED' at the end if every assert succeeds.\n"
        "- Do NOT include the implementation — only the test code that calls it.\n\n"
        f"Original buggy code:\n```\n{code}\n```\n\n"
        f"Error:\n{error}\n\n"
        f"Fixed code:\n```\n{fixed_code}\n```"
    )


def _extract_code(response: str) -> str:
    match = re.search(r"```(?:\w*)\n(.*?)```", response, re.DOTALL)
    if match:
        return match.group(1).strip()
    return response.strip()


def test_generator_node(state: DebugState) -> dict:
    code = state.get("input_code", "")
    error = state.get("error_message", "")
    fixed_code = state.get("fixed_code", "")

    if not fixed_code.strip():
        return {"test_cases": ""}

    response = generate_text(
        prompt=_build_prompt(code, error, fixed_code),
        model=REASONING_MODEL,
    )

    return {"test_cases": _extract_code(response)}