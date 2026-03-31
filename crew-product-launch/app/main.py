"""Execution entry point for the Product Launch Strategy Crew."""

import json

from app.crew import build_crew
from shared.config import set_byok_api_key, reset_byok_api_key

JSON_KEYS = ["market", "personas", "positioning", "gtm"]


def _parse_json(raw: str) -> dict | list | None:
    text = raw.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines).strip()
    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return None


def run(input: str, api_key: str) -> dict:
    """Run the product launch strategy pipeline and return structured output."""
    token = set_byok_api_key(api_key)
    try:
        crew = build_crew(input, verbose=False)
        result = crew.kickoff()
        task_outputs = result.tasks_output if hasattr(result, "tasks_output") else []
        combined = {}
        for i, key in enumerate(JSON_KEYS):
            if i < len(task_outputs):
                parsed = _parse_json(task_outputs[i].raw)
                combined[key] = parsed if parsed is not None else task_outputs[i].raw
            else:
                combined[key] = None
        return {"product": input, **combined}
    finally:
        reset_byok_api_key(token)
