from __future__ import annotations

import re
import subprocess
import sys
import tempfile

from app.state import EXEC_TIMEOUT, DebugState

_BLOCKED_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\bopen\s*\(.*['\"]w['\"]", re.IGNORECASE),
    re.compile(r"\bos\.remove\b"),
    re.compile(r"\bos\.unlink\b"),
    re.compile(r"\bos\.rmdir\b"),
    re.compile(r"\bshutil\.rmtree\b"),
    re.compile(r"\bshutil\.move\b"),
    re.compile(r"\bos\.rename\b"),
    re.compile(r"\bos\.system\b"),
    re.compile(r"\bsubprocess\b"),
    re.compile(r"\bsocket\b"),
    re.compile(r"\bhttp\.server\b"),
    re.compile(r"\bctypes\b"),
    re.compile(r"\bmultiprocessing\b"),
    re.compile(r"\b__import__\b"),
    re.compile(r"\beval\s*\("),
    re.compile(r"\bexec\s*\("),
]


def _check_blocked(code: str) -> str | None:
    """Return a rejection reason if *code* contains a blocked pattern."""
    for pattern in _BLOCKED_PATTERNS:
        match = pattern.search(code)
        if match:
            return f"Blocked: disallowed pattern '{match.group()}'"
    return None


def _safe_exec(code: str, timeout: int = EXEC_TIMEOUT) -> dict:
    """Run *code* in a subprocess sandbox with a timeout."""
    reason = _check_blocked(code)
    if reason:
        return {"stdout": "", "stderr": reason, "exit_code": 1}

    try:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, prefix="dbg_test_",
        ) as tmp:
            tmp.write(code)
            tmp_path = tmp.name

        result = subprocess.run(
            [sys.executable, tmp_path],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=tempfile.gettempdir(),
        )
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {
            "stdout": "",
            "stderr": f"Execution timed out after {timeout}s",
            "exit_code": 1,
        }
    except Exception as exc:
        return {"stdout": "", "stderr": str(exc), "exit_code": 1}


def _format_result(result: dict) -> str:
    parts = [f"exit_code: {result['exit_code']}"]
    if result["stdout"]:
        parts.append(f"stdout:\n{result['stdout'].rstrip()}")
    if result["stderr"]:
        parts.append(f"stderr:\n{result['stderr'].rstrip()}")
    if result["exit_code"] == 0 and not result["stderr"]:
        parts.append("OK")
    return "\n".join(parts)


def tester_node(state: DebugState) -> dict:
    code = state.get("fixed_code", "")
    test_cases = state.get("test_cases", "")

    if not code.strip():
        return {"test_result": "exit_code: 1\nstderr:\nNo code to test."}

    combined = code
    if test_cases.strip():
        combined = code + "\n\n" + test_cases

    result = _safe_exec(combined)
    return {"test_result": _format_result(result)}
