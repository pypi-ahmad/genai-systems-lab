# Autonomous Debugging Agent — Architecture

## Overview

The Autonomous Debugging Agent is a LangGraph-based cyclic graph that takes buggy code and an error message, diagnoses the root cause, generates a fix, validates it through sandboxed execution, and decides whether the fix is sufficient or another iteration is needed. Each node is a pure function that receives the current graph state, performs one focused task, and returns a state update. LangGraph manages execution order, the conditional retry loop, and iteration tracking — there is no custom orchestrator.

Primary flow:

```
START → analyzer → fixer → tester → evaluator → (retry fixer OR END)
```

## Graph State

All data flows through a single `TypedDict` that every node can read and update. LangGraph merges the partial dicts returned by each node into the running state automatically.

```python
class DebuggingState(TypedDict):
    input_code: str        # Original buggy source code
    error_message: str     # Error output (traceback, compiler error, test failure, etc.)
    analysis: str          # Root-cause diagnosis produced by analyzer
    fixed_code: str        # Patched code produced by fixer
    test_result: str       # stdout/stderr captured from sandboxed execution of fixed_code
    iteration: int         # Current fix-test cycle count (starts at 0)
    is_resolved: bool      # True when evaluator accepts the fix
```

### State design rules

- `input_code` and `error_message` are immutable after graph invocation — no node overwrites them.
- `fixed_code` and `test_result` are overwritten each iteration with the latest attempt.
- `analysis` is updated by the analyzer once and read by subsequent nodes; the fixer may append to it on retries when the evaluator feeds back new context.
- `iteration` and `is_resolved` drive the conditional edge after the evaluator node.

## Nodes

Each node is a regular Python function with the signature `(state: DebuggingState) -> dict`. It returns only the keys it modifies.

### analyzer

Diagnoses the root cause of the bug by examining the code and error message.

- **Reads:** `input_code`, `error_message`, `test_result` (on retry iterations, to incorporate new failure context)
- **Writes:** `analysis`
- **Model:** `gemini-3.1-pro-preview` — root-cause analysis requires strong reasoning to trace execution flow, identify faulty logic, and distinguish symptoms from causes.
- **Output:** A structured diagnosis containing: error classification (syntax, runtime, logic, type), the specific faulty code region, an explanation of why the code fails, and a recommended fix strategy.

### fixer

Generates a corrected version of the code based on the analysis.

- **Reads:** `input_code`, `error_message`, `analysis`, `test_result` (on retries), `iteration`
- **Writes:** `fixed_code`
- **Model:** `gemini-3.1-pro-preview` — code generation with correctness constraints demands strong reasoning; the model must respect the original intent while addressing the diagnosed issue.
- **Behavior on first pass:** Applies the fix strategy from `analysis` to produce a corrected version of `input_code`.
- **Behavior on retry pass:** Reads the previous `test_result` to understand why the last fix failed, then generates an improved patch. The prompt includes all prior context to avoid repeating the same mistake.

### tester

Executes the fixed code in a sandboxed environment and captures the result.

- **Reads:** `fixed_code`, `error_message` (to know what to validate)
- **Writes:** `test_result`
- **Model:** None — this node is deterministic. It runs code, not an LLM.
- **Execution:**
  1. Write `fixed_code` to a temporary file inside a restricted sandbox.
  2. Execute with a timeout (default: 10 seconds) and memory limit.
  3. Capture stdout, stderr, and exit code.
  4. Return a structured result: `{"stdout": ..., "stderr": ..., "exit_code": ..., "timed_out": bool}`.
- **Safety:** Code execution uses `subprocess` with `timeout`, no network access, a temporary working directory, and restricted filesystem permissions. Never execute code in the host process.

### evaluator

Decides whether the fix is successful or another iteration is needed.

- **Reads:** `input_code`, `error_message`, `fixed_code`, `test_result`, `iteration`
- **Writes:** `is_resolved`, `iteration`, `analysis` (appends failure context on retry)
- **Model:** `gemini-3.1-pro-preview` — judging fix correctness requires reasoning about whether the output matches expected behavior and whether new errors were introduced.
- **Logic:**
  1. If `test_result` shows exit code 0 and no errors in stderr, set `is_resolved = True`.
  2. If the test failed but `iteration < MAX_ITERATIONS`, set `is_resolved = False`, increment `iteration`, and append diagnostic context to `analysis` explaining what went wrong with the current fix.
  3. If `iteration >= MAX_ITERATIONS`, set `is_resolved = True` (force exit) and annotate `analysis` with a note that the fix is best-effort.

## Graph Transitions

### Edge map

| From | To | Condition |
|---|---|---|
| `START` | `analyzer` | Always |
| `analyzer` | `fixer` | Always |
| `fixer` | `tester` | Always |
| `tester` | `evaluator` | Always |
| `evaluator` | `fixer` | `is_resolved is False AND iteration < MAX_ITERATIONS` |
| `evaluator` | `END` | `is_resolved is True OR iteration >= MAX_ITERATIONS` |

### Conditional edge after evaluator

This is the only branching point in the graph. It is implemented as a LangGraph conditional edge:

```python
MAX_ITERATIONS = 3

def route_after_evaluator(state: DebuggingState) -> str:
    if state["is_resolved"] or state["iteration"] >= MAX_ITERATIONS:
        return "end"
    return "fixer"

graph.add_conditional_edges("evaluator", route_after_evaluator, {
    "end": END,
    "fixer": "fixer",
})
```

`MAX_ITERATIONS` (default: 3) prevents infinite loops. When the limit is reached, the graph terminates with the best fix produced so far and the evaluator annotates the output as best-effort.

