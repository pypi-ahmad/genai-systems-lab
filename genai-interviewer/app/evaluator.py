"""Evaluate candidate answers using Gemini."""

from __future__ import annotations

from shared.llm.gemini import generate_structured

MODEL = "gemini-3.1-pro-preview"

# ---------------------------------------------------------------------------
# Per-topic rubrics
# ---------------------------------------------------------------------------
# Each rubric defines the evaluation criteria the LLM must apply when scoring
# answers for that topic.  Topics are matched case-insensitively.  When no
# rubric matches, the DEFAULT_RUBRIC is used.
# ---------------------------------------------------------------------------

DEFAULT_RUBRIC = (
    "Evaluate the answer on:\n"
    "- Correctness: Are the stated facts accurate?\n"
    "- Completeness: Does the answer cover the key aspects of the question?\n"
    "- Depth: Does the answer go beyond surface-level recall?\n"
    "- Clarity: Is the explanation well-structured and easy to follow?"
)

RUBRICS: dict[str, str] = {
    "machine learning": (
        "Evaluate the answer on:\n"
        "- Correctness: Are algorithms, math, and terminology used accurately?\n"
        "- Completeness: Does the answer cover relevant concepts (e.g., model type, loss function, optimization)?\n"
        "- Depth: Does the candidate explain *why* an approach works, not just *what* it is?\n"
        "- Practical awareness: Does the answer mention trade-offs, failure modes, or real-world considerations?"
    ),
    "databases": (
        "Evaluate the answer on:\n"
        "- Correctness: Are SQL syntax, normalization rules, or indexing concepts accurate?\n"
        "- Completeness: Does the answer address schema design, query behavior, and edge cases where relevant?\n"
        "- Depth: Does the candidate explain trade-offs (e.g., read vs write performance, normalization vs denormalization)?\n"
        "- Practical awareness: Does the answer reference real-world usage patterns or scalability concerns?"
    ),
    "system design": (
        "Evaluate the answer on:\n"
        "- Correctness: Are the proposed components and interactions technically sound?\n"
        "- Completeness: Does the design cover the main building blocks (storage, compute, networking, caching)?\n"
        "- Depth: Does the candidate reason about scalability, fault tolerance, and bottlenecks?\n"
        "- Trade-off awareness: Does the answer discuss alternatives and justify choices?"
    ),
    "python": (
        "Evaluate the answer on:\n"
        "- Correctness: Are language semantics, built-in behavior, and library usage accurate?\n"
        "- Completeness: Does the answer cover the relevant mechanisms (e.g., GIL, decorators, generators) for the question?\n"
        "- Depth: Does the candidate explain underlying implementation details, not just API usage?\n"
        "- Best practices: Does the answer reflect idiomatic Python and awareness of common pitfalls?"
    ),
    "data structures": (
        "Evaluate the answer on:\n"
        "- Correctness: Are time/space complexities and algorithmic descriptions accurate?\n"
        "- Completeness: Does the answer cover the expected operations and their costs?\n"
        "- Depth: Does the candidate compare alternatives and explain when to use each?\n"
        "- Edge cases: Does the answer mention boundary conditions or degenerate inputs?"
    ),
}


def _get_rubric(topic: str) -> str:
    key = topic.lower().strip()
    for rubric_key, rubric in RUBRICS.items():
        if rubric_key in key or key in rubric_key:
            return rubric
    return DEFAULT_RUBRIC


RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "score": {
            "type": "number",
            "description": "Overall score from 0.0 (completely wrong) to 1.0 (perfect answer). Must reflect the strengths, weaknesses, and missing points — not be chosen arbitrarily.",
        },
        "strengths": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Specific things the candidate got right. Each item must quote or directly reference part of the candidate's answer.",
        },
        "weaknesses": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Specific things the candidate got wrong or explained poorly. Each item must reference what the candidate actually said.",
        },
        "missing_points": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Important concepts or details the candidate did not mention at all.",
        },
    },
    "required": ["score", "strengths", "weaknesses", "missing_points"],
}

PROMPT_TEMPLATE = """\
You are a technical interview evaluator. Your job is to assess how well the candidate answered the question.

Rubric for this topic:
{rubric}

Rules:
- Base your evaluation ONLY on the question and the candidate's answer below.
- Apply the rubric criteria above to determine strengths, weaknesses, and missing points.
- Do NOT introduce facts, concepts, or frameworks the candidate did not mention.
- Every strength must reference something the candidate actually said.
- Every weakness must reference something the candidate actually said that is incorrect or poorly explained.
- Every missing point must be something a correct answer would include that the candidate omitted entirely.
- If the answer is empty or completely off-topic, score 0.0 with no strengths.
- The score must be consistent with the number and severity of strengths, weaknesses, and missing points.

Question:
{question}

Candidate's answer:
{answer}
"""


def evaluate_answer(question: str, answer: str, topic: str = "") -> dict:
    rubric = _get_rubric(topic) if topic else DEFAULT_RUBRIC
    prompt = PROMPT_TEMPLATE.format(rubric=rubric, question=question, answer=answer)
    result = generate_structured(prompt=prompt, model=MODEL, schema=RESPONSE_SCHEMA)

    score = max(0.0, min(1.0, float(result.get("score", 0.0))))

    return {
        "score": score,
        "strengths": list(result.get("strengths", [])),
        "weaknesses": list(result.get("weaknesses", [])),
        "missing_points": list(result.get("missing_points", [])),
    }