"""Report writing utilities for the multi-agent research workflow."""

from __future__ import annotations

import json

from google.genai import types

from shared.llm.gemini import _get_client


WRITER_MODEL = "gemini-3-flash-preview"


def write_report(query: str, findings: dict[str, str]) -> str:
	cleaned_query = query.strip()
	cleaned_findings = {str(task).strip(): str(result).strip() for task, result in findings.items()}

	if not cleaned_query:
		raise ValueError("Query must not be empty.")
	if not cleaned_findings:
		raise ValueError("Findings must not be empty.")
	if any(not task or not result for task, result in cleaned_findings.items()):
		raise ValueError("Findings must contain non-empty task names and results.")

	response = _get_client().models.generate_content(
		model=WRITER_MODEL,
		contents=_build_prompt(cleaned_query, cleaned_findings),
		config=types.GenerateContentConfig(
			temperature=0.3,
			maxOutputTokens=1500,
		),
	)

	result = (response.text or "").strip()
	if not result:
		raise ValueError("Writer returned an empty response.")

	return result


def _build_prompt(query: str, findings: dict[str, str]) -> str:
	findings_json = json.dumps(findings, indent=2)
	return f"""
You are a writer agent in a multi-agent research system.

Generate a clean, readable structured report based on the research findings.

Required format:
- Title
- Introduction
- One section per task
- Conclusion

Requirements:
- Keep the writing clear and concise.
- Preserve the substance of the findings.
- Organize sections using the task names as section headings when appropriate.
- Do not add filler or generic commentary.
- Return plain text only.

Original query:
{query}

Findings:
{findings_json}
""".strip()
