from __future__ import annotations

from typing import TypedDict

MAX_REVISIONS = 3
MAX_PLAN_TASKS = 7
MAX_ORIGINALITY_REWRITES = 2
MAX_EDITOR_REVISIONS = 2
REASONING_MODEL = "gemini-3.1-pro-preview"
WRITING_MODEL = "gemini-3-flash-preview"
VALID_TONES = ("formal", "casual", "technical")
DEFAULT_TONE = "formal"

# Tool registry — each tool has a name and a description the planner sees.
TOOLS: dict[str, str] = {
    "web_search": "Search the web for recent information, news, or data.",
    "deep_analysis": "Perform in-depth analytical reasoning on a complex topic.",
    "compare": "Compare and contrast two or more concepts, technologies, or approaches.",
    "summarize": "Condense a broad topic into key points and takeaways.",
    "fact_check": "Verify claims, cross-reference sources, and validate accuracy.",
}
VALID_FORMATS = ("report", "blog", "linkedin", "twitter", "all")
DEFAULT_FORMATS = ("report",)


class ResearchState(TypedDict, total=False):
    run_id: str
    query: str
    tone: str
    formats: tuple[str, ...]
    plan: list[str]
    tool_assignments: dict[str, str]  # task → tool name chosen by planner
    current_task: str
    findings: dict[str, str]
    critiques: dict[str, str]
    iteration: int
    final_output: str
    blog: str
    linkedin_post: str
    twitter_thread: str
    editor_feedback: str
    editor_revisions: int
    originality_score: float
    originality_feedback: str
    originality_rewrites: int
    node_timings: dict[str, float]
    execution_trace: list[dict]
    total_duration_ms: float
    started_at: str
    completed_at: str
    error: str
    quality_metrics: dict
    best_case: dict
    worst_case: dict


def initial_state(
    query: str,
    *,
    tone: str = DEFAULT_TONE,
    formats: tuple[str, ...] = DEFAULT_FORMATS,
) -> ResearchState:
    if tone not in VALID_TONES:
        tone = DEFAULT_TONE
    return ResearchState(
        run_id="",
        query=query,
        tone=tone,
        formats=formats,
        plan=[],
        tool_assignments={},
        current_task="",
        findings={},
        critiques={},
        iteration=0,
        final_output="",
        blog="",
        linkedin_post="",
        twitter_thread="",
        editor_feedback="",
        editor_revisions=0,
        originality_score=0.0,
        originality_feedback="",
        originality_rewrites=0,
        node_timings={},
        execution_trace=[],
        total_duration_ms=0.0,
        started_at="",
        completed_at="",
        error="",
        quality_metrics={},
        best_case={},
        worst_case={},
    )
