from __future__ import annotations

from langgraph.graph import StateGraph, START, END

from app.state import WorkflowState
from app.nodes.planner import planner_node
from app.nodes.executor import executor_node
from app.nodes.validator import validator_node
from app.nodes.checkpoint import checkpoint_node
from app.nodes.finalizer import finalizer_node
from shared.api.langgraph_events import instrument_node


def _route_after_checkpoint(state: WorkflowState) -> str:
    if state.get("completed", False):
        return "finalizer"
    return "executor"


def build_graph():
    graph = StateGraph(WorkflowState)

    graph.add_node("planner", instrument_node("planner", planner_node))
    graph.add_node("executor", instrument_node("executor", executor_node))
    graph.add_node("validator", instrument_node("validator", validator_node))
    graph.add_node("checkpoint", instrument_node("checkpoint", checkpoint_node))
    graph.add_node("finalizer", instrument_node("finalizer", finalizer_node))

    graph.add_edge(START, "planner")
    graph.add_edge("planner", "executor")
    graph.add_edge("executor", "validator")
    graph.add_edge("validator", "checkpoint")

    graph.add_conditional_edges("checkpoint", _route_after_checkpoint, {
        "executor": "executor",
        "finalizer": "finalizer",
    })

    graph.add_edge("finalizer", END)

    return graph.compile()
