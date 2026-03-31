"""Generate a structured UI spec from a natural-language prompt."""

from __future__ import annotations

from shared.llm.gemini import generate_structured

MODEL = "gemini-3.1-pro-preview"

SYSTEM_PROMPT = """\
You are a UI specification generator. Given a user description of a UI, produce a JSON object \
that strictly conforms to the provided schema.

Rules:
- "app_name" must be a short PascalCase name for the application.
- Each component must have a "type" from: button, input, text, container.
- Each component must have a "label" describing its purpose.
- Use "children" to nest components inside a container.
- Use "props" for component-specific key/value configuration.
- Use "className" to assign a CSS class name to a component.
- Use "style" for inline style overrides (colors, spacing, sizing).
- Use top-level "styles" to define shared CSS classes as {className: {property: value}} pairs.
- Do NOT include any keys outside the schema.
- Do NOT add explanations, comments, or markdown — output only valid JSON.
"""

UI_SPEC_SCHEMA = {
    "type": "object",
    "required": ["app_name", "components"],
    "additionalProperties": False,
    "properties": {
        "app_name": {
            "type": "string",
            "minLength": 1,
        },
        "components": {
            "type": "array",
            "items": {"$ref": "#/$defs/component"},
        },
        "styles": {
            "type": "object",
            "additionalProperties": {
                "type": "object",
                "additionalProperties": True,
            },
        },
    },
    "$defs": {
        "component": {
            "type": "object",
            "required": ["type", "label"],
            "additionalProperties": False,
            "properties": {
                "type": {
                    "type": "string",
                    "enum": ["button", "input", "text", "container"],
                },
                "label": {
                    "type": "string",
                },
                "props": {
                    "type": "object",
                    "additionalProperties": True,
                },
                "className": {
                    "type": "string",
                },
                "style": {
                    "type": "object",
                    "additionalProperties": True,
                },
                "children": {
                    "type": "array",
                    "items": {"$ref": "#/$defs/component"},
                },
            },
        },
    },
}

COMPONENT_TYPES = ["button", "input", "text", "container"]


def generate_spec(prompt: str) -> dict:
    """Convert a natural-language UI description into a validated JSON UI spec."""
    full_prompt = f"{SYSTEM_PROMPT}\nUser request:\n{prompt}"
    return generate_structured(prompt=full_prompt, model=MODEL, schema=UI_SPEC_SCHEMA)
