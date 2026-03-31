# Tasks

## 1 — Define State Schema

File: `app/state.py`

- [ ] Define `WorkflowState` as a `TypedDict` with fields: `task` (str), `plan` (list[str]), `current_step` (int), `results` (dict[str, str]), `iteration` (int), `completed` (bool).
- [ ] Create `initial_state(task: str) -> WorkflowState` factory that sets `plan=[]`, `current_step=0`, `results={}`, `iteration=0`, `completed=False`.
- [ ] Add module-level constants: `MAX_RETRIES = 3`, `MAX_PLAN_STEPS = 10`.
- [ ] Add `REASONING_MODEL = "gemini-3.1-pro-preview"` and `SUMMARY_MODEL = "gemini-3-flash-preview"` constants.

## 2 — Implement Planner Node

File: `app/nodes/planner.py`

- [ ] Define `planner_node(state: WorkflowState) -> dict` that reads `state["task"]`.
- [ ] Build a prompt instructing the LLM to decompose the task into 3–10 ordered, actionable steps with clear completion criteria.
- [ ] Call `generate_structured()` with `REASONING_MODEL` and a schema expecting `{"steps": list[str]}`.
- [ ] Cap the result at `MAX_PLAN_STEPS` entries.
- [ ] Return `{"plan": steps, "current_step": 0, "iteration": 0}`.
- [ ] Handle empty or malformed LLM output by returning a single-step fallback plan: `["Execute the task directly"]`.

## 3 — Implement Executor Node

File: `app/nodes/executor.py`

- [ ] Define `executor_node(state: WorkflowState) -> dict` that reads `task`, `plan`, `current_step`, and `results`.
- [ ] Retrieve the current step description from `plan[current_step]`.
- [ ] Build a prompt that includes: the original task for context, the full plan, prior step results from `results`, and the specific step to execute.
- [ ] Give the LLM access to `file_tool` and `analysis_tool` by listing available tool descriptions in the prompt.
- [ ] Call `generate_text()` with `REASONING_MODEL`.
- [ ] Store the output in `results` keyed by the step name: `results[plan[current_step]] = response`.
- [ ] Return `{"results": updated_results}`.
- [ ] If `current_step >= len(plan)`, return `{"results": state["results"]}` unchanged (no-op guard).

## 4 — Implement Validator Node

File: `app/nodes/validator.py`

- [ ] Define `validator_node(state: WorkflowState) -> dict` that reads `task`, `plan`, `current_step`, `results`, and `iteration`.
- [ ] Build a prompt asking the LLM to evaluate whether the executor output for `plan[current_step]` satisfies the step's intent and is consistent with prior results.
- [ ] Call `generate_structured()` with `REASONING_MODEL` and schema `{"valid": bool, "feedback": str}`.
- [ ] If `valid` is True, return `{"iteration": state["iteration"]}` (no change, checkpoint will advance).
- [ ] If `valid` is False and `iteration < MAX_RETRIES`, increment `iteration` and annotate the result with feedback for retry: return `{"iteration": state["iteration"] + 1}`.
- [ ] If `valid` is False and `iteration >= MAX_RETRIES`, return `{"iteration": state["iteration"]}` (allow checkpoint to advance as best-effort).

## 5 — Implement Checkpoint Node

File: `app/nodes/checkpoint.py`

- [ ] Define `checkpoint_node(state: WorkflowState) -> dict` that reads `plan`, `current_step`, `iteration`, and `results`.
- [ ] If validation failed and `iteration < MAX_RETRIES` (retry case): return `{}` (no state change — loop re-enters executor for the same step).
- [ ] If validation passed or retries exhausted: advance `current_step` by 1 and reset `iteration` to 0.
- [ ] If `current_step + 1 >= len(plan)`, set `completed = True`.
- [ ] Return `{"current_step": new_step, "iteration": 0, "completed": is_done}`.
- [ ] Persist the current state snapshot to disk as JSON for crash recovery: write to `checkpoint_{current_step}.json`.
- [ ] On module load, check for existing checkpoint files and log the latest available recovery point.

## 6 — Implement Finalizer Node

File: `app/nodes/finalizer.py`

- [ ] Define `finalizer_node(state: WorkflowState) -> dict` that reads `task`, `plan`, `results`, and `completed`.
- [ ] Build a prompt requesting a structured summary: task description, each step with its result, steps that required retries, overall status, and follow-up recommendations.
- [ ] Call `generate_text()` with `SUMMARY_MODEL`.
- [ ] Return `{"results": state["results"]}` (finalizer output is the terminal state; the summary is printed, not stored in a new field).
- [ ] If `results` is empty, return early with a printed message: `"No steps were executed."`.

## 7 — Build Graph Transitions

File: `app/graph.py`

- [ ] Import `StateGraph`, `START`, `END` from `langgraph.graph`.
- [ ] Import node functions from `app.nodes.planner`, `app.nodes.executor`, `app.nodes.validator`, `app.nodes.checkpoint`, `app.nodes.finalizer`.
- [ ] Import `WorkflowState` and `MAX_RETRIES` from `app.state`.
- [ ] Create `StateGraph(WorkflowState)`.
- [ ] Add five nodes: `"planner"`, `"executor"`, `"validator"`, `"checkpoint"`, `"finalizer"`.
- [ ] Add linear edges: `START → planner`, `planner → executor`, `executor → validator`, `validator → checkpoint`, `finalizer → END`.
- [ ] Define `route_after_checkpoint(state: WorkflowState) -> str` that returns `"finalizer"` if `state["completed"]` is True, else `"executor"`.
- [ ] Register with `graph.add_conditional_edges("checkpoint", route_after_checkpoint, {"finalizer": "finalizer", "executor": "executor"})`.
- [ ] Define `build_graph() -> CompiledGraph` that wires everything and calls `graph.compile()`.
- [ ] Write a unit test: assert `route_after_checkpoint({"completed": False, ...})` returns `"executor"`.
- [ ] Write a unit test: assert `route_after_checkpoint({"completed": True, ...})` returns `"finalizer"`.

