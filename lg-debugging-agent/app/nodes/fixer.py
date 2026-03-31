from __future__ import annotations

import difflib
import re

from app.state import REASONING_MODEL, DebugState
from shared.llm.gemini import generate_text


def _build_prompt(code: str, error: str, analysis: str, test_result: str, iteration: int) -> str:
    prompt = (
        "You are an expert debugging assistant. Fix the buggy code below.\n\n"
        "Rules:\n"
        "- Return ONLY a unified diff (like `diff -u`) inside a single code block.\n"
        "- The diff must apply cleanly to the original code.\n"
        "- Use `--- original` and `+++ fixed` as file headers.\n"
        "- Do NOT include explanations or anything outside the code block.\n\n"
        f"Original code:\n```\n{code}\n```\n\n"
        f"Error:\n{error}\n\n"
        f"Analysis:\n{analysis}"
    )
    if iteration > 0 and test_result:
        prompt += (
            f"\n\nThis is retry attempt {iteration}. "
            f"The previous fix failed with:\n{test_result}\n\n"
            "Generate a different fix that addresses this failure."
        )
    return prompt


def _extract_block(response: str) -> str:
    match = re.search(r"```(?:\w*)\n(.*?)```", response, re.DOTALL)
    if match:
        return match.group(1).strip()
    return response.strip()


def _apply_diff(original: str, diff_text: str) -> str | None:
    """Apply a unified diff to *original* and return the patched text.

    Returns ``None`` when the diff cannot be applied.
    """
    orig_lines = original.splitlines(keepends=True)
    if not orig_lines or not orig_lines[-1].endswith("\n"):
        orig_lines = [l + "\n" for l in original.splitlines()]

    hunks: list[tuple[int, int, list[str]]] = []
    current_start = 0
    current_len = 0
    current_lines: list[str] = []
    in_hunk = False

    for raw in diff_text.splitlines():
        line = raw + "\n"
        if raw.startswith("@@"):
            if in_hunk:
                hunks.append((current_start, current_len, current_lines))
            match = re.match(r"@@ -(\d+)(?:,(\d+))? \+\d+(?:,\d+)? @@", raw)
            if not match:
                return None
            current_start = int(match.group(1)) - 1  # 0-based
            current_len = int(match.group(2)) if match.group(2) is not None else 1
            current_lines = []
            in_hunk = True
        elif raw.startswith("---") or raw.startswith("+++"):
            continue
        elif in_hunk:
            current_lines.append(line)

    if in_hunk:
        hunks.append((current_start, current_len, current_lines))

    if not hunks:
        return None

    result: list[str] = []
    pos = 0
    for start, length, lines in hunks:
        result.extend(orig_lines[pos:start])
        for l in lines:
            if l.startswith("+"):
                result.append(l[1:])
            elif l.startswith("-"):
                pass  # removed line
            elif l.startswith(" "):
                result.append(l[1:])
            else:
                result.append(l)
        pos = start + length
    result.extend(orig_lines[pos:])
    return "".join(result).rstrip("\n") + "\n" if result else ""


def _make_diff(original: str, fixed: str) -> str:
    """Generate a unified diff between *original* and *fixed*."""
    return "".join(
        difflib.unified_diff(
            original.splitlines(keepends=True),
            fixed.splitlines(keepends=True),
            fromfile="original",
            tofile="fixed",
        )
    )


def fixer_node(state: DebugState) -> dict:
    code = state.get("input_code", "")
    error = state.get("error_message", "")
    analysis = state.get("analysis", "")
    test_result = state.get("test_result", "")
    iteration = state.get("iteration", 0)

    if not code.strip():
        return {"diff": "", "fixed_code": ""}

    response = generate_text(
        prompt=_build_prompt(code, error, analysis, test_result, iteration),
        model=REASONING_MODEL,
    )

    block = _extract_block(response)
    patched = _apply_diff(code, block)

    if patched is not None:
        diff_text = block
    else:
        # Fallback: LLM returned full code instead of a diff.
        patched = block
        diff_text = _make_diff(code, patched)

    return {"diff": diff_text, "fixed_code": patched}
