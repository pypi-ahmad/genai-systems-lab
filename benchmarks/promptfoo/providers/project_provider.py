"""Promptfoo custom Python provider for genai-systems-lab project workflows."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure the repo root is on the path so shared imports resolve.
_PROVIDER_DIR = str(Path(__file__).resolve().parent)
_REPO_ROOT = str(Path(__file__).resolve().parents[3])
for candidate in (_PROVIDER_DIR, _REPO_ROOT):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from shared.api.runner import run_project  # noqa: E402
from project_utils import extract_primary_text, parse_output_payload, request_overrides  # noqa: E402


def call_api(prompt: str, options: dict, context: dict) -> dict:
    config = options.get("config", {})
    project = config.get("project", "genai-research-system")
    input_text = prompt.strip() or str(options.get("vars", {}).get("input") or context.get("vars", {}).get("input") or "").strip()

    if not input_text:
        return {"error": "Promptfoo rendered an empty workflow input."}

    try:
        with request_overrides(config) as runtime:
            result = run_project(project, input_text, api_key=str(runtime["api_key"] or ""))

        raw_output = parse_output_payload(result.output)
        return {
            "output": {
                "text": extract_primary_text(raw_output),
                "raw": raw_output,
                "project": result.project,
                "latency_ms": result.elapsed_ms,
            },
            "latencyMs": result.elapsed_ms,
            "metadata": {
                "project": result.project,
                "trace_id": result.trace_id,
            },
        }
    except Exception as exc:
        return {"error": str(exc)}
