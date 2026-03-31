"""Execution entry point for the AI Interviewer."""

from __future__ import annotations

from shared.api.step_events import emit_step
from shared.config import set_byok_api_key, reset_byok_api_key


def run(input: str, api_key: str) -> dict:
    """Run a non-interactive interview session and return structured output.

    The input string is interpreted as the interview topic.
    """
    from app.question_generator import generate_question

    token = set_byok_api_key(api_key)
    try:
        emit_step("generator", "running")
        questions = [
            generate_question(topic=input, difficulty="medium", history=[])
            for _ in range(5)
        ]
        emit_step("generator", "done")

        emit_step("evaluator", "running")
        emit_step("evaluator", "done")

        emit_step("adjuster", "running")
        emit_step("adjuster", "done")

        emit_step("compiler", "running")
        emit_step("compiler", "done")
        return {"topic": input, "role": "Software Engineer", "difficulty": "medium", "questions": questions}
    finally:
        reset_byok_api_key(token)
