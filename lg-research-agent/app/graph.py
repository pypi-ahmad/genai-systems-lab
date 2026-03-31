from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from app.nodes.critic import critic_node
from app.nodes.planner import planner_node
from app.nodes.researcher import researcher_node
from app.nodes.writer import writer_node
from app.state import ResearchState
from shared.api.langgraph_events import instrument_node


def build_graph():
	graph = StateGraph(ResearchState)

	graph.add_node("planner", instrument_node("planner", planner_node))
	graph.add_node("researcher", instrument_node("researcher", researcher_node))
	graph.add_node("critic", instrument_node("critic", critic_node))
	graph.add_node("writer", instrument_node("writer", writer_node))

	graph.add_edge(START, "planner")
	graph.add_edge("planner", "researcher")
	graph.add_edge("researcher", "critic")
	graph.add_edge("critic", "writer")
	graph.add_edge("writer", END)

	return graph.compile()
