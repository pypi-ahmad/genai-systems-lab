"""Application entry point.

Step events (``emit_step``) are now emitted from inside ``agent.run_agent``
as each pipeline stage actually executes — running this wrapper as a flat
``emit_step("planner","running") / emit_step("planner","done") / ...`` loop
*after* ``run_agent`` returned produced a cosmetic replay rather than a
real progress stream (C-3 / C-15 in the audit).
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

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
		response = run_agent(input)
		result_data = response["result"]
		if hasattr(result_data, "to_dict"):
			result_data = result_data.to_dict(orient="records")
		return {"sql": response["sql"], "result": result_data, "summary": response["summary"]}
	finally:
		reset_byok_api_key(token)
