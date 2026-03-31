from __future__ import annotations

from app.state import REASONING_MODEL, DebugState
from shared.llm.gemini import generate_text


def _build_prompt(code: str, error: str, prev_result: str) -> str:
    prompt = (
        "You are an expert debugging assistant. Analyze the following buggy code "
        "and its error message. Do NOT fix the code — only diagnose the problem.\n\n"
        "Provide:\n"
        "1. Error classification (syntax, runtime, logic, or type error)\n"
        "2. The specific faulty code region\n"
        "3. Why the code fails\n"
        "4. Possible root causes\n"
        "5. Recommended fix strategy\n\n"
        f"Code:\n```\n{code}\n```\n\n"
        f"Error:\n{error}"
    )
    if prev_result:
        prompt += f"\n\nPrevious test output (from a failed fix attempt):\n{prev_result}"
    return prompt


def analyzer_node(state: DebugState) -> dict:
    code = state.get("input_code", "")
    error = state.get("error_message", "")

    if not code.strip() and not error.strip():
        return {"analysis": "No code or error provided."}

    prev_result = state.get("test_result", "")

    analysis = generate_text(
        prompt=_build_prompt(code, error, prev_result),
        model=REASONING_MODEL,
    )

    return {"analysis": analysis}
