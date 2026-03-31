from __future__ import annotations

from app.graph import build_graph
from app.state import initial_state
from shared.config import set_byok_api_key, reset_byok_api_key


def run(input: str, api_key: str) -> dict:
    """Run the support agent and return structured output."""
    token = set_byok_api_key(api_key)
    try:
        graph = build_graph()
        result = graph.invoke(initial_state(input))
        output = {
            "intent": result.get("intent", ""),
            "confidence": result.get("confidence", 0.0),
            "response": result.get("response", ""),
            "escalate": result.get("escalate", False),
        }
        if result.get("escalate"):
            output["ticket_summary"] = result.get("ticket_summary", {})
        return output
    finally:
        reset_byok_api_key(token)
