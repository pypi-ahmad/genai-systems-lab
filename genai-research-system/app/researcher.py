"""Research execution utilities."""

from __future__ import annotations

from google.genai import types

from shared.llm.gemini import _get_client


RESEARCH_MODEL = "gemini-3.1-pro-preview"


def research_task(task: str, context: str) -> str:
	cleaned_task = task.strip()
	cleaned_context = context.strip()

	if not cleaned_task:
		raise ValueError("Task must not be empty.")
	if not cleaned_context:
		raise ValueError("Context must not be empty.")

	response = _get_client().models.generate_content(
		model=RESEARCH_MODEL,
		contents=_build_prompt(cleaned_task, cleaned_context),
		config=types.GenerateContentConfig(
			temperature=0.2,
			maxOutputTokens=1200,
		),
	)

	result = (response.text or "").strip()
	if not result:
		raise ValueError("Researcher returned an empty response.")

	return result


def _build_prompt(task: str, context: str) -> str:
	return f"""
You are a research agent working on one task in a multi-agent research system.

Write a detailed, factual response for the task below.

Requirements:
- Focus on substance only.
- Do not add fluff, filler, or motivational language.
- Use the provided context to stay aligned with the original query and existing findings.
- If the context includes prior findings, use them to improve precision and avoid repetition.
- Prefer concrete statements over generic commentary.
- Return plain text only.

Task:
{task}

Context:
{context}
""".strip()
