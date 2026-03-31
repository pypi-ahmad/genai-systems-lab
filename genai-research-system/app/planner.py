"""Planning utilities for research task generation."""

from __future__ import annotations

import json

from google.genai import types

from shared.llm.gemini import _get_client


PLANNER_MODEL = "gemini-3.1-pro-preview"


def create_plan(query: str) -> list[str]:
	cleaned_query = query.strip()
	if not cleaned_query:
		raise ValueError("Query must not be empty.")

	response = _get_client().models.generate_content(
		model=PLANNER_MODEL,
		contents=_build_prompt(cleaned_query),
		config=types.GenerateContentConfig(
			temperature=0.2,
			responseMimeType="application/json",
			responseSchema=list[str],
		),
	)
	return _parse_tasks(response.text)


def _build_prompt(query: str) -> str:
	return f"""
Break the research query into a structured list of 3 to 6 research tasks.

Requirements:
- Return only a JSON array of strings.
- Each task must be clear, specific, and directly executable.
- Avoid vague tasks such as \"research the topic\" or \"analyze more deeply\".
- Make each task focused on a distinct piece of the research process.

User query:
{query}
""".strip()


def _parse_tasks(response_text: str | None) -> list[str]:
	if not response_text:
		raise ValueError("Planner returned an empty response.")

	try:
		data = json.loads(response_text)
	except json.JSONDecodeError:
		data = [line.strip("- *\t ") for line in response_text.splitlines() if line.strip()]

	if not isinstance(data, list):
		raise ValueError("Planner response must be a list of tasks.")

	tasks = [str(item).strip() for item in data if str(item).strip()]
	if not 3 <= len(tasks) <= 6:
		raise ValueError("Planner must return between 3 and 6 tasks.")

	return tasks
