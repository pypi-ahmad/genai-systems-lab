def chunk_text(text: str, max_words: int = 500, min_words: int = 30) -> list[str]:
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if not paragraphs:
        return []

    chunks = []
    current = []
    current_len = 0

    for para in paragraphs:
        word_count = len(para.split())
        if current and current_len + word_count > max_words:
            chunks.append("\n\n".join(current))
            current = [para]
            current_len = word_count
        else:
            current.append(para)
            current_len += word_count

    if current:
        # Merge tiny trailing chunk into previous
        tail = "\n\n".join(current)
        if chunks and current_len < min_words:
            chunks[-1] = chunks[-1] + "\n\n" + tail
        else:
            chunks.append(tail)

    return chunks