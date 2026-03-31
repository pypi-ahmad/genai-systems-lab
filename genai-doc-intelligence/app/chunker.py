import re

DEFAULT_MIN_WORDS = 300
DEFAULT_MAX_WORDS = 500

_HEADING_RE = re.compile(r'^#{1,6}\s+')


def _split_sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]


def _is_heading(paragraph: str) -> bool:
    return bool(_HEADING_RE.match(paragraph))


def _split_sections(text: str) -> list[dict]:
    paragraphs = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]
    sections: list[dict] = []
    current_heading: str | None = None
    current_paragraphs: list[str] = []

    for para in paragraphs:
        if _is_heading(para):
            if current_heading is not None or current_paragraphs:
                sections.append({"heading": current_heading, "body": current_paragraphs})
                current_paragraphs = []
            current_heading = para
        else:
            current_paragraphs.append(para)

    if current_paragraphs or current_heading:
        sections.append({"heading": current_heading, "body": current_paragraphs})

    if not sections and paragraphs:
        sections.append({"heading": None, "body": paragraphs})

    return sections


def _chunk_sentences(
    sentences: list[str],
    heading: str | None,
    max_words: int,
) -> list[str]:
    chunks: list[str] = []
    current: list[str] = []
    current_word_count = 0

    for sentence in sentences:
        sentence_words = len(sentence.split())
        if current_word_count + sentence_words > max_words and current:
            prefix = f"{heading}\n\n" if heading else ""
            chunks.append(prefix + ' '.join(current))
            current = []
            current_word_count = 0
        current.append(sentence)
        current_word_count += sentence_words

    if current:
        prefix = f"{heading}\n\n" if heading else ""
        chunks.append(prefix + ' '.join(current))

    return chunks


def chunk_document(
    text: str,
    min_words: int = DEFAULT_MIN_WORDS,
    max_words: int = DEFAULT_MAX_WORDS,
) -> list[str]:
    if not text or not text.strip():
        return []

    sections = _split_sections(text)

    chunks: list[str] = []
    for section in sections:
        sentences: list[str] = []
        for para in section["body"]:
            sentences.extend(_split_sentences(para))

        if not sentences:
            if section["heading"]:
                chunks.append(section["heading"])
            continue

        section_chunks = _chunk_sentences(sentences, section["heading"], max_words)
        chunks.extend(section_chunks)

    # Merge a short trailing chunk into the previous one if possible,
    # but only if they share the same heading (same section).
    if len(chunks) >= 2:
        last_wc = len(chunks[-1].split())
        prev_wc = len(chunks[-2].split())
        last_heading = chunks[-1].split('\n')[0] if _HEADING_RE.match(chunks[-1]) else None
        prev_heading = chunks[-2].split('\n')[0] if _HEADING_RE.match(chunks[-2]) else None
        if last_wc < min_words and prev_wc + last_wc <= max_words and last_heading == prev_heading:
            chunks[-2] = chunks[-2] + ' ' + chunks[-1]
            chunks.pop()

    return chunks
