"""Task definitions for the Investment Analysis Crew."""

import json

from crewai import Agent, Task

MARKET_SCHEMA = {
    "industry_overview": "High-level description of the industry",
    "growth_drivers": ["driver 1", "driver 2"],
    "competitive_positioning": "Where the target sits vs. peers",
    "market_size": "Total addressable market estimate",
    "headwinds": ["headwind 1"],
    "tailwinds": ["tailwind 1"],
    "sector_outlook": "Bullish / Neutral / Bearish with reasoning",
    "market_attractiveness_score": "integer 1-10 (1 = very unattractive, 10 = extremely attractive)",
}

FINANCIAL_SCHEMA = {
    "revenue_trends": "Revenue trajectory description",
    "profitability_margins": {"gross": "string", "operating": "string", "net": "string"},
    "debt_structure": "Debt/equity overview",
    "cash_flow": "Free cash flow analysis",
    "valuation_multiples": {"pe": "string", "ev_ebitda": "string", "p_fcf": "string"},
    "peer_comparison": "How metrics compare to industry peers",
    "financial_strength_score": "integer 1-10 (1 = very weak, 10 = exceptionally strong)",
}

RISK_SCHEMA = {
    "risks": [
        {
            "type": "market | financial | regulatory | operational",
            "description": "string",
            "probability": "high | medium | low",
            "impact": "high | medium | low",
        }
    ],
    "concentration_risks": ["string"],
    "regulatory_exposure": "string",
    "mitigations": ["string"],
    "risk_level_score": "integer 1-10 (1 = very low risk, 10 = extremely high risk)",
}

SCENARIO_SCHEMA = {
    "label": "string",
    "probability": "float 0.0-1.0",
    "return_estimate": "string (e.g. +40%, -25%)",
    "key_assumptions": ["assumption 1", "assumption 2"],
    "catalysts": ["catalyst 1"],
    "risks": ["risk 1"],
}

STRATEGY_SCHEMA = {
    "decision": "invest | hold | avoid",
    "confidence": "float 0.0-1.0",
    "reasons": ["reason 1", "reason 2"],
    "thesis": "One-paragraph investment thesis",
    "best_case": SCENARIO_SCHEMA,
    "worst_case": SCENARIO_SCHEMA,
    "catalysts": ["catalyst 1", "catalyst 2"],
    "position_sizing": "Rationale for allocation size",
    "entry_criteria": "string",
    "exit_criteria": "string",
    "time_horizon": "string",
}

CHALLENGE_SCHEMA = {
    "challenge_items": [
        {
            "claim": "The specific claim or assumption being challenged",
            "counter_argument": "Why this claim may be wrong or overstated",
            "severity": "high | medium | low",
            "supporting_evidence": "Evidence or reasoning backing the challenge",
        }
    ],
    "overall_risk_adjusted_view": "Summary of risk-adjusted perspective",
    "recommended_adjustments": ["adjustment 1", "adjustment 2"],
    "risk_reward_verdict": "favorable | neutral | unfavorable",
}


def build_market_task(agent: Agent, target: str) -> Task:
    return Task(
        description=(
            f"Analyze the industry and competitive landscape for: {target}\n\n"
            "Cover the industry overview, key growth drivers, competitive "
            "positioning of the target, total addressable market size, "
            "headwinds, tailwinds, and your sector outlook. Ground every "
            "claim in market reasoning — avoid generic statements.\n\n"
            "Return your output as a single JSON object matching this schema:\n"
            f"{json.dumps(MARKET_SCHEMA, indent=2)}\n\n"
            "Return ONLY the JSON object — no markdown fences, no commentary."
        ),
        expected_output="A JSON object matching the market schema.",
        agent=agent,
    )


def build_financial_task(agent: Agent, market_task: Task) -> Task:
    return Task(
        description=(
            "Using the market context from the previous analysis, evaluate the "
            "financial health, profitability, and valuation of the target.\n\n"
            "Analyze revenue trends, profitability margins (gross, operating, "
            "net), debt/equity structure, free cash flow, valuation multiples "
            "(P/E, EV/EBITDA, P/FCF), and compare against industry peers. "
            "If hard data is unavailable, state assumptions explicitly.\n\n"
            "Return your output as a single JSON object matching this schema:\n"
            f"{json.dumps(FINANCIAL_SCHEMA, indent=2)}\n\n"
            "Return ONLY the JSON object — no markdown fences, no commentary."
        ),
        expected_output="A JSON object matching the financial schema.",
        agent=agent,
        context=[market_task],
    )


