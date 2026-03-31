"""Execution entry point for the Content Creation Pipeline."""

from app.crew import build_crew
from shared.config import set_byok_api_key, reset_byok_api_key

STEP_LABELS = [
    "Research Summary",
    "Article Draft",
    "Edited Version",
    "SEO Output",
]
def run(input: str, api_key: str) -> dict:
    """Run the content creation pipeline and return structured output."""
    token = set_byok_api_key(api_key)
    try:
        crew = build_crew(input)
        crew.verbose = False
        result = crew.kickoff(inputs={"topic": input})
        task_outputs = result.tasks_output if hasattr(result, "tasks_output") else []
        steps = {}
        for i, label in enumerate(STEP_LABELS):
            steps[label] = task_outputs[i].raw if i < len(task_outputs) else None
        return {"topic": input, "steps": steps}
    finally:
        reset_byok_api_key(token)
