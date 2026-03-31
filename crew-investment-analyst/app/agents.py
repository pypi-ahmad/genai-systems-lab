"""Agent definitions for the Investment Analysis Crew."""

from crewai import Agent

REASONING_MODEL = "gemini/gemini-3.1-pro-preview"
SUMMARY_MODEL = "gemini/gemini-3-flash-preview"


def build_market_analyst() -> Agent:
    return Agent(
        role="Senior Market Analyst",
        goal=(
            "Assess industry trends, competitive landscape, market size, and "
            "growth drivers relevant to the investment target."
        ),
        backstory=(
            "Equity research analyst with 15 years covering multiple sectors. "
            "Specialized in identifying inflection points, secular trends, and "
            "competitive moats. Evaluates markets through both top-down macro "
            "and bottom-up industry lens."
        ),
        llm=REASONING_MODEL,
        verbose=True,
    )


def build_financial_analyst() -> Agent:
    return Agent(
        role="Senior Financial Analyst",
        goal=(
            "Analyze revenue trends, growth trajectory, profitability margins, "
            "valuation multiples, and cash flow health to determine the "
            "financial strength of the investment target."
        ),
        backstory=(
            "CFA charterholder with deep experience in fundamental analysis. "
            "Reads financial statements the way a mechanic reads engine "
            "diagnostics — identifying stress points, efficiency patterns, "
            "and sustainability of earnings."
        ),
        llm=REASONING_MODEL,
        verbose=True,
    )


def build_risk_analyst() -> Agent:
    return Agent(
        role="Senior Risk Analyst",
        goal=(
            "Identify material risks spanning market, financial, regulatory, "
            "and operational domains, and assess their probability and "
            "potential impact on the investment."
        ),
        backstory=(
            "Risk management professional who has worked across hedge funds "
            "and institutional investors. Thinks in terms of downside "
            "scenarios, tail risks, and correlation exposures. Skeptical by "
            "disposition — the job is to find what can go wrong."
        ),
        llm=REASONING_MODEL,
        verbose=True,
    )


def build_strategist() -> Agent:
    return Agent(
        role="Chief Investment Strategist",
        goal=(
            "Integrate market, financial, and risk analyses into a clear "
            "investment recommendation with conviction level, position sizing "
            "guidance, and entry/exit criteria."
        ),
        backstory=(
            "Portfolio manager who has allocated capital across market cycles. "
            "Balances quantitative rigor with qualitative judgment. Focuses on "
            "asymmetric risk/reward and catalysts that drive re-rating."
        ),
        llm=REASONING_MODEL,
        verbose=True,
    )
