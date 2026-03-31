"""Validate a UI spec against the canonical schema."""

from __future__ import annotations

from app.spec_generator import COMPONENT_TYPES

REQUIRED_TOP_LEVEL = {"app_name", "components"}
ALLOWED_TOP_LEVEL = {"app_name", "components", "styles"}
REQUIRED_COMPONENT = {"type", "label"}
ALLOWED_COMPONENT_KEYS = {"type", "label", "props", "children", "style", "className"}


def _validate_component(component: dict) -> bool:
    if not isinstance(component, dict):
        return False

    if not REQUIRED_COMPONENT.issubset(component):
        return False

    if not component.keys() <= ALLOWED_COMPONENT_KEYS:
        return False

    if component["type"] not in COMPONENT_TYPES:
        return False

    if not isinstance(component["label"], str):
        return False

    if "props" in component and not isinstance(component["props"], dict):
        return False

    if "className" in component and not isinstance(component["className"], str):
        return False

    if "style" in component and not isinstance(component["style"], dict):
        return False

    if "children" in component:
        if not isinstance(component["children"], list):
            return False
        for child in component["children"]:
            if not _validate_component(child):
                return False

    return True


def validate_spec(spec: dict) -> bool:
    """Return True if the spec conforms to the UI schema, False otherwise."""
    if not isinstance(spec, dict):
        return False

    if not REQUIRED_TOP_LEVEL.issubset(spec):
        return False

    if not spec.keys() <= ALLOWED_TOP_LEVEL:
        return False

    if not isinstance(spec["app_name"], str) or not spec["app_name"].strip():
        return False

    if not isinstance(spec["components"], list):
        return False

    if "styles" in spec:
        if not isinstance(spec["styles"], dict):
            return False
        for class_name, rules in spec["styles"].items():
            if not isinstance(class_name, str) or not isinstance(rules, dict):
                return False

    for component in spec["components"]:
        if not _validate_component(component):
            return False

    return True