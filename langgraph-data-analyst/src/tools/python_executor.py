"""Sandboxed Python code execution for data analysis tasks.

Executes user-supplied Python code in a **subprocess** with:

* A configurable timeout (default 10 s).
* Blocked dangerous operations (file-system writes outside temp, network, etc.).
* Captured ``stdout``, ``stderr``, and exceptions.

.. note::

   This sandbox is a **defense-in-depth** measure, not a hard security
   boundary.  Production deployments that accept untrusted code should
   run the executor inside a container or VM.
"""

from __future__ import annotations

import logging
import re
import subprocess
import sys
import tempfile
import textwrap
from dataclasses import dataclass

from src.config.settings import settings

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 10  # seconds

# Patterns that must NOT appear in user code.
_DANGEROUS_PATTERNS: list[re.Pattern[str]] = [
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


@dataclass
class CodeResult:
    """Outcome of a sandboxed code execution."""

    success: bool
    output: str = ""
    error: str = ""


def _check_dangerous(code: str) -> str | None:
    """Return a rejection reason if *code* contains a blocked pattern."""
    for pattern in _DANGEROUS_PATTERNS:
        match = pattern.search(code)
        if match:
            return f"Blocked: code contains disallowed pattern '{match.group()}'"
    return None


def execute_code(
    code: str,
    *,
    timeout_seconds: int | None = None,
) -> CodeResult:
    """Execute *code* in a subprocess sandbox.

    Args:
        code: Python source code to execute.
        timeout_seconds: Maximum wall-clock time.  Falls back to
            ``settings.code_execution_timeout_seconds`` then
            ``DEFAULT_TIMEOUT``.

    Returns:
        A :class:`CodeResult` with captured output and errors.
    """
    timeout = (
        timeout_seconds
        or getattr(settings, "code_execution_timeout_seconds", None)
        or DEFAULT_TIMEOUT
    )

    if not code or not code.strip():
        logger.warning("Empty code supplied — skipping execution")
        return CodeResult(success=False, error="No code provided")

    # ── Static safety check ───────────────────────────────────────
    reason = _check_dangerous(code)
    if reason:
        logger.warning("Code rejected: %s", reason)
        return CodeResult(success=False, error=reason)

    # ── Write code to a temp file and run in a subprocess ─────────
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".py",
            delete=False,
            prefix="analyst_",
        ) as tmp:
            tmp.write(code)
            tmp_path = tmp.name

        logger.debug(
            "Executing code (%d chars) in subprocess, timeout=%ds",
            len(code),
            timeout,
        )

        result = subprocess.run(
            [sys.executable, tmp_path],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=tempfile.gettempdir(),
        )

        stdout = result.stdout.strip()
        stderr = result.stderr.strip()

        if result.returncode == 0:
            output = stdout
            if stderr:
                output += f"\n[stderr]\n{stderr}"
            logger.info("Code executed successfully: %d chars output", len(output))
            return CodeResult(success=True, output=output, error="")

        # Non-zero exit — treat as error
        error_msg = stderr or f"Process exited with code {result.returncode}"
        logger.error("Code execution failed (rc=%d): %s", result.returncode, error_msg)
        return CodeResult(success=False, output=stdout, error=error_msg)

    except subprocess.TimeoutExpired:
        logger.warning("Code execution timed out after %ds", timeout)
        return CodeResult(
            success=False,
            error=f"Execution timed out after {timeout} seconds",
        )
    except Exception as exc:
        logger.error("Code execution error: %s", exc)
        return CodeResult(success=False, error=str(exc))
