"""Execution entry-point for the Data Analysis Agent."""

from __future__ import annotations

from app.data_loader import load_data
from app.graph import build_graph
from app.state import initial_state
from shared.config import set_byok_api_key, reset_byok_api_key


def run(input: str, api_key: str) -> dict:
    """Run the data analysis agent and return structured output.

    Input format: ``<query>`` or ``<query> --data <path> --engine <engine>``.
    """
    token = set_byok_api_key(api_key)
    try:
        parts = input.split()
        data_path = None
        engine = "pandas"
        query_parts: list[str] = []

        i = 0
        while i < len(parts):
            if parts[i] == "--data" and i + 1 < len(parts):
                data_path = parts[i + 1]
                i += 2
            elif parts[i] == "--engine" and i + 1 < len(parts):
                engine = parts[i + 1]
                i += 2
            else:
                query_parts.append(parts[i])
                i += 1

        query = " ".join(query_parts).strip()
        if not query:
            return {"error": "A query is required."}

        load_data(data_path)  # validate early
        graph = build_graph()
        result = graph.invoke(initial_state(query, engine=engine))
        return {
            "plan": result.get("plan", []),
            "result": result.get("execution_result", {}),
            "explanation": result.get("explanation", ""),
            "success": result.get("success", False),
            "iterations": result.get("iteration", 0),
        }
    finally:
        reset_byok_api_key(token)
