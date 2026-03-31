"""Execution entry point for the Hiring Decision Crew."""

import json

from app.crew import build_crew
from shared.config import set_byok_api_key, reset_byok_api_key

STEP_LABELS = [
    "Resume Summary",
    "Technical Evaluation",
    "Behavioral Evaluation",
    "Final Decision",
    "Bias Audit",
]


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
    """Run candidate evaluation on resume text and return structured output."""
    token = set_byok_api_key(api_key)
    try:
        crew = build_crew(input, "", verbose=False)
        result = crew.kickoff()
        task_outputs = result.tasks_output if hasattr(result, "tasks_output") else []
        steps = {}
        for i, label in enumerate(STEP_LABELS):
            if i < len(task_outputs):
                steps[label] = _parse_json(task_outputs[i].raw) or task_outputs[i].raw
            else:
                steps[label] = None
        return {"steps": steps}
    finally:
        reset_byok_api_key(token)
