from __future__ import annotations

from typing import TypedDict


MAX_CONTEXT_CHARS = 8000
MAX_CHUNK_CHARS = 2000


class ContextChunk(TypedDict, total=False):
	text: str
	path: str


def _normalize_chunk_text(text: str, max_chars: int) -> str:
	normalized = text.strip()
	if max_chars <= 0:
		return ""
	if max_chars <= 3:
		return normalized[:max_chars]
	if len(normalized) <= max_chars:
		return normalized
	return normalized[: max_chars - 3].rstrip() + "..."


def _format_chunk(path: str, text: str) -> str:
	return f"[File: {path}]\n{text}"


def build_context(chunks: list[dict]) -> str:
	if not chunks:
		return ""

	formatted_sections: list[str] = []
	current_size = 0

	for chunk in chunks:
		path = str(chunk.get("path", "")).strip() or "unknown"
		text = str(chunk.get("text", "")).strip()

		if not text:
			continue

		section = _format_chunk(
			path=path,
			text=_normalize_chunk_text(text, MAX_CHUNK_CHARS),
		)

		section_size = len(section)
		separator_size = 2 if formatted_sections else 0

		if current_size + separator_size + section_size > MAX_CONTEXT_CHARS:
			remaining = MAX_CONTEXT_CHARS - current_size - separator_size
			if remaining <= len(f"[File: {path}]\n..."):
				break

			available_text_chars = max(0, remaining - len(f"[File: {path}]\n"))
			truncated_text = _normalize_chunk_text(text, available_text_chars)
			section = _format_chunk(path=path, text=truncated_text)
			section_size = len(section)

		formatted_sections.append(section)
		current_size += separator_size + section_size

		if current_size >= MAX_CONTEXT_CHARS:
			break

	return "\n\n".join(formatted_sections)


__all__ = ["ContextChunk", "MAX_CHUNK_CHARS", "MAX_CONTEXT_CHARS", "build_context"]
