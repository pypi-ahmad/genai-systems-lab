"""Helpers for persisted cross-run session memory."""

from __future__ import annotations

import json
import logging
import re
from collections.abc import Sequence

MAX_SESSION_MEMORY_ENTRIES = 12
SESSION_CONTEXT_WINDOW = 4
SESSION_PREVIEW_WINDOW = 5
MAX_INPUT_PREVIEW_CHARS = 220
MAX_OUTPUT_PREVIEW_CHARS = 320
MAX_ENTRY_CHARS = 620

_LOGGER = logging.getLogger(__name__)


def deserialize_session_memory_entries(raw: str | None) -> list[str]:
    if not raw:
        return []

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        # Don't crash the request on data drift, but surface the corruption
        # so silent loss of memory entries shows up in logs.
        _LOGGER.warning(
            "failed to decode session memory entries json (len=%d): %s",
            len(raw),
            exc,
        )
        return []

    if not isinstance(data, list):
        return []

    cleaned: list[str] = []
    for item in data:
        if not isinstance(item, str):
            continue
        normalized = _normalize_whitespace(item)
        if normalized:
            cleaned.append(_truncate(normalized, MAX_ENTRY_CHARS))

    return cleaned[-MAX_SESSION_MEMORY_ENTRIES:]


def serialize_session_memory_entries(entries: Sequence[str] | None) -> str:
    return json.dumps(_sanitize_entries(entries), ensure_ascii=True)


def build_session_prompt(input_text: str, entries: Sequence[str]) -> tuple[str, bool, list[str]]:
    cleaned_input = input_text.strip()
    recent_entries = preview_session_memory_entries(entries, limit=SESSION_CONTEXT_WINDOW)
    if not cleaned_input or not recent_entries or cleaned_input.lower().startswith("previous context:"):
        return input_text, False, recent_entries

    context_block = "\n".join(f"- {entry}" for entry in recent_entries)
    prompt = f"Previous context:\n{context_block}\n\nCurrent request:\n{cleaned_input}"
    return prompt, True, recent_entries


def update_session_memory_entries(
    entries: Sequence[str],
    *,
    user_input: str,
    output_text: str,
) -> list[str]:
    cleaned = _sanitize_entries(entries)
    new_entry = _build_interaction_entry(user_input, output_text)
    if not new_entry:
        return cleaned[-MAX_SESSION_MEMORY_ENTRIES:]

    # Dedup against the *entire* window, not just the last two entries
    # (C-14 in the audit).  A user who asks the same question every third
    # turn previously filled the memory with near-duplicates, which then
    # got re-injected as "Previous context" into the next prompt.
    new_key = _dedupe_key(new_entry)
    existing_keys = {_dedupe_key(entry) for entry in cleaned}
    if new_key in existing_keys:
        return cleaned[-MAX_SESSION_MEMORY_ENTRIES:]

    return [*cleaned, new_entry][-MAX_SESSION_MEMORY_ENTRIES:]


def preview_session_memory_entries(entries: Sequence[str], *, limit: int = SESSION_PREVIEW_WINDOW) -> list[str]:
    cleaned = _sanitize_entries(entries)
    if limit <= 0:
        return []
    return cleaned[-limit:]


def _sanitize_entries(entries: Sequence[str] | None) -> list[str]:
    if not entries:
        return []

    cleaned: list[str] = []
    for item in entries:
        if not isinstance(item, str):
            continue
        normalized = _normalize_whitespace(item)
        if not normalized:
            continue
        truncated = _truncate(normalized, MAX_ENTRY_CHARS)
        if cleaned and _dedupe_key(cleaned[-1]) == _dedupe_key(truncated):
            continue
        cleaned.append(truncated)

    return cleaned[-MAX_SESSION_MEMORY_ENTRIES:]


def _build_interaction_entry(user_input: str, output_text: str) -> str:
    input_preview = _truncate(_normalize_whitespace(user_input), MAX_INPUT_PREVIEW_CHARS)
    output_preview = _truncate(_normalize_whitespace(output_text), MAX_OUTPUT_PREVIEW_CHARS)

    if not input_preview and not output_preview:
        return ""

    if input_preview and output_preview:
        return _truncate(f"User: {input_preview} | Agent: {output_preview}", MAX_ENTRY_CHARS)
    if input_preview:
        return _truncate(f"User: {input_preview}", MAX_ENTRY_CHARS)
    return _truncate(f"Agent: {output_preview}", MAX_ENTRY_CHARS)


def _normalize_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def _truncate(value: str, limit: int) -> str:
    if len(value) <= limit:
        return value
    return value[: max(0, limit - 3)].rstrip() + "..."


def _dedupe_key(value: str) -> str:
    return _normalize_whitespace(value).lower()