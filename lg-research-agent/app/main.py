"""Entry point for the Research Graph Agent."""

from __future__ import annotations

from app.graph import build_graph
from app.state import initial_state
from shared.config import reset_byok_api_key, set_byok_api_key


def run(input: str, api_key: str) -> dict:
    """Run the research graph agent and return structured output."""
    token = set_byok_api_key(api_key)
    try:
        query = input.strip()
        if not query:
            return {
                "query": "",
                "error": "A query is required.",
                "status": "error",
                "success": False,
            }

        graph = build_graph()
        result = graph.invoke(initial_state(query))
        report = str(result.get("report", "")).strip()

        return {
            "query": query,
            "plan": result.get("plan", []),
            "findings": result.get("findings", []),
            "critique": result.get("critique", ""),
            "report": report,
            "success": bool(report),
            "status": "completed" if report else "failed",
        }
    finally:
        reset_byok_api_key(token)
