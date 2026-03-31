"""Crew assembly and execution for the Startup Team Simulator."""

from crewai import Crew, Process

from app.agents import build_ceo, build_cto, build_engineer, build_product_manager
from app.tasks import (
    build_architecture_task,
    build_execution_task,
    build_product_task,
    build_proposal_task,
    build_review_task,
    build_selection_task,
    build_vision_task,
)


def build_crew(idea: str, verbose: bool = True) -> Crew:
    ceo = build_ceo()
    pm = build_product_manager()
    cto = build_cto()
    engineer = build_engineer()

    # Brainstorming phase — each agent proposes a startup direction
    pm_proposal = build_proposal_task(pm, idea, "Product Manager")
    cto_proposal = build_proposal_task(cto, idea, "CTO")
    eng_proposal = build_proposal_task(engineer, idea, "Lead Engineer")

    # CEO evaluates all proposals and selects/synthesizes a direction
    selection_task = build_selection_task(
        ceo, [pm_proposal, cto_proposal, eng_proposal]
    )

    # Core pipeline — selection feeds into product spec onward
    product_task = build_product_task(pm, selection_task)
    architecture_task = build_architecture_task(cto, product_task)
    execution_task = build_execution_task(engineer, architecture_task)

    # Peer reviews — each agent critiques a different agent's output
    selection_review = build_review_task(pm, selection_task, "CEO")
    product_review = build_review_task(cto, product_task, "Product Manager")
    architecture_review = build_review_task(engineer, architecture_task, "CTO")
    execution_review = build_review_task(ceo, execution_task, "Engineer")

    return Crew(
        agents=[ceo, pm, cto, engineer],
        tasks=[
            pm_proposal,
            cto_proposal,
            eng_proposal,
            selection_task,
            product_task,
            architecture_task,
            execution_task,
            selection_review,
            product_review,
            architecture_review,
            execution_review,
        ],
        process=Process.sequential,
        verbose=verbose,
    )


def run(idea: str, verbose: bool = True) -> str:
    crew = build_crew(idea, verbose)
    try:
        result = crew.kickoff(inputs={"idea": idea})
    except Exception as exc:
        raise RuntimeError(f"Crew execution failed: {exc}") from exc
    return str(result)
