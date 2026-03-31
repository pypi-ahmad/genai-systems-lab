"""LangGraph workflow — wires agent nodes into a compiled state graph.

Graph topology::

    START ─► planner ─► executor ─► validator ─┬─► reporter ─► END
                            ▲                  │
                            └── retry (max 2) ─┘

If validation fails and ``retry_count < MAX_RETRIES`` the graph loops
back to the executor.  Once retries are exhausted the reporter runs
with whatever partial results are available.
"""

from __future__ import annotations

import logging

from langgraph.graph import END, START, StateGraph

from src.agents.executor import execute_plan
from src.agents.planner import plan_analysis
from src.agents.reporter import generate_report
from src.agents.validator import validate_output
from src.schemas.state import AnalystState

logger = logging.getLogger(__name__)

MAX_RETRIES = 2


# ── Logging wrappers ─────────────────────────────────────────────

def _planner(state: AnalystState) -> dict:
    logger.info("Node [planner] — query: %.120s", state.get("user_query", ""))
    result = plan_analysis(state)
    logger.info("Node [planner] — plan produced (%d chars)", len(result.get("plan", "")))
    return result


def _executor(state: AnalystState) -> dict:
    logger.info("Node [executor] — attempt %d", state.get("retry_count", 0) + 1)
    result = execute_plan(state)
    if result.get("error"):
        logger.warning("Node [executor] — error: %.200s", result["error"])
    else:
        logger.info("Node [executor] — success (%d chars output)",
                     len(result.get("execution_result", "")))
    return result


def _validator(state: AnalystState) -> dict:
    logger.info("Node [validator] — validating execution output")
    result = validate_output(state)
    passed = result.get("validation_passed", False)
    logger.info("Node [validator] — passed=%s retry_count=%d",
                passed, result.get("retry_count", state.get("retry_count", 0)))
    return result


def _reporter(state: AnalystState) -> dict:
    logger.info("Node [reporter] — generating final report")
    result = generate_report(state)
    logger.info("Node [reporter] — report generated (%d chars)",
                len(result.get("final_report", "")))
    return result


# ── Conditional router ────────────────────────────────────────────

def _after_validator(state: AnalystState) -> str:
    """Route after validation: retry executor or proceed to reporter."""
    if state.get("validation_passed", False):
        return "reporter"

    retries = state.get("retry_count", 0)
    if retries >= MAX_RETRIES:
        logger.warning("Max retries (%d) reached — moving to reporter", MAX_RETRIES)
        return "reporter"

    logger.info("Retrying executor (attempt %d/%d)", retries + 1, MAX_RETRIES)
    return "executor"


# ── Graph construction ────────────────────────────────────────────

def build_graph() -> StateGraph:
    """Construct and compile the analysis workflow."""
    graph = StateGraph(AnalystState)

    graph.add_node("planner", _planner)
    graph.add_node("executor", _executor)
    graph.add_node("validator", _validator)
    graph.add_node("reporter", _reporter)

    graph.add_edge(START, "planner")
    graph.add_edge("planner", "executor")
    graph.add_edge("executor", "validator")
    graph.add_conditional_edges(
        "validator",
        _after_validator,
        {"executor": "executor", "reporter": "reporter"},
    )
    graph.add_edge("reporter", END)

    logger.info("Analysis workflow graph compiled")
    return graph.compile()


workflow = build_graph()
