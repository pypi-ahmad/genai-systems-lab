"""Task definitions for the Content Creation Pipeline."""

from crewai import Agent, Task


def build_research_task(agent: Agent, topic: str) -> Task:
    return Task(
        description=(
            f"Research the following topic thoroughly: {topic}\n\n"
            "Gather key facts, statistics, expert quotes, and credible sources. "
            "Organize findings into a structured brief with sections for "
            "key findings, supporting data, notable quotes, and a source list."
        ),
        expected_output=(
            "A structured research brief with key findings, statistics, and sources"
        ),
        agent=agent,
    )


def build_writing_task(agent: Agent, research_task: Task) -> Task:
    return Task(
        description=(
            "Using the research brief provided, write a complete article in Markdown.\n\n"
            "Structure the article with:\n"
            "- A compelling title\n"
            "- An engaging introduction\n"
            "- Well-organized body sections with clear headings\n"
            "- A conclusion that summarizes the key takeaways\n\n"
            "Ensure the article is informative, engaging, and covers all key points "
            "from the research."
        ),
        expected_output="Complete article draft in Markdown",
        agent=agent,
        context=[research_task],
    )


def build_editing_task(agent: Agent, writing_task: Task) -> Task:
    return Task(
        description=(
            "Review and edit the article draft for publication quality.\n\n"
            "Focus on:\n"
            "- Grammar, spelling, and punctuation\n"
            "- Clarity and conciseness of each paragraph\n"
            "- Logical flow between sections\n"
            "- Consistent tone throughout\n"
            "- Factual accuracy against the original research\n\n"
            "Return the full improved article with all edits applied inline."
        ),
        expected_output="Polished, publication-ready article",
        agent=agent,
        context=[writing_task],
    )


def build_seo_task(agent: Agent, editing_task: Task) -> Task:
    return Task(
        description=(
            "Optimize the polished article for search engine visibility.\n\n"
            "Perform the following:\n"
            "- Optimize headings (H1, H2, H3) with target keywords\n"
            "- Add a meta description (under 160 characters)\n"
            "- Check and adjust keyword density for primary and secondary keywords\n"
            "- Suggest internal linking opportunities\n"
            "- Score readability (target: grade 8–10)\n\n"
            "Return the final article followed by an SEO metadata block containing "
            "title tag, meta description, target keywords, and readability score."
        ),
        expected_output="SEO-optimized article with metadata block",
        agent=agent,
        context=[editing_task],
    )
