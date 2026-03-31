# Architecture

## Overview

The Customer Support Resolution Agent is a LangGraph-based directed graph where four specialized nodes process an incoming customer query and produce a verified response — or escalate to a human agent when confidence is insufficient. Each node is a pure function that receives the current graph state, performs one focused task, and returns a state update. LangGraph handles execution order and the single conditional branch; there is no custom orchestrator.

Primary flow:

```
START → classifier → retriever → responder → evaluator → END (or escalate)
```

## Graph State

All data flows through a single `TypedDict` that every node can read and update. LangGraph merges the partial dicts returned by each node into the running state automatically.

```python
class SupportState(TypedDict, total=False):
    query: str              # Raw customer message
    intent: str             # Classified intent label (e.g. "billing", "technical", "account")
    retrieved_docs: list[dict]  # Relevant KB articles retrieved for the classified intent
    response: str           # Generated customer-facing response
    confidence: float       # Evaluator's confidence score (0.0–1.0)
    escalate: bool          # True when the query must be handed to a human agent
```

### State design rules

- The flow is strictly linear — each node writes to a disjoint set of keys, so there are no race conditions or overwrites.
- `confidence` and `escalate` are set exclusively by the evaluator node and drive the single conditional edge.
- `total=False` allows nodes to return only the keys they modify.

## Nodes

Each node is a regular Python function with the signature `(state: SupportState) -> dict`. It returns only the keys it modifies.

### classifier

Determines the customer's intent from the raw query.

- **Reads:** `query`
- **Writes:** `intent`
- **Model:** `gemini-3.1-pro-preview` — intent classification requires strong reasoning to handle ambiguous, multi-intent, or poorly worded queries.
- **Output:** A single intent label from a fixed set (e.g. `"billing"`, `"technical"`, `"account"`, `"returns"`, `"general"`). The model is prompted with the allowed labels and must return exactly one.
- **Edge case:** If the query is unintelligible or maps to no known intent, the classifier sets `intent = "unknown"`.

### retriever

Fetches relevant knowledge base articles based on the classified intent and original query using embedding similarity.

- **Reads:** `query`, `intent`
- **Writes:** `retrieved_docs`
- **Model:** `gemini-embedding-2-preview` — used to embed the query and all KB articles. Article embeddings are computed lazily on the first search and cached in memory.
- **Retrieval:** Cosine similarity between the query embedding and each article embedding. When intent matches a known category, only articles in that category are scored. Falls back to searching all articles when the intent is unknown or yields no results above the threshold.
- **Output:** A list of article text strings, ranked by similarity. Returns the top-k results (default: `RETRIEVAL_TOP_K = 5`) filtered by `RELEVANCE_THRESHOLD = 0.3`.
- **Edge case:** If no documents match above the relevance threshold, returns an empty list. The downstream responder detects this and generates a generic fallback.

### responder

Generates a customer-facing response grounded in the retrieved documentation.

- **Reads:** `query`, `intent`, `retrieved_docs`
- **Writes:** `response`
- **Model:** `gemini-3-flash-preview` — response generation is a synthesis and formatting task; speed and tone matter more than deep reasoning.
- **Prompt strategy:** The retrieved docs are injected as context. The model is instructed to answer strictly from the provided material, cite article titles where applicable, and maintain a professional, empathetic tone.
- **Edge case:** When `retrieved_docs` is empty, the responder produces a polite acknowledgment and states that a human agent will follow up.

### evaluator

Assesses the quality and correctness of the generated response and decides whether to finalize or escalate.

- **Reads:** `query`, `intent`, `retrieved_docs`, `response`
- **Writes:** `confidence`, `escalate`
- **Model:** `gemini-3.1-pro-preview` — evaluation requires strong reasoning to detect hallucinations, unsupported claims, and tone issues.
- **Logic:**
  1. Score the response on a 0.0–1.0 scale across factual grounding, completeness, and tone.
  2. Compute a single `confidence` value (weighted average of the three scores).
  3. If `confidence >= CONFIDENCE_THRESHOLD`, set `escalate = False` — the response is safe to send.
  4. If `confidence < CONFIDENCE_THRESHOLD`, set `escalate = True` — route to human handoff.

## Graph Transitions

### Edge map

| From | To | Condition |
|---|---|---|
| `START` | `classifier` | Always |
| `classifier` | `retriever` | Always |
| `retriever` | `responder` | Always |
| `responder` | `evaluator` | Always |
| `evaluator` | `END` | Always (state contains the routing decision) |

### Conditional logic after evaluator

The evaluator is the only decision point. Rather than a conditional edge that routes to different nodes, the evaluator writes `escalate` into state. The caller inspects `escalate` after the graph completes to decide whether to deliver the response or hand off to a human queue.

