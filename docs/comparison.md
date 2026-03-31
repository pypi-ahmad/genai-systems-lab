# LangGraph vs CrewAI: Implementation Comparison

A technical comparison of the two agent frameworks used in this repository, grounded in the 5 LangGraph and 5 CrewAI projects implemented here.

## Control vs Collaboration

LangGraph projects are built as explicit state machines. Each node is a pure function `(state) -> dict` that reads typed state, performs work, and returns a partial update. Routing between nodes is controlled by conditional edge functions that inspect state values. The developer decides what happens next.

In `lg-debugging-agent`, the evaluator node sets `is_resolved` and `iteration` on state. A routing function inspects those values and either sends execution back to the fixer node or terminates the graph. The retry path skips the analyzer on subsequent iterations because the routing function maps directly to a downstream node:

```python
graph.add_conditional_edges("evaluator", route_after_evaluator, {
    "end": END,
    "fixer": "fixer",
})
```

In `lg-data-agent`, the planner node writes a structured plan to state, and a conditional edge routes to either the pandas executor or the DuckDB executor based on `state["engine"]`. The execution path is fully deterministic once the engine is selected.

CrewAI projects are built as role-based collaboration pipelines. Each agent has a role, goal, and backstory that get injected into system prompts. Tasks bind agents to deliverables and chain outputs through context references. The framework handles prompt construction and context forwarding.

In `crew-startup-simulator`, four agents (CEO, PM, CTO, Engineer) execute 11 tasks across four phases: independent proposals, CEO selection, feedforward pipeline, and cross-functional peer review. The PM reviews the CEO's selection; the CTO reviews the PM's spec; the Engineer reviews the CTO's architecture; the CEO reviews the Engineer's execution plan. The collaboration pattern is encoded in task ordering and context lists, not in explicit routing logic.

In `crew-hiring-system`, the framework demonstrates composable crews: a single-candidate evaluation runs a 5-agent sequential pipeline, and a separate comparison crew with a `comparative_analyst` agent synthesizes rankings across multiple candidates. Each crew is an independent orchestration unit.

**Summary**: LangGraph gives the developer explicit control over transitions, retries, and branching. CrewAI encodes collaboration structure through role definitions and task context, delegating execution flow to the framework.

## Determinism vs Flexibility

LangGraph projects maintain a clear boundary between deterministic nodes and LLM-driven nodes within the same graph.

In `lg-data-agent`, the planner and analyzer nodes call the LLM. The executor nodes do not — they map structured plan operations to pandas or DuckDB calls from a fixed allowlist. The LLM reasons about what to compute; deterministic code computes it.

In `lg-debugging-agent`, the tester node runs generated test cases in a subprocess sandbox with timeout and memory limits. The fixer node uses the LLM to generate a diff. The sandbox execution is fully deterministic; the fix generation is not.

In `lg-workflow-agent`, the checkpoint node manages state persistence and step advancement with no LLM involvement. The executor and validator nodes use the LLM. State snapshots written to disk enable `--resume` for checkpoint recovery — a deterministic mechanism wrapping an LLM-driven inner loop.

State management in LangGraph is typed (`TypedDict`) and explicit. Each node reads specific keys and returns specific keys. The iteration counter that drives retry logic is a plain integer on state, incremented by deterministic code after the evaluator runs.

CrewAI projects are LLM-driven end-to-end by design. Every agent node calls the LLM. Determinism is pushed to the tool and schema level rather than the node level.

In `crew-hiring-system`, `resolve_role_criteria()` applies deterministic role-specific scoring weights (e.g., software engineer: 40% technical, 30% behavioral, 30% screening). The scoring weights are fixed; the evaluation that produces the scores is LLM-driven.

All CrewAI projects in this repository enforce structured JSON output by embedding schemas in task descriptions. This constrains the output format deterministically even though the content is generated.

Context flow differs. LangGraph state is a global typed dict available to all nodes. CrewAI context is passed through `Task.context` lists — each downstream agent sees prior outputs injected into its prompt, not an explicit state object.

**Summary**: LangGraph enables deterministic + LLM hybrid execution within a single graph. CrewAI is LLM-first, with determinism applied at the tool and schema boundary.

## Use Cases

### When LangGraph fits

LangGraph is the right choice when the workflow needs:

- **Conditional branching with explicit routing.** `lg-data-agent` routes to different execution engines based on state. `lg-support-agent` routes to escalation only when confidence is below threshold.
- **Retry loops with state-driven termination.** `lg-debugging-agent` retries the fix-test cycle up to 3 times, skipping the analyzer on retry. `lg-data-agent` re-plans when execution fails, using the error from the previous iteration.
- **Deterministic execution alongside LLM reasoning.** `lg-data-agent` executes data operations without LLM involvement. `lg-debugging-agent` runs tests in a sandbox.
- **Checkpoint and recovery.** `lg-workflow-agent` persists state after each step and supports resumption from the last checkpoint.

Projects in this repository that use LangGraph: `lg-data-agent`, `lg-debugging-agent`, `lg-research-agent`, `lg-support-agent`, `lg-workflow-agent`.

### When CrewAI fits

CrewAI is the right choice when the workflow needs:

- **Role-based reasoning where multiple perspectives improve output quality.** `crew-startup-simulator` gets three independent proposals from PM, CTO, and Engineer before the CEO synthesizes a direction.
- **Deep sequential analysis with cumulative context.** `crew-investment-analyst` layers market analysis → financial analysis → risk assessment → strategy → adversarial risk challenge, with each agent reasoning on all prior outputs.
- **Cross-functional review patterns.** `crew-startup-simulator` has each agent review a different agent's output, creating perspective checks that would require complex conditional edges in LangGraph.
- **Composable multi-crew workflows.** `crew-hiring-system` runs independent evaluation crews per candidate, then a comparison crew to synthesize rankings.
- **Fast prototyping of multi-agent pipelines.** `crew-content-pipeline` defines a research → write → edit → SEO pipeline in four agent definitions and four task definitions with minimal orchestration code.

Projects in this repository that use CrewAI: `crew-content-pipeline`, `crew-hiring-system`, `crew-investment-analyst`, `crew-product-launch`, `crew-startup-simulator`.

## Side-by-Side Reference

| Aspect | LangGraph | CrewAI |
|---|---|---|
| Abstraction | `StateGraph` with typed state dict | Agents with role/goal/backstory + Tasks |
| Node definition | `(state) -> dict` | Agent bound to Task with context list |
| State | Explicit `TypedDict`; nodes return partial updates | Implicit context passing via `Task.context` |
| Branching | `add_conditional_edges` with routing functions | Sequential process; branching via separate crews |
| Retry | State counter + conditional edge back to earlier node | No built-in retry; separate phases or crews |
| Deterministic nodes | First-class; nodes with no LLM calls | Not typical; determinism at tool/schema level |
| Model selection | Per-node (reasoning vs. fast models) | Per-agent (same model for all agent tasks) |
| Error handling | Node-level; evaluator decides retry or exit | Framework-level; agents reason about failures via context |
| Output | Final state dict | `CrewResult.tasks_output` list |
| Typical complexity | 4–5 nodes, 1–3 conditional branches | 4–11 tasks, linear or phased sequencing |
