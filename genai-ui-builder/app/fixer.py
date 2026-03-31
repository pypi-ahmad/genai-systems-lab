"""Fix generated React code based on an error message."""

from __future__ import annotations

from shared.llm.gemini import generate_text

MODEL = "gemini-3-flash-preview"

PROMPT_TEMPLATE = """\
You are a React code fixer. The following React component code has an error.

Code:
```jsx
{code}
```

Error:
{error}

Fix the code so it resolves the error. Output ONLY the corrected full component code. \
No explanations, no markdown fences, no extra text.
"""


def fix_code(code: str, error: str) -> str:
    """Return a corrected version of the React code based on the error message."""
    prompt = PROMPT_TEMPLATE.format(code=code, error=error)
    return generate_text(prompt=prompt, model=MODEL)