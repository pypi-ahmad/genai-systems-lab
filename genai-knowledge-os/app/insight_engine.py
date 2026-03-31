from shared.llm.gemini import generate_text


MODEL = "gemini-3.1-pro-preview"

PROMPT_TEMPLATE = """You are an insight engine analyzing a personal knowledge base. You are given multiple text chunks from different documents.

Your job is NOT to summarize. Instead:
1. Identify non-obvious connections between the chunks.
2. Highlight recurring patterns or themes across documents.
3. Surface contradictions or tensions between ideas.
4. Generate original observations that the reader might not notice on their own.

Be specific. Reference the content directly. Avoid generic statements.

Chunks:
{chunks}

Insights:"""


def generate_insights(chunks: list[str]) -> str:
    chunks = [c.strip() for c in chunks if c.strip()]
    if not chunks:
        return ""
    numbered = "\n\n".join(
        f"[Chunk {i + 1}]\n{text}" for i, text in enumerate(chunks)
    )
    prompt = PROMPT_TEMPLATE.format(chunks=numbered)
    return generate_text(prompt, model=MODEL)