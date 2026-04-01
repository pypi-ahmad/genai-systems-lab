"""Retired Streamlit entrypoint.

The project now standardizes on the Next.js portfolio frontend.
This file remains only to provide a clear deprecation message when invoked.
"""

from __future__ import annotations

import streamlit as st


st.set_page_config(page_title="GenAI Systems Lab", layout="centered")
st.title("Streamlit UI retired")
st.info("GenAI Systems Lab now standardizes on the Next.js portfolio frontend.")
st.markdown(
    "Use the portfolio at `http://localhost:3000` during local development or the deployed site at `https://genai-systems-lab.vercel.app/`."
)
