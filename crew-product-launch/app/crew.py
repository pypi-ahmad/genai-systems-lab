"""Crew assembly and execution for the Product Launch Strategy Crew."""

from crewai import Crew, Process

from app.agents import (
    build_customer_analyst,
    build_market_researcher,
    build_marketing_strategist,
    build_product_strategist,
)
from app.tasks import (
    build_customer_task,
    build_gtm_task,
    build_market_task,
    build_positioning_task,
)


def build_crew(product: str, verbose: bool = True) -> Crew:
    market_researcher = build_market_researcher()
    customer_analyst = build_customer_analyst()
    product_strategist = build_product_strategist()
    marketing_strategist = build_marketing_strategist()

    market_task = build_market_task(market_researcher, product)
    customer_task = build_customer_task(customer_analyst, market_task)
    positioning_task = build_positioning_task(
        product_strategist, market_task, customer_task
    )
    gtm_task = build_gtm_task(
        marketing_strategist, market_task, customer_task, positioning_task
    )

    return Crew(
        agents=[market_researcher, customer_analyst, product_strategist, marketing_strategist],
        tasks=[market_task, customer_task, positioning_task, gtm_task],
        process=Process.sequential,
        verbose=verbose,
    )


def run(product: str, verbose: bool = True) -> str:
    crew = build_crew(product, verbose)
    try:
        result = crew.kickoff()
    except Exception as exc:
        raise RuntimeError(f"Crew execution failed: {exc}") from exc
    return str(result)
