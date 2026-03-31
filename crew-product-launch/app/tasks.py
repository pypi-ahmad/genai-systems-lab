"""Task definitions for the Product Launch Strategy Crew."""

import json

from crewai import Agent, Task

SCORECARD_METRICS = [
    "features",
    "pricing",
    "ux",
    "market_reach",
    "brand_trust",
]

MARKET_SCHEMA = {
    "industry_overview": "High-level description of the industry landscape",
    "competitors": [
        {
            "name": "string",
            "type": "direct | indirect",
            "strengths": "string",
            "weaknesses": "string",
            "scores": {
                "features": "1-10",
                "pricing": "1-10",
                "ux": "1-10",
                "market_reach": "1-10",
                "brand_trust": "1-10",
            },
        }
    ],
    "product_scores": {
        "features": "1-10",
        "pricing": "1-10",
        "ux": "1-10",
        "market_reach": "1-10",
        "brand_trust": "1-10",
    },
    "competitive_advantages": ["Metric where the product leads and why"],
    "competitive_gaps": ["Metric where the product trails and remediation"],
    "market_size": {"tam": "string", "sam": "string", "som": "string"},
    "growth_drivers": ["driver 1", "driver 2"],
    "barriers": ["barrier 1"],
    "timing_assessment": "Why now is (or isn't) the right time to launch",
    "opportunities": ["opportunity 1"],
}

CUSTOMER_SCHEMA = {
    "segments": [
        {"name": "string", "priority": "primary | secondary", "size": "string"}
    ],
    "personas": [
        {
            "name": "string",
            "demographics": "string",
            "psychographics": "string",
            "jobs_to_be_done": ["string"],
            "pain_points": ["string"],
        }
    ],
    "buying_journey": "Stages from awareness to purchase",
    "decision_criteria": ["criterion 1"],
    "adoption_barriers": ["barrier 1"],
}

POSITIONING_SCHEMA = {
    "positioning_statement": "For [target] who [need], [product] is [category] that [benefit]",
    "category": "Market category the product owns",
    "messaging_framework": [
        {"segment": "string", "headline": "string", "supporting_points": ["string"]}
    ],
    "value_propositions": ["value prop 1"],
    "differentiators": ["differentiator 1"],
    "proof_points": ["proof point 1"],
}

GTM_SCHEMA = {
    "channel_strategy": [
        {"channel": "string", "type": "organic | paid | partnership", "rationale": "string"}
    ],
    "campaigns": [
        {"segment": "string", "concept": "string", "channels": ["string"]}
    ],
    "launch_plan": {
        "day_1_30": {
            "theme": "string — overarching focus for this phase",
            "goals": ["measurable goal"],
            "activities": ["activity"],
            "channels": ["channel"],
            "kpis": ["KPI with target"],
        },
        "day_31_60": {
            "theme": "string",
            "goals": ["measurable goal"],
            "activities": ["activity"],
            "channels": ["channel"],
            "kpis": ["KPI with target"],
        },
        "day_61_90": {
            "theme": "string",
            "goals": ["measurable goal"],
            "activities": ["activity"],
            "channels": ["channel"],
            "kpis": ["KPI with target"],
        },
    },
    "budget_allocation": [
        {
            "channel": "string",
            "percentage": "number",
            "amount_usd": "number",
            "expected_roi": "string (e.g. 3.2x)",
            "rationale": "string",
        }
    ],
    "total_budget_usd": "number — sum of all channel amounts",
    "budget_rationale": "Why this total is appropriate for the launch",
    "kpis": ["KPI 1"],
    "contingencies": ["contingency 1"],
}