```python
def evaluator_node(state: SupportState) -> dict:
    confidence = evaluate_response(
        query=state["query"],
        intent=state["intent"],
        docs=state["retrieved_docs"],
        response=state["response"],
    )
    return {
        "confidence": confidence,
        "escalate": confidence < CONFIDENCE_THRESHOLD,
    }
```

`CONFIDENCE_THRESHOLD` (default: 0.7) is the minimum confidence for automated delivery. Queries with `intent = "unknown"` or empty `retrieved_docs` will almost always fall below this threshold, triggering escalation.

### Why this topology works

- **Deterministic flow.** All four nodes execute in strict sequence — no branching, no loops. The graph always terminates in exactly four steps.
- **Single decision point.** Escalation is a state flag, not a graph fork. This keeps the graph simple and makes the decision auditable.
- **No wasted calls.** Every node runs exactly once. The evaluator is the quality gate at the end rather than a loop, keeping latency predictable.
- **Graceful degradation.** If retrieval returns nothing, the responder still produces a response and the evaluator escalates it. No node crashes on empty input.

## Model Usage

| Model | Nodes | Rationale |
|---|---|---|
| `gemini-3.1-pro-preview` | classifier, evaluator | Intent classification on ambiguous input and response evaluation both require strong reasoning |
| `gemini-3-flash-preview` | responder | Response generation from retrieved context is a synthesis task; speed and fluency matter more than raw reasoning |
| `gemini-embedding-2-preview` | retriever | Embedding similarity search against KB articles |

### Cost and latency considerations

- The graph makes exactly two `gemini-3.1-pro-preview` calls and one `gemini-3-flash-preview` call per query, plus one embedding call in the retriever.
- KB article embeddings are computed once on the first search and cached in memory; subsequent searches only embed the query.
- Total wall-clock time is dominated by the two pro-model calls. Running classifier and retriever sequentially (not in parallel) is intentional — the retriever needs the classified intent.

## Graph Construction

```python
from langgraph.graph import StateGraph, START, END

graph = StateGraph(SupportState)

# Add nodes
graph.add_node("classifier", classifier_node)
graph.add_node("retriever", retriever_node)
graph.add_node("responder", responder_node)
graph.add_node("evaluator", evaluator_node)

# Linear edges
graph.add_edge(START, "classifier")
graph.add_edge("classifier", "retriever")
graph.add_edge("retriever", "responder")
graph.add_edge("responder", "evaluator")
graph.add_edge("evaluator", END)

app = graph.compile()
```

Invocation:

```python
result = app.invoke({"query": "I was charged twice for my subscription last month"})

if result["escalate"]:
    route_to_human_queue(result)
else:
    send_response(result["response"])
```

## Production Design Notes

### Observability

- Each node should log its input keys, output keys, token count, and latency.
- `confidence` and `escalate` provide a built-in audit trail for every resolution decision.
- LangGraph's built-in tracing (LangSmith integration) can be enabled for full run visualization.
- Track escalation rate as a key metric — a rising rate signals knowledge base gaps or classifier drift.

### Error handling

- Wrap each node's LLM call in a retry with exponential backoff (max 3 attempts).
- If the classifier fails after retries, set `intent = "unknown"` and continue — the evaluator will escalate.
- If the responder fails, set `response = ""` and let the evaluator escalate.
- If the evaluator itself fails, default to `escalate = True` — fail safe, not silent.

### Configuration

Key parameters should be externalized:

| Parameter | Default | Purpose |
|---|---|---|
| `CONFIDENCE_THRESHOLD` | 0.7 | Minimum confidence to auto-deliver a response |
| `CLASSIFICATION_MODEL` | `gemini-3.1-pro-preview` | Model for classifier and evaluator |
| `RESPONSE_MODEL` | `gemini-3-flash-preview` | Model for responder |
| `RETRIEVAL_TOP_K` | 5 | Number of KB articles to retrieve |
| `RELEVANCE_THRESHOLD` | 0.3 | Minimum similarity score for retrieved docs |

### Testing

- Each node is a pure function of state — unit test by passing a constructed `SupportState` dict and asserting the returned keys.
- Integration test the full graph with a mock LLM that returns canned responses, verifying all four nodes fire in order.
- Test escalation by setting `confidence` below threshold and asserting `escalate is True`.
- Test the retriever independently with a seeded knowledge base and known queries.

## Summary

The system is a four-node LangGraph `StateGraph` with a strictly linear topology: classifier → retriever → responder → evaluator. There are no loops or conditional edges in the graph itself. The evaluator writes a `confidence` score and an `escalate` flag into state; the calling code inspects `escalate` after the graph completes to decide between automated delivery and human handoff. State is a flat `TypedDict` passed through the graph — no shared memory, no custom orchestrator, no branching logic inside the graph.