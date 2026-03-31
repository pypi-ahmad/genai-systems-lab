"""Execution entry point for the multi-agent research workflow."""

from __future__ import annotations

from .service import run_research_workflow
from shared.config import set_byok_api_key, reset_byok_api_key


def run(input: str, api_key: str) -> dict:
	"""Run the multi-agent research workflow and return structured output."""
	token = set_byok_api_key(api_key)
	try:
		result = run_research_workflow(input, tone="formal", formats=("report",))
		output = {
			"query": result["query"],
			"report": result["report"],
			"metrics": result["metrics"],
			"node_timings": result["node_timings"],
		}
		for key in ("blog", "linkedin_post", "twitter_thread", "best_case", "worst_case"):
			if result.get(key):
				output[key] = result[key]
		return output
	finally:
		reset_byok_api_key(token)
