from shared.llm.gemini import generate_structured

MODEL = "gemini-3.1-pro-preview"

EXTRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "key_points": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Main facts, conclusions, or takeaways from the text.",
        },
        "important_clauses": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Significant clauses, conditions, or stipulations found in the text.",
        },
        "risks": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Potential risks, warnings, or concerns mentioned in the text. Empty list if none.",
        },
    },
    "required": ["key_points", "important_clauses", "risks"],
}

PROMPT_TEMPLATE = """\
You are a document information extractor.
Given the text below, extract ONLY information that is explicitly stated.
Do NOT infer, assume, or hallucinate any details.

Extract the following:
- "key_points": the main facts, conclusions, or takeaways.
- "important_clauses": significant clauses, conditions, or stipulations.
- "risks": any potential risks, warnings, or concerns. Return an empty list if none are mentioned.

Text:
{text}
"""


def extract_key_information(text: str) -> dict:
    if not text or not text.strip():
        return {"key_points": [], "important_clauses": [], "risks": []}
    prompt = PROMPT_TEMPLATE.format(text=text)
    return generate_structured(prompt=prompt, model=MODEL, schema=EXTRACTION_SCHEMA)
