"""Adjust interview difficulty based on candidate performance."""

from __future__ import annotations

LEVELS = ("easy", "medium", "hard")

_LEVEL_INDEX = {level: i for i, level in enumerate(LEVELS)}

INCREASE_THRESHOLD = 0.75
DECREASE_THRESHOLD = 0.4


def adjust_difficulty(current: str, score: float) -> str:
    if current not in _LEVEL_INDEX:
        raise ValueError(f"current must be one of {LEVELS}")

    index = _LEVEL_INDEX[current]

    if score > INCREASE_THRESHOLD:
        index = min(index + 1, len(LEVELS) - 1)
    elif score < DECREASE_THRESHOLD:
        index = max(index - 1, 0)

    return LEVELS[index]