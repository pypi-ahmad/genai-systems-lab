"""Crew assembly and execution for the Investment Analysis Crew."""

from crewai import Crew, Process

from app.agents import (
    build_financial_analyst,
    build_market_analyst,
    build_risk_analyst,
    build_strategist,
)
from app.tasks import (
    build_financial_task,
    build_market_task,
    build_risk_challenge_task,
    build_risk_task,
    build_strategy_task,
)


def build_crew(target: str, verbose: bool = True) -> Crew:
    market_analyst = build_market_analyst()
    financial_analyst = build_financial_analyst()
    risk_analyst = build_risk_analyst()
    strategist = build_strategist()

    market_task = build_market_task(market_analyst, target)
    financial_task = build_financial_task(financial_analyst, market_task)
    risk_task = build_risk_task(risk_analyst, market_task, financial_task)
    strategy_task = build_strategy_task(
        strategist, market_task, financial_task, risk_task
    )
    risk_challenge_task = build_risk_challenge_task(
        risk_analyst, market_task, financial_task, risk_task, strategy_task
    )

    return Crew(
        agents=[market_analyst, financial_analyst, risk_analyst, strategist, risk_analyst],
        tasks=[market_task, financial_task, risk_task, strategy_task, risk_challenge_task],
        process=Process.sequential,
        verbose=verbose,
    )


def run(target: str, verbose: bool = True) -> str:
    crew = build_crew(target, verbose)
    try:
        result = crew.kickoff(inputs={"target": target})
    except Exception as exc:
        raise RuntimeError(f"Crew execution failed: {exc}") from exc
    return str(result)