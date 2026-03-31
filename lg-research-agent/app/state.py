from __future__ import annotations

from typing import TypedDict


class ResearchState(TypedDict, total=False):
	query: str
	plan: list[str]
	findings: list[str]
	critique: str
	report: str
	success: bool


def initial_state(query: str) -> ResearchState:
	return {
		"query": query.strip(),
		"plan": [],
		"findings": [],
		"critique": "",
		"report": "",
		"success": False,
	}
