# Data Analysis Agent — Architecture

## Overview

The Data Analysis Agent is a LangGraph-based cyclic graph that takes a natural-language analytics question and a dataset, decomposes it into executable operations, runs them as Python code against the data, explains the results, and decides whether the analysis is complete or needs refinement. Each node is a pure function that receives the current graph state, performs one focused task, and returns a state update. LangGraph manages execution order, the conditional retry loop, and iteration tracking — there is no custom orchestrator.

Core principle: **LLM plans, Python executes.** The LLM never sees raw data rows. It produces structured operation plans and receives only computed results (aggregates, statistics, column metadata). All data manipulation runs as deterministic Python code.

Primary flow:

```
START → planner → executor → analyzer → evaluator → (retry execution OR END)
```

## Graph State

All data flows through a single `TypedDict` that every node can read and update. LangGraph merges the partial dicts returned by each node into the running state automatically.

```python
class AnalysisState(TypedDict):
    query: str                # Original user analytics question
    plan: list[dict]          # Structured operations produced by planner
    execution_result: dict    # Output from Python execution (data, stats, errors)
    explanation: str          # Human-readable interpretation of results
    iteration: int            # Current plan-execute cycle count (starts at 0)
    success: bool             # True when evaluator accepts the analysis
```

### State design rules

- `query` is immutable after graph invocation — no node overwrites it.
- `plan` is a list of structured operation dicts (e.g., `{"operation": "group_by", "column": "region", "agg": "sum", "target": "revenue"}`). The planner produces it; the evaluator may request a revised plan on retry.
- `execution_result` is overwritten each iteration with the latest output. It contains `{"data": ..., "columns": [...], "shape": [...], "error": str | None}`.
- `explanation` is only populated by the analyzer node after successful execution.
- `iteration` and `success` drive the conditional edge after the evaluator node.

## Nodes

Each node is a regular Python function with the signature `(state: AnalysisState) -> dict`. It returns only the keys it modifies.

### planner

Decomposes the user's analytics question into a sequence of structured data operations.

- **Reads:** `query`, `execution_result` (on retry, to see what failed)
- **Writes:** `plan`
- **Model:** `gemini-3.1-pro-preview` — decomposing ambiguous natural-language questions into precise, ordered operations requires strong reasoning. The model must infer groupings, filters, aggregations, and joins from context.
- **Output:** A list of operation dicts. Each dict specifies the operation type, target columns, parameters, and expected output shape. Example:
  ```python
  [
      {"operation": "filter", "column": "date", "condition": ">=", "value": "2024-01-01"},
      {"operation": "group_by", "column": "category", "agg": "mean", "target": "sales"},
      {"operation": "sort", "column": "sales", "order": "descending"},
  ]
  ```
- **Behavior on retry:** Reads `execution_result["error"]` to understand why the previous plan failed, and produces a revised plan that avoids the same mistake.

### executor

Translates the structured plan into Python code and executes it against the loaded dataset.

- **Reads:** `plan`
- **Writes:** `execution_result`
- **Model:** None — this node is deterministic. It maps operation dicts to pandas/Python calls and runs them. No LLM is involved.
- **Execution:**
  1. Load the dataset via `data_loader` (CSV, JSON, or Parquet).
  2. Iterate through `plan` operations in order, applying each as a pandas transformation.
  3. Capture the result: computed DataFrame or Series, column names, shape, and any error.
  4. Return `{"data": result_dict, "columns": [...], "shape": [rows, cols], "error": None}` on success, or `{"data": None, "columns": [], "shape": [], "error": "description"}` on failure.
- **Safety:** All execution runs against an in-memory DataFrame copy. No file writes, no network calls, no `exec()`/`eval()` of LLM-generated code. Operations are mapped from a fixed allowlist of pandas methods.

### analyzer

Interprets the execution results and generates a human-readable explanation.

