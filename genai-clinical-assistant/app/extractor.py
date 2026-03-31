from __future__ import annotations

from shared.llm.gemini import generate_structured

MODEL = "gemini-3.1-pro-preview"

EXTRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "symptoms": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of symptoms mentioned by the patient.",
        },
        "duration": {
            "type": "string",
            "description": "How long the symptoms have lasted, if mentioned.",
        },
        "age": {
            "type": "integer",
            "description": "Patient age in years, if mentioned.",
        },
        "gender": {
            "type": "string",
            "description": "Patient gender, if mentioned.",
        },
    },
    "required": ["symptoms"],
}

PROMPT_TEMPLATE = """\
You are a medical information extractor.
Given the patient description below, extract ONLY the information that is explicitly stated.
Do NOT infer, assume, or hallucinate any details.

Rules:
- "symptoms": list every symptom the patient mentions. If none are clear, return an empty list.
- "duration": include only if the patient states how long symptoms have lasted. Omit the field otherwise.
- "age": include only if a numeric age is mentioned. Omit the field otherwise.
- "gender": include only if gender is explicitly stated. Omit the field otherwise.

Patient description:
{text}
"""


def extract_patient_info(text: str) -> dict:
    """Extract structured patient information from free-text input."""
    prompt = PROMPT_TEMPLATE.format(text=text)
    result = generate_structured(prompt=prompt, model=MODEL, schema=EXTRACTION_SCHEMA)

    # Guarantee symptoms is always a list
    if not isinstance(result.get("symptoms"), list):
        result["symptoms"] = []

    # Strip fields the model returned as empty/null to avoid hallucinated blanks
    for optional_field in ("duration", "age", "gender"):
        value = result.get(optional_field)
        if value is None or value == "" or value == 0:
            result.pop(optional_field, None)

    return result