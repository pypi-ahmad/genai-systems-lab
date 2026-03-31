from __future__ import annotations

from app.graph import build_graph
from app.state import initial_state
from shared.config import set_byok_api_key, reset_byok_api_key


def run(input: str, api_key: str) -> dict:
    """Run the debugging agent and return structured output.

    Input is the buggy source code. Optionally append ``\n---ERROR---\n<traceback>``
    to provide an error message.
    """
    token = set_byok_api_key(api_key)
    try:
        separator = "\n---ERROR---\n"
        if separator in input:
            code, error = input.split(separator, 1)
        else:
            code, error = input, ""

        graph = build_graph()
        result = graph.invoke(initial_state(code.strip(), error.strip()))
        return {
            "diff": result.get("diff", ""),
            "fixed_code": result.get("fixed_code", ""),
            "test_result": result.get("test_result", ""),
            "is_resolved": result.get("is_resolved", False),
            "iterations": result.get("iteration", 0),
        }
    finally:
        reset_byok_api_key(token)
