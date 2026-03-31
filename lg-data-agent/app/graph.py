"""LangGraph workflow: planner → executor → analyzer → evaluator (with retry loop)."""

from __future__ import annotations

from langgraph.graph import StateGraph, START, END

from app.state import AnalysisState, MAX_ITERATIONS
from app.nodes.planner import planner_node
from app.nodes.executor import executor_node
from app.nodes.duckdb_executor import duckdb_executor_node
from app.nodes.analyzer import analyzer_node
from app.nodes.evaluator import evaluator_node
from shared.api.langgraph_events import instrument_node


def _route_after_evaluator(state: AnalysisState) -> str:
    if state.get("success"):
        return END
    if state.get("iteration", 0) >= MAX_ITERATIONS:
        return END
    return "planner"


def _route_after_planner(state: AnalysisState) -> str:
    if state.get("engine") == "duckdb":
        return "duckdb_executor"
    return "executor"


def build_graph():
    graph = StateGraph(AnalysisState)

    graph.add_node("planner", instrument_node("planner", planner_node))
    graph.add_node("executor", instrument_node("executor", executor_node))
    graph.add_node("duckdb_executor", instrument_node("duckdb_executor", duckdb_executor_node))
    graph.add_node("analyzer", instrument_node("analyzer", analyzer_node))
    graph.add_node("evaluator", instrument_node("evaluator", evaluator_node))

    graph.add_edge(START, "planner")
    graph.add_conditional_edges("planner", _route_after_planner)
    graph.add_edge("executor", "analyzer")
    graph.add_edge("duckdb_executor", "analyzer")
    graph.add_edge("analyzer", "evaluator")
    graph.add_conditional_edges("evaluator", _route_after_evaluator)

    return graph.compile()
