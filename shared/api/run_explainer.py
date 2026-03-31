"""Helpers for generating explainability summaries for saved runs."""

from __future__ import annotations

import json
from typing import Any

from shared.llm import generate_structured

MODEL = "gemini-3.1-pro-preview"
MAX_INPUT_CHARS = 2_500
MAX_OUTPUT_CHARS = 5_000
MAX_MEMORY_ENTRIES = 60
MAX_TIMELINE_ENTRIES = 120
MAX_ENTRY_CHARS = 220

EXPLANATION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "steps_taken": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "step": {"type": "string"},
                    "what_happened": {"type": "string"},
                    "why_it_mattered": {"type": "string"},
                },
                "required": ["step", "what_happened", "why_it_mattered"],
            },
        },
        "key_decisions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "decision": {"type": "string"},
                    "reason": {"type": "string"},
                },
                "required": ["decision", "reason"],
            },
        },
        "final_reasoning": {"type": "string"},
        "final_outcome": {"type": "string"},
    },
    "required": ["steps_taken", "key_decisions", "final_reasoning", "final_outcome"],
}

SYSTEM_PROMPT = (
    "You explain how an AI system worked using only saved run artifacts. "
    "Do not invent hidden reasoning, missing tool calls, or extra facts. "
    "Summarize only what is supported by the run input, output, memory, and timeline.\n\n"
    "Style rules:\n"
    "- Be concise and concrete.\n"
    "- Prefer plain product language over research language.\n"
    "- Keep step summaries short and readable.\n"
    "- Keep decision summaries grounded in observable artifacts.\n"
    "- If evidence is limited, say only what is directly supported."
)


def _truncate(value: str, limit: int) -> str:
    cleaned = value.strip()
    if len(cleaned) <= limit:
        return cleaned
    return f"{cleaned[: limit - 3].rstrip()}..."


def _format_input(input_text: str) -> str:
    return _truncate(input_text or "", MAX_INPUT_CHARS) or "(empty input)"


def _format_output(output_text: str) -> str:
    cleaned = (output_text or "").strip()
    if not cleaned:
        return "(empty output)"

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        return _truncate(cleaned, MAX_OUTPUT_CHARS)

    return _truncate(json.dumps(parsed, indent=2), MAX_OUTPUT_CHARS)


def _format_memory(memory: list[dict[str, str]]) -> str:
    if not memory:
        return "- No saved memory entries."

    lines: list[str] = []
    for index, entry in enumerate(memory[:MAX_MEMORY_ENTRIES], start=1):
        entry_type = entry.get("type", "observation")
        step = entry.get("step", "Unknown step")
        content = _truncate(entry.get("content", ""), MAX_ENTRY_CHARS) or "(empty)"
        lines.append(f"{index}. [{entry_type}] {step}: {content}")

    if len(memory) > MAX_MEMORY_ENTRIES:
        lines.append(f"... {len(memory) - MAX_MEMORY_ENTRIES} additional memory entries omitted.")

    return "\n".join(lines)


def _format_timeline(timeline: list[dict[str, Any]]) -> str:
    if not timeline:
        return "- No saved timeline entries."

    lines: list[str] = []
    for index, entry in enumerate(timeline[:MAX_TIMELINE_ENTRIES], start=1):
        timestamp = float(entry.get("timestamp", 0.0) or 0.0)
        step = str(entry.get("step", "unknown"))
        event = str(entry.get("event", "unknown"))
        data = _truncate(str(entry.get("data", "")), MAX_ENTRY_CHARS) or "(empty)"
        lines.append(f"{index}. +{timestamp:.2f}s | {step} | {event} | {data}")

    if len(timeline) > MAX_TIMELINE_ENTRIES:
        lines.append(f"... {len(timeline) - MAX_TIMELINE_ENTRIES} additional timeline entries omitted.")

    return "\n".join(lines)


def build_run_explanation(
    *,
    project: str,
    input_text: str,
    output_text: str,
    memory: list[dict[str, str]],
    timeline: list[dict[str, Any]],
) -> dict[str, Any]:
    """Generate a concise structured explanation for one saved run."""

    prompt = (
        f"{SYSTEM_PROMPT}\n\n"
        f"## Project\n{project}\n\n"
        f"## Original Input\n{_format_input(input_text)}\n\n"
        f"## Final Output\n{_format_output(output_text)}\n\n"
        f"## Saved Memory\n{_format_memory(memory)}\n\n"
        f"## Saved Timeline\n{_format_timeline(timeline)}\n\n"
        "Explain how the system worked."
    )

    return generate_structured(prompt=prompt, model=MODEL, schema=EXPLANATION_SCHEMA)