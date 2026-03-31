import re


def attach_citations(answer: str, chunks: list[dict]) -> str:
    if not answer or not chunks:
        return answer

    source_map: dict[int, str] = {}
    for i, chunk in enumerate(chunks, 1):
        meta = chunk.get("metadata", {})
        source = meta.get("source", "unknown")
        chunk_id = meta.get("chunk_id", i - 1)
        source_map[i] = f"[Source: {source}, chunk_id={chunk_id}]"

    def _replace_marker(match: re.Match) -> str:
        n = int(match.group(1))
        return source_map.get(n, match.group(0))

    cited = re.sub(r"\[Source (\d+)\]", _replace_marker, answer)

    # Build references section from sources actually cited in the answer
    used = sorted(
        n for n in source_map if re.search(rf"\[Source: .+?, chunk_id=.+?\]", cited)
    )
    if not used:
        used = sorted(source_map)

    references = []
    for n in used:
        meta = chunks[n - 1].get("metadata", {})
        source = meta.get("source", "unknown")
        chunk_id = meta.get("chunk_id", n - 1)
        references.append(f"  [{n}] {source} (chunk {chunk_id})")

    if references:
        cited += "\n\nReferences:\n" + "\n".join(references)

    return cited
