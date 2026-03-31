from __future__ import annotations

from langgraph.graph import StateGraph, START, END

from app.state import MAX_ITERATIONS, DebugState
from app.nodes.analyzer import analyzer_node
from app.nodes.fixer import fixer_node
from app.nodes.case_generator import test_generator_node
from app.nodes.tester import tester_node
from app.nodes.evaluator import evaluator_node
from shared.api.langgraph_events import instrument_node


def route_after_evaluator(state: DebugState) -> str:
    if state.get("is_resolved") or state.get("iteration", 0) >= MAX_ITERATIONS:
        return "end"
    return "fixer"


def build_graph():
    graph = StateGraph(DebugState)

    graph.add_node("analyzer", instrument_node("analyzer", analyzer_node))
    graph.add_node("fixer", instrument_node("fixer", fixer_node))
    graph.add_node("test_generator", instrument_node("test_generator", test_generator_node))
    graph.add_node("tester", instrument_node("tester", tester_node))
    graph.add_node("evaluator", instrument_node("evaluator", evaluator_node))

    graph.add_edge(START, "analyzer")
    graph.add_edge("analyzer", "fixer")
    graph.add_edge("fixer", "test_generator")
    graph.add_edge("test_generator", "tester")
    graph.add_edge("tester", "evaluator")

    graph.add_conditional_edges("evaluator", route_after_evaluator, {
        "end": END,
        "fixer": "fixer",
    })

    return graph.compile()
