# Tasks

## 1 — Define State Schema

File: `app/state.py`

- [ ] Define `ResearchState` as a `TypedDict` with fields: `query` (str), `plan` (list[str]), `findings` (list[str]), `critiques` (list[str]), `revision_count` (int), `approved` (bool), `final_output` (str).
- [ ] Set default factory values: `plan=[]`, `findings=[]`, `critiques=[]`, `revision_count=0`, `approved=False`, `final_output=""`.
- [ ] Add module-level constants: `MAX_REVISIONS = 3`, `MAX_PLAN_TASKS = 7`.
- [ ] Add `REASONING_MODEL = "gemini-3.1-pro-preview"` and `WRITING_MODEL = "gemini-3-flash-preview"` constants.

## 2 — Implement Planner Node

File: `app/nodes/planner.py`

- [ ] Define `planner_node(state: ResearchState) -> dict` that reads `state["query"]`.
- [ ] Build a prompt instructing the LLM to decompose the query into 3–7 bounded research sub-tasks.
- [ ] Call `generate_structured()` with `REASONING_MODEL` and a schema expecting `{"tasks": list[str]}`.
- [ ] Return `{"plan": tasks}` capped at `MAX_PLAN_TASKS`.
- [ ] Handle empty or malformed LLM output by returning a single-task fallback plan.

## 3 — Implement Researcher Node

File: `app/nodes/researcher.py`

- [ ] Define `researcher_node(state: ResearchState) -> dict` that reads `query`, `plan`, and `critiques`.
- [ ] On first pass (`critiques` empty): build a prompt listing all sub-tasks and requesting findings for each.
- [ ] On revision pass (`critiques` non-empty): build a prompt including current `findings` and `critiques`, requesting targeted improvements.
- [ ] Call `generate_text()` with `REASONING_MODEL`.
- [ ] Parse the response into a list of finding strings (one per sub-task).
- [ ] Return `{"findings": parsed_findings}`.

## 4 — Implement Critic Node

File: `app/nodes/critic.py`

- [ ] Define `critic_node(state: ResearchState) -> dict` that reads `query`, `plan`, and `findings`.
- [ ] Build an evaluation prompt asking the LLM to check coverage, accuracy, depth, and coherence against the plan.
- [ ] Call `generate_structured()` with `REASONING_MODEL` and schema `{"approved": bool, "issues": list[str]}`.
- [ ] If `approved` is True, return `{"critiques": [], "approved": True, "revision_count": state["revision_count"]}`.
- [ ] If `approved` is False, return `{"critiques": issues, "approved": False, "revision_count": state["revision_count"] + 1}`.

## 5 — Implement Writer Node

File: `app/nodes/writer.py`

- [ ] Define `writer_node(state: ResearchState) -> dict` that reads `query`, `plan`, `findings`, and `critiques`.
- [ ] Build a prompt requesting a Markdown report with: title, executive summary, one section per sub-task, and a conclusion.
- [ ] If there are unresolved critiques (hit revision limit), instruct the LLM to note limitations.
- [ ] Call `generate_text()` with `WRITING_MODEL`.
- [ ] Return `{"final_output": report_text}`.

## 6 — Build Graph Transitions

File: `app/graph.py`

- [ ] Import `StateGraph`, `START`, `END` from `langgraph.graph`.
- [ ] Import node functions from `app.nodes.*` and `ResearchState` from `app.state`.
- [ ] Create `StateGraph(ResearchState)`.
- [ ] Add four nodes: `"planner"`, `"researcher"`, `"critic"`, `"writer"`.
- [ ] Add linear edges: `START → planner`, `planner → researcher`, `researcher → critic`, `writer → END`.
- [ ] Define `build_graph() -> CompiledGraph` that wires everything and calls `graph.compile()`.

## 7 — Add Loop Logic

File: `app/graph.py` (extend from task 6)

- [ ] Define `route_after_critic(state: ResearchState) -> str` that returns `"writer"` if `state["approved"]` or `state["revision_count"] >= MAX_REVISIONS`, else `"researcher"`.
- [ ] Register with `graph.add_conditional_edges("critic", route_after_critic, {"writer": "writer", "researcher": "researcher"})`.
- [ ] Write a unit test: assert `route_after_critic({"approved": False, "revision_count": 0, ...})` returns `"researcher"`.
- [ ] Write a unit test: assert `route_after_critic({"approved": True, ...})` returns `"writer"`.
- [ ] Write a unit test: assert `route_after_critic({"approved": False, "revision_count": MAX_REVISIONS, ...})` returns `"writer"`.

