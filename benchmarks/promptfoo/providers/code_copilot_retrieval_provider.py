from __future__ import annotations

import builtins
import sys
import time
from pathlib import Path
from typing import Any

_PROVIDER_DIR = str(Path(__file__).resolve().parent)
if _PROVIDER_DIR not in sys.path:
    sys.path.insert(0, _PROVIDER_DIR)

from project_utils import load_project_module, repo_relative_path, request_overrides, resolve_path


def _index_state() -> dict[str, str | None]:
    state = getattr(builtins, "_promptfoo_code_copilot_index_state", None)
    if isinstance(state, dict):
        return state

    state = {"path": None}
    setattr(builtins, "_promptfoo_code_copilot_index_state", state)
    return state


def _ensure_indexed(module: Any, codebase_path: str) -> None:
    state = _index_state()
    if state.get("path") == codebase_path:
        return

    module.index_codebase(codebase_path)
    state["path"] = codebase_path


def _normalize_chunks(chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "text": str(chunk.get("text", "")),
            "path": repo_relative_path(chunk.get("path", "")),
        }
        for chunk in chunks
    ]


def call_api(prompt: str, options: dict, context: dict) -> dict:
    config = options.get("config", {})
    vars_payload = context.get("vars", {}) or options.get("vars", {}) or {}
    query = prompt.strip() or str(vars_payload.get("query") or "").strip()
    codebase_path = str(resolve_path(vars_payload.get("codebase_path") or config.get("codebase_path") or "shared"))

    if not query:
        return {"error": "Promptfoo rendered an empty retrieval query."}

    try:
        start = time.perf_counter()
        with request_overrides(config):
            module = load_project_module("genai-code-copilot")
            _ensure_indexed(module, codebase_path)
            chunks = _normalize_chunks(module.retrieve(query))
            context_text = module.build_context(chunks)
        elapsed_ms = (time.perf_counter() - start) * 1000

        return {
            "output": context_text,
            "latencyMs": round(elapsed_ms, 2),
            "metadata": {
                "chunk_count": len(chunks),
                "codebase_path": repo_relative_path(codebase_path),
            },
        }
    except Exception as exc:
        return {"error": str(exc)}