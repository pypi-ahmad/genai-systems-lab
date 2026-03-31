"""Agent definitions for the Product Launch Strategy Crew."""

from crewai import Agent

REASONING_MODEL = "gemini/gemini-3.1-pro-preview"
SUMMARY_MODEL = "gemini/gemini-3-flash-preview"


def build_market_researcher() -> Agent:
    return Agent(
        role="Senior Market Researcher",
        goal=(
            "Produce a structured market analysis covering industry landscape, "
            "competitor mapping, market sizing, growth trends, and key "
            "opportunities/threats for the product launch. Return JSON."
        ),
        backstory=(
            "Market intelligence professional with 12 years in product-led "
            "companies. Specializes in competitive analysis, TAM/SAM/SOM "
            "estimation, and identifying market timing windows. Evaluates "
            "markets through both quantitative data and qualitative trend "
            "analysis."
        ),
        llm=REASONING_MODEL,
        verbose=True,
    )


def build_customer_analyst() -> Agent:
    return Agent(
        role="Senior Customer Analyst",
        goal=(
            "Define target customer segments with detailed personas, pain "
            "points, buying behavior, and decision criteria based on market "
            "research findings. Return JSON."
        ),
        backstory=(
            "Customer research specialist with experience across B2B and B2C "
            "launches. Builds personas from behavioral data rather than "
            "demographics alone. Focuses on jobs-to-be-done, switching costs, "
            "and purchase triggers that drive actual adoption."
        ),
        llm=REASONING_MODEL,
        verbose=True,
    )


def build_product_strategist() -> Agent:
    return Agent(
        role="Head of Product Strategy",
        goal=(
            "Define clear product positioning, core messaging, value "
            "propositions per segment, and competitive differentiation based "
            "on market analysis and customer personas. Return JSON."
        ),
        backstory=(
            "Product strategist who has launched products from zero-to-one "
            "across SaaS, consumer, and platform businesses. Thinks in terms "
            "of positioning narratives — the intersection of what customers "
            "need, what competitors miss, and what the product uniquely "
            "delivers."
        ),
        llm=REASONING_MODEL,
        verbose=True,
    )


def build_marketing_strategist() -> Agent:
    return Agent(
        role="VP of Marketing",
        goal=(
            "Produce a detailed go-to-market plan with channel strategy, "
            "campaign tactics, launch timeline, budget allocation with "
            "dollar-amount estimates and projected ROI per channel, and "
            "success metrics based on the full strategic context. Return JSON."
        ),
        backstory=(
            "Growth marketing leader who has executed product launches from "
            "startup to enterprise scale. Balances brand-building with "
            "performance marketing. Plans backward from revenue targets and "
            "works in terms of funnel economics, channel ROI, and launch "
            "sequencing. Known for rigorous budget modelling — estimates "
            "spend per channel, forecasts CAC and expected ROI, and always "
            "proposes a total launch budget with clear justification."
        ),
        llm=REASONING_MODEL,
        verbose=True,
    )
