from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed

from app.state import WRITING_MODEL, ResearchState
from shared.llm.gemini import generate_text


def _blog_prompt(report: str, query: str, tone: str) -> str:
    return (
        "You are a content strategist. Convert the research report below into "
        "an engaging blog post (800-1200 words).\n\n"
        f"Original research query: {query}\n"
        f"Tone: {tone}\n\n"
        f"Report:\n{report}\n\n"
        "Guidelines:\n"
        "- Write a compelling title and opening hook.\n"
        "- Use subheadings, short paragraphs, and bullet points for scannability.\n"
        "- Include a clear call-to-action or takeaway at the end.\n"
        "- Maintain the factual accuracy of the report.\n"
        "- Output valid Markdown."
    )


def _linkedin_prompt(report: str, query: str, tone: str) -> str:
    return (
        "You are a LinkedIn content creator. Convert the research report below "
        "into a LinkedIn post (150-300 words).\n\n"
        f"Original research query: {query}\n"
        f"Tone: {tone}\n\n"
        f"Report:\n{report}\n\n"
        "Guidelines:\n"
        "- Start with a strong hook line.\n"
        "- Use short paragraphs (1-2 sentences each) with line breaks.\n"
        "- Include 2-3 key insights from the report.\n"
        "- End with a question or call-to-action to drive engagement.\n"
        "- Add 3-5 relevant hashtags at the end.\n"
        "- Do NOT use Markdown formatting — plain text only."
    )


def _twitter_prompt(report: str, query: str, tone: str) -> str:
    return (
        "You are a Twitter/X content creator. Convert the research report below "
        "into a Twitter thread of 4-8 tweets.\n\n"
        f"Original research query: {query}\n"
        f"Tone: {tone}\n\n"
        f"Report:\n{report}\n\n"
        "Guidelines:\n"
        "- Each tweet must be under 280 characters.\n"
        "- Number each tweet (1/, 2/, etc.).\n"
        "- First tweet should hook the reader with a bold claim or question.\n"
        "- Last tweet should summarize the key takeaway.\n"
        "- Use plain text — no Markdown.\n"
        "- Include 1-2 relevant hashtags in the final tweet only."
    )


_FORMAT_BUILDERS = {
    "blog": ("blog", _blog_prompt),
    "linkedin": ("linkedin_post", _linkedin_prompt),
    "twitter": ("twitter_thread", _twitter_prompt),
}


def formatter_node(state: ResearchState) -> dict:
    report = state.get("final_output", "")
    query = state.get("query", "")
    tone = state.get("tone", "formal")
    formats = state.get("formats", ("report",))

    if not report.strip():
        return {}

    if "all" in formats:
        requested = set(_FORMAT_BUILDERS.keys())
    else:
        requested = set(formats) & set(_FORMAT_BUILDERS.keys())

    if not requested:
        return {}

    results: dict[str, str] = {}

    def _generate(fmt: str) -> tuple[str, str]:
        field, prompt_fn = _FORMAT_BUILDERS[fmt]
        text = generate_text(
            prompt=prompt_fn(report, query, tone),
            model=WRITING_MODEL,
        )
        return field, text

    with ThreadPoolExecutor(max_workers=len(requested)) as pool:
        futures = {pool.submit(_generate, fmt): fmt for fmt in requested}
        for future in as_completed(futures):
            try:
                field, text = future.result()
                results[field] = text
            except Exception:
                fmt = futures[future]
                field = _FORMAT_BUILDERS[fmt][0]
                results[field] = ""

    return results
