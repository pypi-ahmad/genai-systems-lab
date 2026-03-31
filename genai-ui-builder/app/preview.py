"""Local preview server for generated React components.

Uses Python's built-in http.server to serve an HTML page that loads
React and Babel from CDN, rendering the generated JSX in-browser.
No npm or build tools required.
"""

from __future__ import annotations

import os
import re
from functools import partial
from http.server import HTTPServer, SimpleHTTPRequestHandler

DEFAULT_PORT = 3000

HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title} — Preview</title>
  <script src="https://unpkg.com/react@18/umd/react.development.js" crossorigin></script>
  <script src="https://unpkg.com/react-dom@18/umd/react-dom.development.js" crossorigin></script>
  <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; }}
    body {{ margin: 0; font-family: system-ui, -apple-system, sans-serif; }}
    #root {{ padding: 24px; }}
{css}
  </style>
</head>
<body>
  <div id="root"></div>
  <script type="text/babel">
{components_js}

{app_js}

    const root = ReactDOM.createRoot(document.getElementById('root'));
    root.render(<App />);
  </script>
</body>
</html>
"""


def _strip_imports(code: str) -> str:
    """Remove import/export statements for inline use."""
    lines = code.splitlines()
    out: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("import "):
            continue
        if stripped.startswith("export default "):
            out.append(line.replace("export default ", "", 1))
            continue
        out.append(line)
    return "\n".join(out)


def _css_to_style_block(css: str) -> str:
    """Indent CSS for embedding inside a <style> tag."""
    return "\n".join(f"    {line}" for line in css.splitlines())


def build_preview_html(files: dict[str, str], title: str = "App") -> str:
    """Build a self-contained HTML preview from generated files."""
    # Collect sub-component code (inline, imports stripped)
    component_blocks: list[str] = []
    for filename, content in sorted(files.items()):
        if filename.startswith("components/") and filename.endswith(".jsx"):
            component_blocks.append(f"    // --- {filename} ---")
            component_blocks.append(_strip_imports(content))

    # App.jsx (imports stripped)
    app_code = files.get("App.jsx", "")
    # Also strip sub-component imports since they're inlined
    app_stripped = _strip_imports(app_code)
    # Rename the component function to App for the render call
    app_stripped = re.sub(
        r"^function\s+\w+\(",
        "function App(",
        app_stripped,
        count=1,
        flags=re.MULTILINE,
    )

    # CSS
    css = files.get("styles.css", "")
    css_block = _css_to_style_block(css) if css else ""

    return HTML_TEMPLATE.format(
        title=title,
        css=css_block,
        components_js="\n".join(component_blocks),
        app_js=app_stripped,
    )


class _PreviewHandler(SimpleHTTPRequestHandler):
    """Serves the preview HTML on GET /."""

    html: str = ""

    def do_GET(self) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(self.html.encode("utf-8"))

    def log_message(self, format: str, *args: object) -> None:
        # Quieter logging: single-line
        print(f"  [{self.address_string()}] {args[0]}" if args else "")


def start_preview(files: dict[str, str], port: int = DEFAULT_PORT, title: str = "App") -> None:
    """Start a local HTTP server to preview the generated UI."""
    html = build_preview_html(files, title=title)

    handler = type("Handler", (_PreviewHandler,), {"html": html})
    server = HTTPServer(("localhost", port), handler)

    print(f"\nPreview server running at http://localhost:{port}")
    print("Press Ctrl+C to stop.\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
    finally:
        server.server_close()
