from shared.llm.gemini import generate_text


MODEL = "gemini-3-flash-preview"

PROMPT_TEMPLATE = """Summarize the following text concisely. Preserve the key facts, ideas, and structure. Do not add information that is not present in the original text.

Text:
{text}

Summary:"""


def summarize(text: str) -> str:
    text = text.strip()
    if not text:
        return ""
    prompt = PROMPT_TEMPLATE.format(text=text)
    return generate_text(prompt, model=MODEL)