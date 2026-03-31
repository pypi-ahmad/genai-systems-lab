"""Generate interview questions using Gemini."""

from __future__ import annotations

from shared.llm.gemini import generate_text

MODEL = "gemini-3.1-pro-preview"

DIFFICULTY_GUIDANCE = {
    "easy": (
        "Ask a foundational question that tests basic understanding. "
        "Focus on definitions, simple use cases, or straightforward concepts. "
        "A junior candidate with 0-1 years of experience should be able to answer."
    ),
    "medium": (
        "Ask a question that tests applied understanding. "
        "Require the candidate to explain trade-offs, compare approaches, or walk through a realistic scenario. "
        "A mid-level candidate with 2-4 years of experience should find this challenging but fair."
    ),
    "hard": (
        "Ask a question that tests deep expertise. "
        "Require the candidate to reason about edge cases, performance implications, system-level trade-offs, or design decisions under constraints. "
        "A senior candidate with 5+ years of experience should need to think carefully."
    ),
}

PROMPT_TEMPLATE = """\
You are a technical interviewer conducting a {topic} interview.

Difficulty level: {difficulty}
{difficulty_guidance}

{history_block}

Generate exactly ONE interview question. Requirements:
- The question must be specific and precise, not vague or overly broad.
- It must have a concrete, verifiable answer — avoid opinion-based or open-ended discussion prompts.
- Do not repeat or closely rephrase any previously asked question.
- Output ONLY the question text. No preamble, numbering, or explanation.
"""


def _build_history_block(history: list[str]) -> str:
    if not history:
        return "No questions have been asked yet."
    formatted = "\n".join(f"- {q}" for q in history)
    return f"Previously asked questions (do NOT repeat these):\n{formatted}"


def generate_question(topic: str, difficulty: str, history: list[str] | None = None) -> str:
    if difficulty not in DIFFICULTY_GUIDANCE:
        raise ValueError(f"difficulty must be one of {tuple(DIFFICULTY_GUIDANCE)}")

    prompt = PROMPT_TEMPLATE.format(
        topic=topic,
        difficulty=difficulty,
        difficulty_guidance=DIFFICULTY_GUIDANCE[difficulty],
        history_block=_build_history_block(history or []),
    )

    return generate_text(prompt=prompt, model=MODEL)