def build_risk_task(agent: Agent, market_task: Task, financial_task: Task) -> Task:
    return Task(
        description=(
            "Using the market and financial analyses, identify and assess "
            "material risks across all dimensions.\n\n"
            "Categorize each risk by type (market, financial, regulatory, "
            "operational). Estimate probability and impact for each. Highlight "
            "concentration risks, regulatory exposure, and propose concrete "
            "mitigations. Be specific — vague risk statements are not useful.\n\n"
            "Return your output as a single JSON object matching this schema:\n"
            f"{json.dumps(RISK_SCHEMA, indent=2)}\n\n"
            "Return ONLY the JSON object — no markdown fences, no commentary."
        ),
        expected_output="A JSON object matching the risk schema.",
        agent=agent,
        context=[market_task, financial_task],
    )


def build_strategy_task(
    agent: Agent,
    market_task: Task,
    financial_task: Task,
    risk_task: Task,
) -> Task:
    return Task(
        description=(
            "Synthesize the market, financial, and risk analyses into a final "
            "investment recommendation.\n\n"
            "Return a decision (invest / hold / avoid) with a confidence "
            "score between 0.0 and 1.0, and a list of concrete reasons "
            "supporting that decision. Also include your investment thesis, "
            "key catalysts, position sizing rationale, entry and exit "
            "criteria, and time horizon.\n\n"
            "Simulate two scenarios:\n"
            "  - best_case: optimistic outcome with estimated return, "
            "probability, key assumptions, catalysts, and residual risks.\n"
            "  - worst_case: pessimistic outcome with estimated loss, "
            "probability, key assumptions, trigger risks, and mitigations.\n\n"
            "Justify every element by referencing specific findings from "
            "the prior analyses.\n\n"
            "Return your output as a single JSON object matching this schema:\n"
            f"{json.dumps(STRATEGY_SCHEMA, indent=2)}\n\n"
            "Return ONLY the JSON object — no markdown fences, no commentary."
        ),
        expected_output="A JSON object matching the strategy schema.",
        agent=agent,
        context=[market_task, financial_task, risk_task],
    )


def build_risk_challenge_task(
    agent: Agent,
    market_task: Task,
    financial_task: Task,
    risk_task: Task,
    strategy_task: Task,
) -> Task:
    return Task(
        description=(
            "You are the Risk Analyst. The Chief Investment Strategist has "
            "just issued their recommendation. Your job is to stress-test "
            "and challenge the strategy BEFORE the final decision is accepted.\n\n"
            "Review the strategy output and the underlying market, financial, "
            "and risk analyses. For each claim, assumption, or conclusion in "
            "the strategy that could be wrong, overstated, or missing nuance, "
            "produce a challenge item with:\n"
            "  - claim: the specific assertion being challenged\n"
            "  - counter_argument: why it may be flawed\n"
            "  - severity: high / medium / low\n"
            "  - supporting_evidence: data or reasoning backing your challenge\n\n"
            "Be rigorous and adversarial. Focus on:\n"
            "  - Over-optimistic return estimates or probabilities\n"
            "  - Under-estimated risks or missing tail risks\n"
            "  - Confirmation bias in the thesis\n"
            "  - Questionable assumptions in scenario analysis\n"
            "  - Position sizing that doesn't match the risk profile\n\n"
            "After listing all challenges, provide an overall risk-adjusted view, "
            "recommended adjustments, and a risk_reward_verdict "
            "(favorable / neutral / unfavorable).\n\n"
            "Return your output as a single JSON object matching this schema:\n"
            f"{json.dumps(CHALLENGE_SCHEMA, indent=2)}\n\n"
            "Return ONLY the JSON object — no markdown fences, no commentary."
        ),
        expected_output="A JSON object matching the challenge schema.",
        agent=agent,
        context=[market_task, financial_task, risk_task, strategy_task],
    )