"""Streamlit UI for invoking project pipelines through the shared FastAPI API."""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

# Ensure repo root is on sys.path so `shared.*` imports work when Streamlit
# runs this file directly.
_REPO_ROOT = str(Path(__file__).resolve().parent.parent.parent)
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

import streamlit as st  # noqa: E402

from shared.api.runner import list_available  # noqa: E402

API_BASE_URL = "http://127.0.0.1:8000"


def _call_run_endpoint(project: str, user_input: str) -> dict:
    """POST to the FastAPI /{project}/run endpoint and return the JSON body."""
    payload = json.dumps({"input": user_input}).encode("utf-8")
    url = f"{API_BASE_URL.rstrip('/')}/{project}/run"
    request = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        return {"output": "", "elapsed_ms": 0, "exit_code": 1, "error": f"HTTP {exc.code}: {detail}"}
    except urllib.error.URLError as exc:
        return {"output": "", "elapsed_ms": 0, "exit_code": 1, "error": f"Connection error: {exc.reason}"}


# ---------------------------------------------------------------------------
# Streamlit page
# ---------------------------------------------------------------------------

st.set_page_config(page_title="GenAI Systems Lab", layout="wide")
st.title("GenAI Systems Lab")
st.markdown("Run any project through the shared FastAPI endpoint.")

projects = list_available()

col1, col2 = st.columns([1, 3])

with col1:
    selected_project = st.selectbox("Project", projects, index=0)

with col2:
    user_input = st.text_area("Input", height=150, placeholder="Enter the request payload text…")

run_clicked = st.button("Run Project", type="primary")

if run_clicked:
    if not selected_project:
        st.error("Please select a project.")
    else:
        with st.spinner(f"Running {selected_project}…"):
            result = _call_run_endpoint(selected_project, user_input)

        error = result.get("error")
        exit_code = result.get("exit_code", 1)

        status_col, latency_col = st.columns(2)
        with status_col:
            if error:
                st.error(f"Status: error — {error}")
            elif exit_code == 0:
                st.success("Status: success")
            else:
                st.warning(f"Status: error (exit_code={exit_code})")
        with latency_col:
            st.metric("Latency", f"{result.get('elapsed_ms', 0):.2f} ms")

        st.subheader("Output")
        st.code(result.get("output", ""), language=None)

    return demo
