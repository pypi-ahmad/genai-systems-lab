# Workflow Automation Agent — Architecture

## Overview

The Workflow Automation Agent is a LangGraph-based cyclic graph that decomposes a high-level task into an ordered plan, executes each step sequentially, validates results, and checkpoints progress for resilience. Each node is a pure function that receives the current graph state, performs one focused task, and returns a state update. LangGraph manages execution order, conditional branching, and the step-iteration loop — there is no custom orchestrator.

Primary flow:

```
START → planner → executor → validator → checkpoint → (next step OR finalizer) → END
```

## Graph State

All data flows through a single `TypedDict` that every node can read and update. LangGraph merges the partial dicts returned by each node into the running state automatically.

```python
class WorkflowState(TypedDict):
    task: str                  # Original high-level task description
    plan: list[str]            # Ordered steps produced by planner
    current_step: int          # Index into plan (0-based)
    results: dict[str, str]    # Step name → execution output
    iteration: int             # Retry count for the current step (resets per step)
    completed: bool            # True when all steps finish or max retries exhausted
```

### State design rules

- `task` is immutable after graph invocation — no node overwrites it.
- `plan` is written once by the planner and read by all downstream nodes.
- `results` is additive — each successful step appends its output keyed by the step name. Failed retries do not overwrite prior successful entries.
- `current_step` advances only after a step passes validation and is checkpointed.
- `iteration` tracks retries for the current step and resets to 0 when `current_step` advances.
- `completed` drives the terminal condition and is set by the checkpoint node.

## Nodes

Each node is a regular Python function with the signature `(state: WorkflowState) -> dict`. It returns only the keys it modifies.

### planner

Decomposes `state["task"]` into a structured, ordered list of execution steps.

- **Reads:** `task`
- **Writes:** `plan`, `current_step`, `iteration`
- **Model:** `gemini-3.1-pro-preview` — requires strong reasoning to break down ambiguous tasks into concrete, sequentially-dependent steps with clear completion criteria.
- **Output:** A list of 3–10 actionable steps, each described as a single imperative sentence. Initializes `current_step` to 0 and `iteration` to 0.

### executor

Runs the current step from the plan using available tools and LLM reasoning.

- **Reads:** `task`, `plan`, `current_step`, `results` (prior step outputs for context)
- **Writes:** `results`
- **Model:** `gemini-3.1-pro-preview` — step execution may involve tool selection, multi-step reasoning, and incorporating prior results.
- **Behavior:** Reads `plan[current_step]`, builds a prompt that includes the original task, the full plan for context, prior results, and the specific step instruction. Stores the output in `results[plan[current_step]]`.
- **Tools:** Has access to `file_tool` (read/write files, list directories) and `analysis_tool` (compute metrics, parse structured data). The model decides which tools to invoke based on the step description.

### validator

Checks whether the executor's output for the current step meets quality and correctness criteria.

- **Reads:** `task`, `plan`, `current_step`, `results`, `iteration`
- **Writes:** `iteration`, `results` (may annotate with validation status)
- **Model:** `gemini-3.1-pro-preview` — evaluating correctness requires reasoning about whether the output satisfies the step's intent and is consistent with prior results.
- **Logic:**
  1. Compare the executor output against the step description and expected behavior.
  2. If valid, return without modifying `iteration` (checkpoint will advance the step).
  3. If invalid and `iteration < MAX_RETRIES`, increment `iteration` and annotate the result with feedback for the executor's next attempt.
  4. If invalid and `iteration >= MAX_RETRIES`, mark the step as best-effort and allow progression.

### checkpoint

Persists progress and decides whether to continue to the next step or finalize.

- **Reads:** `plan`, `current_step`, `iteration`, `results`
- **Writes:** `current_step`, `iteration`, `completed`
- **Model:** None — this node is deterministic. It manages state transitions, not LLM calls.
- **Logic:**
  1. If validation passed or max retries exhausted, advance `current_step` by 1 and reset `iteration` to 0.
  2. If `current_step >= len(plan)`, set `completed = True`.
  3. If validation failed and retries remain, do not advance (the loop returns to executor).
  4. Persist the current state snapshot for recovery. On restart, the graph resumes from the last checkpointed `current_step`.

### finalizer

Produces a summary of the completed workflow and all step results.

- **Reads:** `task`, `plan`, `results`, `completed`
- **Writes:** (terminal — output is the final state)
- **Model:** `gemini-3-flash-preview` — summarization is a formatting task; speed matters more than deep reasoning since all analytical work is done.
- **Output:** A structured report containing: task description, each step with its result, any steps that required retries, overall success/failure status, and recommendations for follow-up.

