"""Critique utilities for reviewing research outputs."""

from __future__ import annotations

from google.genai import types

from shared.llm.gemini import _get_client


CRITIC_MODEL = "gemini-3.1-pro-preview"


def critique(task: str, research_output: str) -> str:
	cleaned_task = task.strip()
	cleaned_output = research_output.strip()

	if not cleaned_task:
		raise ValueError("Task must not be empty.")
	if not cleaned_output:
		raise ValueError("Research output must not be empty.")

	response = _get_client().models.generate_content(
		model=CRITIC_MODEL,
		contents=_build_prompt(cleaned_task, cleaned_output),
		config=types.GenerateContentConfig(
			temperature=0.2,
			maxOutputTokens=1000,
		),
	)

	result = (response.text or "").strip()
	if not result:
		raise ValueError("Critic returned an empty response.")

	return result


def _build_prompt(task: str, research_output: str) -> str:
	return f"""
You are a critic agent reviewing a research output in a multi-agent research system.

Evaluate the response for:
- correctness
- completeness
- missing points

Requirements:
- Provide constructive critique.
- Give specific suggestions for improvement.
- Focus on factual quality and coverage.
- Do not rewrite the full answer.
- Return plain text only.

Task:
{task}

Research output:
{research_output}
""".strip()
