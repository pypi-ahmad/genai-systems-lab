from __future__ import annotations

import time

from langgraph.graph import END, START, StateGraph

from app.nodes.critic import parallel_critic_node
from app.nodes.editor import editor_node
from app.nodes.formatter import formatter_node
from app.nodes.originality_checker import originality_checker_node
from app.nodes.planner import planner_node
from app.nodes.researcher import parallel_researcher_node
from app.nodes.writer import writer_node
from app.state import MAX_REVISIONS, ResearchState
from shared.api.step_events import emit_step
from shared.logging import get_logger


LOGGER = get_logger(__name__)


def _instrument_node(name: str, node_fn):
    def wrapped(state: ResearchState) -> dict:
        emit_step(name, "running")
        LOGGER.info("node started: %s", name)
        start = time.perf_counter()
        try:
            update = node_fn(state)
        except Exception as exc:
            elapsed_ms = (time.perf_counter() - start) * 1000
            emit_step(name, "error")
            LOGGER.exception(
                "node failed: %s",
                name,
                extra={"latency_ms": f"{elapsed_ms:.2f}", "error": str(exc)},
            )
            raise

        emit_step(name, "done")

        elapsed_ms = (time.perf_counter() - start) * 1000
        node_timings = dict(state.get("node_timings", {}) or {})
        node_timings[name] = round(elapsed_ms, 2)
        execution_trace = list(state.get("execution_trace", []) or [])
        execution_trace.append(
            {
                "node": name,
                "latency_ms": round(elapsed_ms, 2),
                "updated_keys": sorted(update.keys()),
                "status": "ok",
            }
        )
        LOGGER.info(
            "node completed: %s",
            name,
            extra={"latency_ms": f"{elapsed_ms:.2f}", "error": "-"},
        )

        merged = dict(update)
        merged["node_timings"] = node_timings
        merged["execution_trace"] = execution_trace
        return merged

    return wrapped


# ---------------------------------------------------------------------------
# Conditional routing after parallel critic
# ---------------------------------------------------------------------------

def route_after_critic(state: ResearchState) -> str:
    critiques = state.get("critiques", {})
    iteration = state.get("iteration", 0)

    if critiques and iteration < MAX_REVISIONS:
        return "researcher"

    return "writer"


def route_after_originality(state: ResearchState) -> str:
    feedback = state.get("originality_feedback", "")
    if feedback:
        return "writer"
    return "formatter"


def route_after_editor(state: ResearchState) -> str:
    feedback = state.get("editor_feedback", "")
    if feedback:
        return "writer"
    return "originality_checker"


# ---------------------------------------------------------------------------
# Graph assembly
# ---------------------------------------------------------------------------

def build_graph() -> StateGraph:
    graph = StateGraph(ResearchState)

    graph.add_node("planner", _instrument_node("planner", planner_node))
    graph.add_node("researcher", _instrument_node("researcher", parallel_researcher_node))
    graph.add_node("critic", _instrument_node("critic", parallel_critic_node))
    graph.add_node("writer", _instrument_node("writer", writer_node))
    graph.add_node("editor", _instrument_node("editor", editor_node))
    graph.add_node("originality_checker", _instrument_node("originality_checker", originality_checker_node))
    graph.add_node("formatter", _instrument_node("formatter", formatter_node))

    graph.add_edge(START, "planner")
    graph.add_edge("planner", "researcher")
    graph.add_edge("researcher", "critic")
    graph.add_conditional_edges("critic", route_after_critic, {
        "researcher": "researcher",
        "writer": "writer",
    })
    graph.add_edge("writer", "editor")
    graph.add_conditional_edges("editor", route_after_editor, {
        "writer": "writer",
        "originality_checker": "originality_checker",
    })
    graph.add_conditional_edges("originality_checker", route_after_originality, {
        "writer": "writer",
        "formatter": "formatter",
    })
    graph.add_edge("formatter", END)

    return graph.compile()
