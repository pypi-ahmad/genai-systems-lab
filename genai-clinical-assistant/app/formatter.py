from __future__ import annotations

from shared.llm.gemini import generate_text

MODEL = "gemini-3-flash-preview"

DISCLAIMER = "\n\n⚠️ Disclaimer: This is not medical advice. Consult a qualified healthcare professional."

PROMPT_TEMPLATE = """\
You are a clinical report formatter.

Given a patient query and a list of analyzed conditions with confidence scores, produce a clear, \
well-organized clinical summary using the following structure:

1. **Summary** – A brief overview of the patient's reported symptoms.
2. **Top Conditions** – A ranked list of the most likely conditions.
3. **Explanation** – For each condition, summarize the reasoning and which symptoms matched or were absent.
4. **Confidence Levels** – For each condition, state the confidence score and label (Low / Medium / High).

Be concise. Do not add information beyond what is provided.

Patient query:
{query}

Analyzed conditions:
{conditions}
"""


def _format_condition_block(result: dict) -> str:
    name = result.get("condition", result.get("name", "Unknown"))
    confidence = result.get("confidence", "N/A")
    label = result.get("label", "N/A")
    reasoning = result.get("reasoning", "No reasoning provided.")
    return (
        f"- {name}\n"
        f"  Confidence: {confidence} ({label})\n"
        f"  Reasoning: {reasoning}"
    )


def format_output(query: str, results: list[dict]) -> str:
    """Format analyzed conditions into a human-readable clinical summary."""
    conditions_text = "\n".join(_format_condition_block(r) for r in results)
    prompt = PROMPT_TEMPLATE.format(query=query, conditions=conditions_text)
    summary = generate_text(prompt=prompt, model=MODEL)
    return summary + DISCLAIMER