- **Reads:** `query`, `plan`, `execution_result`
- **Writes:** `explanation`
- **Model:** `gemini-3-flash-preview` — explanation generation is a synthesis and formatting task. The heavy reasoning (planning, operation selection) is already done. Speed and fluency matter more than raw reasoning here.
- **Output:** A clear, structured explanation that answers the original query using the computed results. Includes key findings, notable patterns, and caveats about the data.
- **Guard:** If `execution_result["error"]` is not None, the analyzer skips explanation and returns an empty string — the evaluator will handle the failure.

### evaluator

Decides whether the analysis is complete or another iteration is needed.

- **Reads:** `query`, `plan`, `execution_result`, `explanation`, `iteration`
- **Writes:** `success`, `iteration`
- **Model:** `gemini-3.1-pro-preview` — judging whether results actually answer the user's question requires reasoning about completeness, correctness, and relevance.
- **Logic:**
  1. If `execution_result["error"]` is not None and `iteration < MAX_ITERATIONS`, set `success = False`, increment `iteration`, and return — the planner will revise.
  2. If the explanation adequately answers `query` and the results are coherent, set `success = True`.
  3. If the analysis is incomplete (e.g., the plan missed a required aggregation) and `iteration < MAX_ITERATIONS`, set `success = False` and increment `iteration`.
  4. If `iteration >= MAX_ITERATIONS`, set `success = True` (force exit) and allow the current best explanation to stand.

## Graph Transitions

### Edge map

| From | To | Condition |
|---|---|---|
| `START` | `planner` | Always |
| `planner` | `executor` | Always |
| `executor` | `analyzer` | Always |
| `analyzer` | `evaluator` | Always |
| `evaluator` | `planner` | `success is False AND iteration < MAX_ITERATIONS` |
| `evaluator` | `END` | `success is True OR iteration >= MAX_ITERATIONS` |

### Conditional edge after evaluator

This is the only branching point in the graph. It is implemented as a LangGraph conditional edge:

```python
MAX_ITERATIONS = 3

def route_after_evaluator(state: AnalysisState) -> str:
    if state["success"] or state["iteration"] >= MAX_ITERATIONS:
        return "end"
    return "planner"

graph.add_conditional_edges("evaluator", route_after_evaluator, {
    "end": END,
    "planner": "planner",
})
```

`MAX_ITERATIONS` (default: 3) prevents infinite loops. When the limit is reached, the graph terminates with the best explanation produced so far.

### Why this topology works

- **LLM plans, Python executes.** The planner reasons about what operations to perform; the executor runs deterministic code. The LLM never touches raw data.
- **Targeted retry loop.** On failure, the evaluator routes back to the planner with error context, allowing a revised plan. The executor and analyzer simply re-run with the new plan.
- **Deterministic routing.** The conditional edge reads two scalar fields (`success`, `iteration`). There is no LLM call in the routing logic.
- **Graceful degradation.** Hitting `MAX_ITERATIONS` does not crash the graph — it terminates with the last explanation and a clear indication if issues remain.

## Model Usage

| Model | Nodes | Rationale |
|---|---|---|
| `gemini-3.1-pro-preview` | planner, evaluator | Query decomposition and completeness evaluation require strong reasoning about data operations and analytical correctness |
| `gemini-3-flash-preview` | analyzer | Result explanation is a synthesis task; speed and fluency matter more than deep reasoning |
| None (deterministic) | executor | Pure Python/pandas execution — no LLM involved |

### Cost and latency considerations

- The planner and evaluator account for most token usage since they may run up to `MAX_ITERATIONS` times each.
- The executor node has zero LLM cost — it is pure code execution against pandas.
- The analyzer uses the cheaper, faster model and runs once per iteration.
- Setting `MAX_ITERATIONS` to 3 keeps total cost bounded at a maximum of 9 LLM calls (3 planner + 3 analyzer + 3 evaluator).

## Graph Construction

