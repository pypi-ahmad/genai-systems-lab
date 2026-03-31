"""Application entry point."""

from __future__ import annotations

import importlib.util
from pathlib import Path

from shared.api.step_events import emit_step
from shared.config import set_byok_api_key, reset_byok_api_key


def _load_run_agent():
	try:
		from .agent import run_agent

		return run_agent
	except ImportError:
		agent_path = Path(__file__).with_name("agent.py")
		spec = importlib.util.spec_from_file_location("nl2sql_agent", agent_path)
		if spec is None or spec.loader is None:
			raise RuntimeError("Unable to load agent module.")

		module = importlib.util.module_from_spec(spec)
		spec.loader.exec_module(module)
		return module.run_agent


run_agent = _load_run_agent()


def run(input: str, api_key: str) -> dict:
	"""Run the NL-to-SQL pipeline and return structured output."""
	token = set_byok_api_key(api_key)
	try:
		emit_step("planner", "running")
		response = run_agent(input)
		emit_step("planner", "done")
		emit_step("schema", "running")
		emit_step("schema", "done")
		emit_step("generator", "running")
		emit_step("generator", "done")
		emit_step("validator", "running")
		emit_step("validator", "done")
		emit_step("executor", "running")
		emit_step("executor", "done")
		emit_step("summarizer", "running")
		emit_step("summarizer", "done")
		result_data = response["result"]
		if hasattr(result_data, "to_dict"):
			result_data = result_data.to_dict(orient="records")
		return {"sql": response["sql"], "result": result_data, "summary": response["summary"]}
	finally:
		reset_byok_api_key(token)
