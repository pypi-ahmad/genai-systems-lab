"""Agent definitions for the Startup Team Simulator."""

from crewai import Agent

REASONING_MODEL = "gemini/gemini-3.1-pro-preview"
SUMMARY_MODEL = "gemini/gemini-3-flash-preview"


def build_ceo() -> Agent:
    return Agent(
        role="Chief Executive Officer",
        goal=(
            "Transform a raw startup idea into a clear vision statement with "
            "target market, value proposition, competitive positioning, and "
            "success metrics. Always return output as a JSON object."
        ),
        backstory=(
            "Experienced startup founder who has built and scaled multiple "
            "companies. Thinks in terms of market opportunity, defensibility, "
            "and growth potential."
        ),
        llm=REASONING_MODEL,
        verbose=True,
    )


def build_product_manager() -> Agent:
    return Agent(
        role="Head of Product",
        goal=(
            "Define the product scope, core features, user personas, and a "
            "prioritized roadmap based on the CEO's vision. "
            "Always return output as a JSON object."
        ),
        backstory=(
            "Senior product manager with experience shipping B2B and B2C "
            "products. Skilled at turning abstract strategy into specific, "
            "buildable features with clear acceptance criteria."
        ),
        llm=REASONING_MODEL,
        verbose=True,
    )


def build_cto() -> Agent:
    return Agent(
        role="Chief Technology Officer",
        goal=(
            "Define the system architecture, technology stack, infrastructure "
            "requirements, and technical constraints based on the product "
            "specification. Always return output as a JSON object."
        ),
        backstory=(
            "Senior engineering leader who has designed systems at scale. "
            "Balances technical excellence with pragmatic delivery, favoring "
            "proven technologies for MVPs and reserving cutting-edge choices "
            "for genuine technical differentiators."
        ),
        llm=REASONING_MODEL,
        verbose=True,
    )


def build_engineer() -> Agent:
    return Agent(
        role="Lead Engineer",
        goal=(
            "Produce a detailed execution plan with sprint-level breakdown, "
            "task assignments, milestones, and delivery timeline based on the "
            "technical architecture. Always return output as a JSON object."
        ),
        backstory=(
            "Staff engineer experienced in greenfield builds and team "
            "leadership. Focuses on incremental delivery, risk mitigation "
            "through early integration, and realistic time estimates."
        ),
        llm=SUMMARY_MODEL,
        verbose=True,
    )
