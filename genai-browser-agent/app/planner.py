from __future__ import annotations

from shared.llm.gemini import generate_structured

MODEL = "gemini-3.1-pro-preview"

ALLOWED_ACTIONS = ["open_url", "click", "type", "stop"]

RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "action": {
            "type": "string",
            "enum": ALLOWED_ACTIONS,
        },
        "args": {
            "type": "object",
            "properties": {
                "url": {"type": "string"},
                "target": {"type": "string"},
                "text": {"type": "string"},
            },
        },
    },
    "required": ["action", "args"],
}

SYSTEM_PROMPT = (
    "You are an autonomous browser agent. Your job is to decide the single next "
    "action to take in a web browser to accomplish the user's goal.\n\n"
    "Allowed actions:\n"
    "- open_url: args {{\"url\": \"...\"}}\n"
    "- click: args {{\"target\": \"visible text of the link or button\"}}\n"
    "- type: args {{\"target\": \"label or placeholder of the input field\", \"text\": \"...\"}}\n"
    "- stop: args {{}} (use when the goal is complete or impossible)\n\n"
    "Rules:\n"
    "- Return exactly ONE action per turn.\n"
    "- Only use the allowed actions listed above.\n"
    "- For click and type, use the visible text you see on the page as the target "
    "(e.g. button label, link text, input placeholder, or field label). "
    "Do NOT use CSS selectors or XPath.\n"
    "- If the page does not help, navigate elsewhere or stop.\n"
    "- Do not repeat the same failing action.\n"
)


def decide_next_action(goal: str, observation: str, history: str) -> dict:
    prompt = (
        f"{SYSTEM_PROMPT}"
        f"## Goal\n{goal}\n\n"
        f"## Current Page Observation\n{observation}\n\n"
        f"## Action History\n{history if history else 'None yet.'}\n\n"
        "Decide the next action."
    )

    return generate_structured(prompt=prompt, model=MODEL, schema=RESPONSE_SCHEMA)