"""Generate candidate-facing feedback using Gemini."""

from __future__ import annotations

from shared.llm.gemini import generate_text

MODEL = "gemini-3-flash-preview"

PROMPT_TEMPLATE = """\
You are an interview coach giving feedback to a candidate after they answered a technical question.

Question:
{question}

Candidate's answer:
{answer}

Evaluation:
- Score: {score}
- Strengths: {strengths}
- Weaknesses: {weaknesses}
- Missing points: {missing_points}

Write a short, constructive feedback paragraph (3–5 sentences). Requirements:
- Reference specifics from the candidate's answer — no generic praise or criticism.
- Mention what they did well first.
- Then note what was missed or incorrect.
- End with one concrete suggestion for improvement.
- Keep the tone encouraging and professional.
"""


def generate_feedback(question: str, answer: str, evaluation: dict) -> str:
    prompt = PROMPT_TEMPLATE.format(
        question=question,
        answer=answer,
        score=evaluation.get("score", 0.0),
        strengths=", ".join(evaluation.get("strengths", [])) or "None",
        weaknesses=", ".join(evaluation.get("weaknesses", [])) or "None",
        missing_points=", ".join(evaluation.get("missing_points", [])) or "None",
    )

    return generate_text(prompt=prompt, model=MODEL)