## Graph Transitions

### Edge map

| From | To | Condition |
|---|---|---|
| `START` | `planner` | Always |
| `planner` | `executor` | Always |
| `executor` | `validator` | Always |
| `validator` | `checkpoint` | Always |
| `checkpoint` | `executor` | `completed is False AND iteration > 0` (retry current step) |
| `checkpoint` | `executor` | `completed is False AND iteration == 0` (next step) |
| `checkpoint` | `finalizer` | `completed is True` |
| `finalizer` | `END` | Always |

### Conditional edge after checkpoint

This is the only branching point in the graph. It is implemented as a LangGraph conditional edge:

```python
MAX_RETRIES = 3

def route_after_checkpoint(state: WorkflowState) -> str:
    if state["completed"]:
        return "finalizer"
    return "executor"

graph.add_conditional_edges("checkpoint", route_after_checkpoint, {
    "finalizer": "finalizer",
    "executor": "executor",
})
```

The executor → validator → checkpoint cycle repeats for each step in the plan, and within each step for retries. `MAX_RETRIES` (default: 3) prevents infinite loops on any single step. When the limit is reached, the step is marked best-effort and the workflow advances.

### Why this topology works

- **Step-by-step execution.** Each plan step runs through the full executor → validator → checkpoint pipeline before the next step begins. This ensures sequential dependencies are respected.
- **Targeted retry loop.** Only the current step retries. Prior successful steps are preserved in `results` and never re-executed.
- **Deterministic routing.** The conditional edge reads two scalar fields (`completed`, `iteration`). There is no LLM call in the routing logic.
- **State persistence.** The checkpoint node snapshots progress after every step. On failure or restart, the graph resumes from the last completed step rather than starting over.
- **Graceful degradation.** Hitting `MAX_RETRIES` does not crash the graph — it advances with the best available result and the finalizer reports which steps required fallback.

## Model Usage

| Model | Nodes | Rationale |
|---|---|---|
| `gemini-3.1-pro-preview` | planner, executor, validator | Task decomposition, step execution with tool use, and result validation all require strong reasoning |
| `gemini-3-flash-preview` | finalizer | Report generation is a synthesis and formatting task; speed and cost efficiency matter more than raw reasoning |

### Cost and latency considerations

- The executor and validator account for most token usage since they run once per step and potentially `MAX_RETRIES` times per step.
- For a plan with N steps and no retries, the graph makes 1 (planner) + 2N (executor + validator) + 1 (finalizer) = 2N + 2 LLM calls.
- Worst case with retries: 1 + N × 2 × MAX_RETRIES + 1 = 6N + 2 calls (at MAX_RETRIES = 3).
- The checkpoint node has zero LLM cost — it is pure state management.
- The planner and finalizer each run exactly once.

## Graph Construction

```python
from langgraph.graph import StateGraph, START, END

graph = StateGraph(WorkflowState)

# Add nodes
graph.add_node("planner", planner_node)
graph.add_node("executor", executor_node)
graph.add_node("validator", validator_node)
graph.add_node("checkpoint", checkpoint_node)
graph.add_node("finalizer", finalizer_node)

# Linear edges
graph.add_edge(START, "planner")
graph.add_edge("planner", "executor")
graph.add_edge("executor", "validator")
graph.add_edge("validator", "checkpoint")
graph.add_edge("finalizer", END)

# Conditional loop / exit
graph.add_conditional_edges("checkpoint", route_after_checkpoint, {
    "finalizer": "finalizer",
    "executor": "executor",
})

app = graph.compile()
```

Invocation:

```python
result = app.invoke({"task": "Analyze Q1 sales data and generate a trends report with charts"})
print(result["results"])
```

## File Structure

```
lg-workflow-agent/
├── app/
│   ├── __init__.py
│   ├── main.py               # Runtime entry point, graph invocation
│   ├── graph.py               # StateGraph construction and compilation
│   ├── state.py               # WorkflowState TypedDict, MAX_RETRIES, initial_state()
│   └── nodes/
│       ├── planner.py         # Task decomposition
│       ├── executor.py        # Step execution with tool access
│       ├── validator.py       # Result validation and retry logic
│       ├── checkpoint.py      # State persistence and step advancement
│       └── finalizer.py       # Summary report generation
│   └── tools/
│       ├── file_tool.py       # File read/write/list operations
│       └── analysis_tool.py   # Data parsing and metric computation
├── tests/
├── README.md
├── architecture.md
└── tasks.md
```