from __future__ import annotations

from app.graph import build_graph
from app.state import initial_state
from shared.config import set_byok_api_key, reset_byok_api_key


def run(input: str, api_key: str) -> dict:
    """Run the workflow agent and return structured output."""
    token = set_byok_api_key(api_key)
    try:
        state = initial_state(input)
        graph = build_graph()
        result = graph.invoke(state)
        plan = result.get("plan", [])
        results = result.get("results", {})
        return {
            "task": input,
            "plan": plan,
            "results": {step: results.get(step, "") for step in plan},
            "summary": results.get("_final_summary", ""),
        }
    finally:
        reset_byok_api_key(token)