### Why this topology works

- **Targeted retry loop.** Only the fixer → tester → evaluator cycle repeats. The analyzer runs once upfront; re-analysis context is folded into the evaluator's feedback, avoiding a full re-diagnosis each iteration.
- **Deterministic routing.** The conditional edge reads two scalar fields (`is_resolved`, `iteration`). There is no LLM call in the routing logic.
- **Graceful degradation.** Hitting `MAX_ITERATIONS` does not crash the graph — it terminates with the last `fixed_code` and a clear indication of unresolved issues.
- **No wasted calls.** Each iteration adds new context from the test failure, so the fixer has strictly more information with each pass.

## Model Usage

| Model | Nodes | Rationale |
|---|---|---|
| `gemini-3.1-pro-preview` | analyzer, fixer, evaluator | Diagnosis, code generation, and correctness evaluation all require strong reasoning |
| `gemini-3-flash-preview` | (optional) post-run explanation | If the caller requests a human-readable summary of the debugging session, use the faster model to generate it from the final state |

### Cost and latency considerations

- The fixer and evaluator account for most token usage since they may run up to `MAX_ITERATIONS` times.
- The tester node has zero LLM cost — it is pure code execution.
- Setting `MAX_ITERATIONS` to 3 keeps total cost bounded at a maximum of 7 LLM calls (1 analyzer + 3 fixer + 3 evaluator).
- The analyzer runs exactly once and front-loads the expensive reasoning work.

## Graph Construction

```python
from langgraph.graph import StateGraph, START, END

graph = StateGraph(DebuggingState)

# Add nodes
graph.add_node("analyzer", analyzer_node)
graph.add_node("fixer", fixer_node)
graph.add_node("tester", tester_node)
graph.add_node("evaluator", evaluator_node)

# Linear edges
graph.add_edge(START, "analyzer")
graph.add_edge("analyzer", "fixer")
graph.add_edge("fixer", "tester")
graph.add_edge("tester", "evaluator")

# Conditional retry loop
graph.add_conditional_edges("evaluator", route_after_evaluator, {
    "end": END,
    "fixer": "fixer",
})

app = graph.compile()
```

Invocation:

```python
result = app.invoke({
    "input_code": buggy_source,
    "error_message": "TypeError: unsupported operand type(s) for +: 'int' and 'str'",
    "iteration": 0,
    "is_resolved": False,
})
print(result["fixed_code"])
print("Resolved:", result["is_resolved"])
```

## Production Design Notes

### Safe Code Execution

The tester node is the primary security boundary. All execution must be sandboxed:

- **Subprocess isolation.** Run `fixed_code` via `subprocess.run()` with `timeout`, `cwd` set to a temporary directory, and `env` stripped of sensitive variables.
- **No network access.** Block outbound connections via environment or firewall rules in the execution sandbox.
- **Resource limits.** Enforce a 10-second timeout and memory cap to prevent fork bombs or infinite loops.
- **No host-process eval.** Never use `exec()` or `eval()` in the agent process. All code runs in a child process.
- **Temporary files.** Write code to a `tempfile.mkdtemp()` directory and clean up after execution.

### Observability

- Each node should log its input keys, output keys, token count, and latency.
- `iteration` and `is_resolved` provide a built-in audit trail of retry attempts.
- The full sequence of `analysis → fixed_code → test_result` per iteration should be captured for post-mortem review.
- LangGraph's built-in tracing (LangSmith integration) can be enabled for full run visualization.

### Error Handling

- Wrap each node's LLM call in a retry with exponential backoff (max 2 retries per call).
- If the tester node's subprocess crashes or times out, populate `test_result` with the error details rather than raising — the evaluator will treat it as a failed test.
- If a node fails after retries, set `is_resolved = False` and route to END with a clear error annotation in `analysis`.

### Configuration

Key parameters should be externalized:

| Parameter | Default | Purpose |
|---|---|---|
| `MAX_ITERATIONS` | 3 | Cap on fixer → tester → evaluator retry cycles |
| `REASONING_MODEL` | `gemini-3.1-pro-preview` | Model for analyzer, fixer, evaluator |
| `EXPLANATION_MODEL` | `gemini-3-flash-preview` | Model for optional post-run explanation |
| `EXEC_TIMEOUT` | 10 | Seconds before sandboxed execution is killed |
| `EXEC_MEMORY_LIMIT` | 256 | MB memory cap for sandboxed execution |

### Testing

- Each node is a pure function of state — unit test by passing a constructed `DebuggingState` dict and asserting the returned keys.
- Integration test the full graph with a mock LLM that returns canned responses and a mock subprocess runner, verifying the correct node sequence fires.
- Test the conditional edge by asserting `route_after_evaluator` returns `"fixer"` when `is_resolved=False` and `iteration < MAX_ITERATIONS`, and `"end"` otherwise.
- Test the retry loop by mocking the tester to fail for N iterations then succeed, and verify `iteration` matches expected count.
- Test the safety boundary by confirming the tester node handles timeout, crash, and excessive output cases without propagating to the host.

## Summary

The system is a four-node LangGraph `StateGraph` with one conditional retry loop. The analyzer diagnoses the root cause, the fixer generates corrected code, the tester validates it in a sandbox, and the evaluator decides whether to retry or terminate. State is a flat `TypedDict` passed through the graph — no shared memory service, no custom orchestrator. The conditional edge after the evaluator is the only branching logic, controlled by `is_resolved` and `iteration`. Code execution is fully sandboxed with subprocess isolation, timeouts, and resource limits.