from __future__ import annotations

from shared.llm.gemini import generate_structured

MODEL = "gemini-3.1-pro-preview"

RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "analyses": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "condition": {
                        "type": "string",
                        "description": "Name of the condition being analyzed.",
                    },
                    "reasoning": {
                        "type": "string",
                        "description": "Explanation of relevance, matching symptoms, and missing symptoms.",
                    },
                },
                "required": ["condition", "reasoning"],
            },
        },
    },
    "required": ["analyses"],
}

PROMPT_TEMPLATE = """\
You are a clinical reasoning assistant.

Given the patient information and a list of candidate conditions, analyze each condition.
For every condition you MUST:
1. Explain why it is relevant to this patient.
2. List which of the patient's symptoms match the condition.
3. List which typical symptoms of the condition are NOT reported by the patient.

Be concise and factual. Do not speculate beyond the provided data.

Patient information:
{patient_info}

Candidate conditions:
{conditions}
"""


def _format_patient(patient_info: dict) -> str:
    parts = []
    if patient_info.get("symptoms"):
        parts.append(f"Symptoms: {', '.join(patient_info['symptoms'])}")
    if patient_info.get("age"):
        parts.append(f"Age: {patient_info['age']}")
    if patient_info.get("gender"):
        parts.append(f"Gender: {patient_info['gender']}")
    if patient_info.get("duration"):
        parts.append(f"Duration: {patient_info['duration']}")
    return "\n".join(parts) if parts else "No patient details provided."


def _format_conditions(conditions: list[dict]) -> str:
    lines = []
    for c in conditions:
        symptoms = ", ".join(c.get("symptoms", []))
        lines.append(f"- {c['name']}: symptoms=[{symptoms}]")
    return "\n".join(lines)


def analyze_conditions(patient_info: dict, conditions: list[dict]) -> list[dict]:
    """Analyze candidate conditions against patient info using LLM reasoning."""
    prompt = PROMPT_TEMPLATE.format(
        patient_info=_format_patient(patient_info),
        conditions=_format_conditions(conditions),
    )

    result = generate_structured(prompt=prompt, model=MODEL, schema=RESPONSE_SCHEMA)
    return result.get("analyses", [])