from __future__ import annotations

from app.agent import run_agent
from shared.config import set_byok_api_key, reset_byok_api_key


def run(input: str, api_key: str) -> dict:
    """Run the browser automation agent and return structured output."""
    token = set_byok_api_key(api_key)
    try:
        return run_agent(input)
    finally:
        reset_byok_api_key(token)