def build_market_task(agent: Agent, product: str) -> Task:
    return Task(
        description=(
            f"Analyze the market landscape, competitors, and dynamics for: {product}\n\n"
            "Cover the industry overview, direct and indirect competitors with "
            "their strengths and weaknesses, total addressable market "
            "(TAM/SAM/SOM), growth drivers, barriers to entry, timing "
            "assessment, and key opportunities.\n\n"
            "COMPETITIVE SCORECARD: Score the product AND each competitor on "
            "five metrics (1-10 scale): features, pricing, ux, market_reach, "
            "brand_trust. Populate the 'scores' object for each competitor "
            "and the top-level 'product_scores' object. Then list "
            "'competitive_advantages' (metrics where the product leads) and "
            "'competitive_gaps' (metrics where it trails, with remediation "
            "ideas). Ground every score in market reasoning.\n\n"
            "Return your output as a single JSON object matching this schema:\n"
            f"{json.dumps(MARKET_SCHEMA, indent=2)}\n\n"
            "Return ONLY the JSON object — no markdown fences, no commentary."
        ),
        expected_output="A JSON object matching the market schema.",
        agent=agent,
    )


def build_customer_task(agent: Agent, market_task: Task) -> Task:
    return Task(
        description=(
            "Using the market research from the previous analysis, define "
            "target customer segments and detailed personas.\n\n"
            "Identify primary and secondary segments with sizing. Build "
            "personas with demographics, psychographics, jobs-to-be-done, and "
            "pain points. Map the buying journey, decision criteria, and "
            "adoption barriers for each segment.\n\n"
            "Return your output as a single JSON object matching this schema:\n"
            f"{json.dumps(CUSTOMER_SCHEMA, indent=2)}\n\n"
            "Return ONLY the JSON object — no markdown fences, no commentary."
        ),
        expected_output="A JSON object matching the customer schema.",
        agent=agent,
        context=[market_task],
    )


def build_positioning_task(
    agent: Agent, market_task: Task, customer_task: Task
) -> Task:
    return Task(
        description=(
            "Using the market analysis and customer personas, define product "
            "positioning, messaging framework, and competitive differentiation.\n\n"
            "Craft a positioning statement, define the market category, build "
            "a messaging framework per segment with headlines and supporting "
            "points, list value propositions, competitive differentiators, and "
            "proof points. Every element should trace back to customer needs "
            "and competitive gaps identified earlier.\n\n"
            "Return your output as a single JSON object matching this schema:\n"
            f"{json.dumps(POSITIONING_SCHEMA, indent=2)}\n\n"
            "Return ONLY the JSON object — no markdown fences, no commentary."
        ),
        expected_output="A JSON object matching the positioning schema.",
        agent=agent,
        context=[market_task, customer_task],
    )


def build_gtm_task(
    agent: Agent,
    market_task: Task,
    customer_task: Task,
    positioning_task: Task,
) -> Task:
    return Task(
        description=(
            "Synthesize all prior analyses — market research, customer "
            "personas, and positioning strategy — into a detailed go-to-market "
            "execution plan.\n\n"
            "Define channel strategy (organic, paid, partnerships) with "
            "rationale and campaign concepts per segment.\n\n"
            "Build a 30-60-90 day launch plan:\n"
            "- Day 1-30: pre-launch and early traction activities, goals, "
            "channels, and KPIs with concrete targets.\n"
            "- Day 31-60: growth acceleration activities, goals, channels, "
            "and KPIs with concrete targets.\n"
            "- Day 61-90: optimization and scale activities, goals, channels, "
            "and KPIs with concrete targets.\n"
            "Each phase needs a theme that summarises the focus.\n\n"
            "For budget allocation: estimate a total launch budget in USD, "
            "then break it down by channel with dollar amounts, percentage "
            "share, and expected ROI (e.g. '3.2x'). Provide a brief "
            "budget_rationale explaining why the total is appropriate.\n\n"
            "Include risk contingencies. Justify every allocation by "
            "referencing specific findings from earlier reports.\n\n"
            "Return your output as a single JSON object matching this schema:\n"
            f"{json.dumps(GTM_SCHEMA, indent=2)}\n\n"
            "Return ONLY the JSON object — no markdown fences, no commentary."
        ),
        expected_output="A JSON object matching the GTM schema.",
        agent=agent,
        context=[market_task, customer_task, positioning_task],
    )
