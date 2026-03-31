from shared.llm.gemini import generate_text

QA_MODEL = "gemini-3.1-pro-preview"


def _build_prompt(query: str, chunks: list[dict]) -> str:
    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        source = chunk.get("metadata", {}).get("source", "unknown")
        context_parts.append(f"[Source {i}: {source}]\n{chunk['text']}")
    context_block = "\n\n".join(context_parts)

    return f"""You are a document question-answering assistant.

Answer the user's question using ONLY the provided document chunks below.
Do NOT use any knowledge outside these chunks. If the chunks do not contain enough information to answer, say so explicitly.

When making a claim, cite the source using [Source N] notation.

User question:
{query}

Document chunks:
{context_block}

Answer:"""


def answer_query(query: str, chunks: list[dict]) -> str:
    if not chunks:
        return "No relevant document chunks were provided. Unable to answer the question."
    prompt = _build_prompt(query, chunks)
    return generate_text(prompt, model=QA_MODEL)
