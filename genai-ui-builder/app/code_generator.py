"""Generate React component code from a validated UI spec."""

from __future__ import annotations

ELEMENT_MAP = {
    "button": "button",
    "input": "input",
    "text": "p",
    "container": "div",
}

INDENT = "  "


def _render_css(styles: dict) -> str:
    """Render top-level shared styles as a CSS stylesheet string."""
    if not styles:
        return ""
    lines: list[str] = []
    for class_name, rules in styles.items():
        props = "\n".join(f"  {_camel_to_kebab(k)}: {v};" for k, v in rules.items())
        lines.append(f".{class_name} {{\n{props}\n}}")
    return "\n\n".join(lines) + "\n"


def _camel_to_kebab(name: str) -> str:
    """Convert camelCase to kebab-case (e.g. backgroundColor -> background-color)."""
    result: list[str] = []
    for ch in name:
        if ch.isupper():
            result.append("-")
            result.append(ch.lower())
        else:
            result.append(ch)
    return "".join(result)


def _render_style(style: dict) -> str:
    pairs = ", ".join(f'"{k}": "{v}"' for k, v in style.items())
    return "{{ " + pairs + " }}"


def _render_props(component: dict) -> str:
    parts: list[str] = []

    if component.get("className"):
        parts.append(f'className="{component["className"]}"')

    if component.get("style"):
        parts.append(f"style={_render_style(component['style'])}")

    for key, value in component.get("props", {}).items():
        if isinstance(value, bool):
            parts.append(key if value else f'{key}={{false}}')
        elif isinstance(value, str):
            parts.append(f'{key}="{value}"')
        else:
            parts.append(f"{key}={{{value!r}}}")

    return (" " + " ".join(parts)) if parts else ""


def _render_component(component: dict, depth: int) -> str:
    tag = ELEMENT_MAP[component["type"]]
    prefix = INDENT * depth
    props = _render_props(component)
    children = component.get("children", [])

    if tag == "input":
        return f'{prefix}<input placeholder="{component["label"]}"{props} />'

    if not children:
        return f"{prefix}<{tag}{props}>{component['label']}</{tag}>"

    lines = [f"{prefix}<{tag}{props}>"]
    for child in children:
        lines.append(_render_component(child, depth + 1))
    lines.append(f"{prefix}</{tag}>")
    return "\n".join(lines)


def _collect_component_names(components: list[dict]) -> list[str]:
    """Collect unique component type labels suitable for extraction as sub-components."""
    names: list[str] = []
    for comp in components:
        if comp.get("children"):
            name = comp["label"].replace(" ", "")
            if name not in names:
                names.append(name)
    return names


def _render_subcomponent(component: dict) -> str:
    """Render a top-level component with children as a standalone React component."""
    name = component["label"].replace(" ", "")
    body_lines: list[str] = []
    for child in component.get("children", []):
        body_lines.append(_render_component(child, 2))
    body = "\n".join(body_lines)
    tag = ELEMENT_MAP[component["type"]]
    props = _render_props(component)

    return (
        f"import React from 'react';\n"
        f"\n"
        f"export default function {name}() {{\n"
        f"  return (\n"
        f"    <{tag}{props}>\n"
        f"{body}\n"
        f"    </{tag}>\n"
        f"  );\n"
        f"}}\n"
    )


def generate_files(spec: dict) -> dict[str, str]:
    """Convert a validated UI spec into a dict of {filename: content} pairs.

    Always produces:
      - App.jsx  (root component importing sub-components)
    Optionally produces:
      - components/<Name>.jsx  (one per top-level container with children)
      - styles.css             (when top-level 'styles' is present)
    """
    app_name = spec["app_name"]
    components = spec.get("components", [])
    styles = spec.get("styles", {})
    files: dict[str, str] = {}

    # Identify extractable sub-components (top-level containers with children)
    sub_components: list[dict] = []
    flat_components: list[dict] = []
    for comp in components:
        if comp.get("children"):
            sub_components.append(comp)
        else:
            flat_components.append(comp)

    # Generate sub-component files
    for comp in sub_components:
        name = comp["label"].replace(" ", "")
        files[f"components/{name}.jsx"] = _render_subcomponent(comp)

    # Generate styles.css
    css = _render_css(styles)
    if css:
        files["styles.css"] = css

    # Generate App.jsx
    imports: list[str] = ["import React from 'react';"]
    if css:
        imports.append("import './styles.css';")
    for comp in sub_components:
        name = comp["label"].replace(" ", "")
        imports.append(f"import {name} from './components/{name}';")

    body_lines: list[str] = []
    for comp in components:
        if comp in sub_components:
            name = comp["label"].replace(" ", "")
            body_lines.append(f"{INDENT * 3}<{name} />")
        else:
            body_lines.append(_render_component(comp, 3))

    body = "\n".join(body_lines)
    import_block = "\n".join(imports)

    files["App.jsx"] = (
        f"{import_block}\n"
        f"\n"
        f"export default function {app_name}() {{\n"
        f"  return (\n"
        f"    <div>\n"
        f"{body}\n"
        f"    </div>\n"
        f"  );\n"
        f"}}\n"
    )

    return files


def generate_react_code(spec: dict) -> str:
    """Convert a validated UI spec into a single React component string.

    Kept for backward compatibility. For multi-file output, use generate_files().
    """
    return generate_files(spec)["App.jsx"]