```python
from langgraph.graph import StateGraph, START, END

graph = StateGraph(AnalysisState)

# Add nodes
graph.add_node("planner", planner_node)
graph.add_node("executor", executor_node)
graph.add_node("analyzer", analyzer_node)
graph.add_node("evaluator", evaluator_node)

# Linear edges
graph.add_edge(START, "planner")
graph.add_edge("planner", "executor")
graph.add_edge("executor", "analyzer")
graph.add_edge("analyzer", "evaluator")

# Conditional retry loop
graph.add_conditional_edges("evaluator", route_after_evaluator, {
    "end": END,
    "planner": "planner",
})

app = graph.compile()
```

Invocation:

```python
result = app.invoke({
    "query": "What is the average revenue by region for Q4 2024?",
    "plan": [],
    "execution_result": {},
    "explanation": "",
    "iteration": 0,
    "success": False,
})
print(result["explanation"])
print("Success:", result["success"])
```

## Production Design Notes

### Data Safety

The executor node is the primary security boundary. All data operations must be controlled:

- **Allowlisted operations.** The executor maps plan dicts to a fixed set of pandas methods (filter, group_by, sort, aggregate, pivot, merge). Arbitrary code strings from the LLM are never executed.
- **In-memory only.** All operations run on an in-memory DataFrame copy. No writes to disk or network.
- **No eval/exec.** The executor never calls `eval()` or `exec()` on LLM-generated content. Operations are dispatched by matching operation type strings to handler functions.
- **Column validation.** Before executing any operation, the executor validates that referenced columns exist in the DataFrame. Missing columns produce a clear error in `execution_result` rather than an exception.

### Observability

- Each node should log its input keys, output keys, token count, and latency.
- `iteration` and `success` provide a built-in audit trail of retry attempts.
- The full sequence of `plan → execution_result → explanation` per iteration should be captured for post-mortem review.
- LangGraph's built-in tracing (LangSmith integration) can be enabled for full run visualization.

### Error Handling

- Wrap each node's LLM call in a retry with exponential backoff (max 2 retries per call).
- If the executor encounters a pandas error (bad column name, type mismatch, empty result), populate `execution_result["error"]` with the details rather than raising — the evaluator will route back to the planner for a revised plan.
- If a node fails after retries, set `success = False` and route to END with the best available explanation.

### Configuration

Key parameters should be externalized:

| Parameter | Default | Purpose |
|---|---|---|
| `MAX_ITERATIONS` | 3 | Cap on planner → executor → analyzer → evaluator retry cycles |
| `REASONING_MODEL` | `gemini-3.1-pro-preview` | Model for planner, evaluator |
| `EXPLANATION_MODEL` | `gemini-3-flash-preview` | Model for analyzer |
| `MAX_PLAN_STEPS` | 10 | Upper bound on operations in a single plan |
| `SUPPORTED_FORMATS` | `["csv", "json", "parquet"]` | File formats accepted by data_loader |

### Testing

- Each node is a pure function of state — unit test by passing a constructed `AnalysisState` dict and asserting the returned keys.
- Integration test the full graph with a mock LLM that returns canned plans and explanations, and a small test DataFrame, verifying the correct node sequence fires.
- Test the conditional edge by asserting `route_after_evaluator` returns `"planner"` when `success=False` and `iteration < MAX_ITERATIONS`, and `"end"` otherwise.
- Test the retry loop by mocking the executor to return an error for N iterations then succeed, and verify `iteration` matches expected count.
- Test the executor's allowlist by confirming that unsupported operation types produce a clear error rather than executing arbitrary code.

## Summary

The system is a four-node LangGraph `StateGraph` with one conditional retry loop. The planner decomposes the query into structured operations, the executor runs them as deterministic Python against pandas, the analyzer explains the results, and the evaluator decides whether to retry or terminate. State is a flat `TypedDict` passed through the graph — no shared memory service, no custom orchestrator. The conditional edge after the evaluator is the only branching logic, controlled by `success` and `iteration`. The LLM never touches raw data: it plans operations, and Python executes them.