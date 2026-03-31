from __future__ import annotations

import sys
from pathlib import Path

_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = str(Path(__file__).resolve().parent.parent.parent)
for _path in (_PROJECT_ROOT, _REPO_ROOT):
    if _path not in sys.path:
        sys.path.insert(0, _path)

import streamlit as st  # noqa: E402

from app.service import run_research_workflow  # noqa: E402


st.set_page_config(page_title="Flagship Research System", layout="wide")
st.title("Flagship Multi-Agent Research System")
st.caption("Production-grade research workflow with quality gates, observability, and multi-format output.")

with st.sidebar:
    st.subheader("Run Configuration")
    tone = st.selectbox("Tone", ["formal", "casual", "technical"], index=0)
    formats = st.multiselect(
        "Formats",
        ["report", "blog", "linkedin", "twitter"],
        default=["report", "blog"],
    )

query = st.text_area(
    "Research Query",
    height=180,
    placeholder="Compare transformer and state space models for long-context enterprise workloads.",
)

if st.button("Run Research Workflow", type="primary"):
    if not query.strip():
        st.error("Enter a research query.")
    else:
        with st.spinner("Running multi-agent research workflow..."):
            result = run_research_workflow(query.strip(), tone=tone, formats=formats)

        metrics = result["metrics"]
        metric_cols = st.columns(4)
        metric_cols[0].metric("Latency", f"{metrics['latency_ms']:.1f} ms")
        metric_cols[1].metric("Quality Score", f"{metrics['quality_score']:.2f}")
        metric_cols[2].metric("Originality", f"{metrics['originality_score']:.2f}")
        metric_cols[3].metric("Format Coverage", f"{metrics['format_coverage']:.0%}")

        st.subheader("Research Report")
        st.markdown(result["report"] or "_No report generated._")

        if result.get("blog"):
            with st.expander("Blog Post"):
                st.markdown(result["blog"])
        if result.get("linkedin_post"):
            with st.expander("LinkedIn Post"):
                st.text(result["linkedin_post"])
        if result.get("twitter_thread"):
            with st.expander("Twitter Thread"):
                st.text(result["twitter_thread"])

        scenario_cols = st.columns(2)
        with scenario_cols[0]:
            st.subheader("Best Case")
            st.json(result.get("best_case", {}))
        with scenario_cols[1]:
            st.subheader("Worst Case")
            st.json(result.get("worst_case", {}))

        st.subheader("Node Timings")
        st.json(result.get("node_timings", {}))

        with st.expander("Execution Trace"):
            st.json(result.get("trace", []))