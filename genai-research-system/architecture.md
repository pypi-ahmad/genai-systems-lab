# Architecture

## Overview

The Multi-Agent Research System is a LangGraph-based directed graph where four specialized nodes collaborate to transform a user query into a polished research report. Each node is a pure function that receives the current graph state, performs one focused task, and returns a state update. LangGraph manages execution order, conditional branching, and the iterative critic loop — there is no custom orchestrator.

Primary flow:

```
START → planner → researcher → critic → (loop back to researcher OR continue) → writer → END
```

## Graph State

All data flows through a single `TypedDict` that every node can read and update. LangGraph merges the partial dicts returned by each node into the running state automatically.

```python
class ResearchState(TypedDict):
    query: str              # Original user research question
    plan: list[str]         # Ordered research sub-tasks produced by planner
    findings: list[str]     # Evidence and analysis collected by researcher
    critiques: list[str]    # Issues and gaps identified by critic
    revision_count: int     # Number of researcher ↔ critic iterations so far
    approved: bool          # True when critic accepts findings
    final_output: str       # Formatted report produced by writer
```

### State design rules

- Fields are additive — nodes append to lists rather than overwrite, preserving full history.
- `revision_count` and `approved` drive the conditional edge after the critic node.
- `final_output` is only populated by the writer node as the last step.

## Nodes

Each node is a regular Python function with the signature `(state: ResearchState) -> dict`. It returns only the keys it modifies.

### planner

Decomposes `state["query"]` into a structured list of research sub-tasks.

- **Reads:** `query`
- **Writes:** `plan`
- **Model:** `gemini-3.1-pro-preview` — requires strong reasoning to identify scope, prioritize sub-tasks, and detect implicit requirements.
- **Output:** A list of 3–7 concrete, bounded research tasks.

### researcher

Executes the research plan (or addresses critique feedback on subsequent passes).

- **Reads:** `query`, `plan`, `critiques` (if revision pass)
- **Writes:** `findings`
- **Model:** `gemini-3.1-pro-preview` — needs deep reasoning to synthesize evidence, compare sources, and incorporate critique.
- **Behavior on first pass:** Works through each sub-task in `plan` and produces detailed findings.
- **Behavior on revision pass:** Reads `critiques`, identifies weak or missing areas in `findings`, and produces an improved version.

### critic

Reviews the current findings for accuracy, depth, evidence gaps, and coherence.

- **Reads:** `query`, `plan`, `findings`
- **Writes:** `critiques`, `revision_count`, `approved`
- **Model:** `gemini-3.1-pro-preview` — evaluation and gap analysis require the strongest reasoning model.
- **Logic:**
  1. Evaluate findings against the plan and original query.
  2. If all sub-tasks are adequately covered and no major issues remain, set `approved = True` and return empty critiques.
  3. Otherwise, set `approved = False`, increment `revision_count`, and return a list of specific, actionable critiques.

### writer

Synthesizes approved findings into a final structured report.

- **Reads:** `query`, `plan`, `findings`, `critiques`
- **Writes:** `final_output`
- **Model:** `gemini-3-flash-preview` — optimized for fast, fluent text generation; reasoning work is already done.
- **Output:** A Markdown report with title, executive summary, sections per sub-task, and a conclusion.

## Graph Transitions

### Edge map

| From | To | Condition |
|---|---|---|
| `START` | `planner` | Always |
| `planner` | `researcher` | Always |
| `researcher` | `critic` | Always |
| `critic` | `researcher` | `approved is False AND revision_count < MAX_REVISIONS` |
| `critic` | `writer` | `approved is True OR revision_count >= MAX_REVISIONS` |
| `writer` | `END` | Always |

### Conditional edge after critic

This is the only branching point in the graph. It is implemented as a LangGraph conditional edge:

```python
def route_after_critic(state: ResearchState) -> str:
    if state["approved"] or state["revision_count"] >= MAX_REVISIONS:
        return "writer"
    return "researcher"

graph.add_conditional_edges("critic", route_after_critic, {
    "writer": "writer",
    "researcher": "researcher",
})
```

`MAX_REVISIONS` (default: 3) prevents infinite loops. When the limit is reached, the writer proceeds with the best available findings and notes any unresolved critiques.

### Why this topology works

- **No wasted calls.** The planner runs once. The researcher and critic iterate only when quality is insufficient.
- **Deterministic routing.** The conditional edge reads two scalar fields (`approved`, `revision_count`). There is no LLM call in the routing logic.
- **Graceful degradation.** Hitting `MAX_REVISIONS` does not crash the graph — it funnels into the writer with whatever findings exist.

## Model Usage

| Model | Nodes | Rationale |
|---|---|---|
| `gemini-3.1-pro-preview` | planner, researcher, critic | Planning, deep research synthesis, and critical evaluation all require strong reasoning |
| `gemini-3-flash-preview` | writer | Report generation is a formatting and synthesis task; speed and fluency matter more than raw reasoning |

### Cost and latency considerations

- The researcher and critic nodes account for most token usage since they may run multiple times.
- Setting `MAX_REVISIONS` to 2–3 keeps the total cost bounded while allowing meaningful improvement.
- The writer runs exactly once and uses the cheaper, faster model.

## Graph Construction

```python
from langgraph.graph import StateGraph, START, END

graph = StateGraph(ResearchState)

# Add nodes
graph.add_node("planner", planner_node)
graph.add_node("researcher", researcher_node)
graph.add_node("critic", critic_node)
graph.add_node("writer", writer_node)

# Linear edges
graph.add_edge(START, "planner")
graph.add_edge("planner", "researcher")
graph.add_edge("researcher", "critic")
graph.add_edge("writer", END)

# Conditional loop
graph.add_conditional_edges("critic", route_after_critic, {
    "writer": "writer",
    "researcher": "researcher",
})

app = graph.compile()
```

Invocation:

```python
result = app.invoke({"query": "Compare transformer and SSM architectures for long-context tasks"})
print(result["final_output"])
```

## Production Design Notes

### Observability

- Each node should log its input keys, output keys, token count, and latency.
- `revision_count` and `critiques` provide a built-in audit trail of quality iterations.
- LangGraph's built-in tracing (LangSmith integration) can be enabled for full run visualization.

### Error handling

- Wrap each node's LLM call in a retry with exponential backoff.
- If a node fails after retries, set a `status: "error"` field in state and route to the writer, which produces a partial report with an error notice.

### Configuration

Key parameters should be externalized:

| Parameter | Default | Purpose |
|---|---|---|
| `MAX_REVISIONS` | 3 | Cap on researcher ↔ critic iterations |
| `REASONING_MODEL` | `gemini-3.1-pro-preview` | Model for planner, researcher, critic |
| `WRITING_MODEL` | `gemini-3-flash-preview` | Model for writer |
| `MAX_PLAN_TASKS` | 7 | Upper bound on planner sub-tasks |

### Testing

- Each node is a pure function of state — unit test by passing a constructed `ResearchState` dict and asserting the returned keys.
- Integration test the full graph with a mock LLM that returns canned responses, verifying the correct node sequence fires.
- Test the conditional edge by asserting `route_after_critic` returns `"researcher"` when `approved=False` and `"writer"` when `approved=True` or at the revision limit.

## Summary

The system is a four-node LangGraph `StateGraph` with one conditional loop. The planner decomposes the query, the researcher produces findings, the critic gates quality through an approval flag, and the writer formats the final output. State is a flat `TypedDict` passed through the graph — no shared memory service, no custom orchestrator. The conditional edge after the critic is the only branching logic, controlled by `approved` and `revision_count`.
