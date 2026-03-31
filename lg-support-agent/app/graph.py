from __future__ import annotations

from langgraph.graph import StateGraph, START, END

from app.state import SupportState
from app.nodes.classifier import classifier_node
from app.nodes.retriever import retriever_node
from app.nodes.responder import responder_node
from app.nodes.evaluator import evaluator_node
from app.nodes.escalation import escalation_node
from shared.api.langgraph_events import instrument_node


def _route_after_evaluator(state: SupportState) -> str:
    if state.get("escalate"):
        return "escalation"
    return END


def build_graph():
    graph = StateGraph(SupportState)

    graph.add_node("classifier", instrument_node("classifier", classifier_node))
    graph.add_node("retriever", instrument_node("retriever", retriever_node))
    graph.add_node("responder", instrument_node("responder", responder_node))
    graph.add_node("evaluator", instrument_node("evaluator", evaluator_node))
    graph.add_node("escalation", instrument_node("escalation", escalation_node))

    graph.add_edge(START, "classifier")
    graph.add_edge("classifier", "retriever")
    graph.add_edge("retriever", "responder")
    graph.add_edge("responder", "evaluator")
    graph.add_conditional_edges("evaluator", _route_after_evaluator, ["escalation", END])
    graph.add_edge("escalation", END)

    return graph.compile()