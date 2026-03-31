# Tasks

## 1 — Define State Schema

File: `app/state.py`

- [ ] Define `AnalysisState` as a `TypedDict` with fields: `query` (str), `plan` (list[dict]), `execution_result` (dict), `explanation` (str), `iteration` (int), `success` (bool).
- [ ] Create `initial_state(query: str) -> AnalysisState` factory that sets `plan=[]`, `execution_result={}`, `explanation=""`, `iteration=0`, `success=False`.
- [ ] Add module-level constants: `MAX_ITERATIONS = 3`, `MAX_PLAN_STEPS = 10`.
- [ ] Add `REASONING_MODEL = "gemini-3.1-pro-preview"` and `EXPLANATION_MODEL = "gemini-3-flash-preview"` constants.
- [ ] Define `SUPPORTED_OPERATIONS` list: `["filter", "group_by", "sort", "aggregate", "pivot", "merge", "select", "drop", "rename"]`.

## 2 — Create Dataset Loader

File: `app/data_loader.py`

- [ ] Define `SUPPORTED_FORMATS = ["csv", "json", "parquet"]`.
- [ ] Define `load_dataset(path: str) -> pd.DataFrame` that reads a file into a pandas DataFrame.
- [ ] Detect format from file extension and call the appropriate `pd.read_csv`, `pd.read_json`, or `pd.read_parquet`.
- [ ] Raise `ValueError` for unsupported file extensions with a message listing supported formats.
- [ ] Raise `FileNotFoundError` if the path does not exist.
- [ ] Define `get_metadata(df: pd.DataFrame) -> dict` returning `{"columns": list[str], "dtypes": dict[str, str], "shape": [rows, cols], "sample": dict}` where `sample` is the first 3 rows as a dict.
- [ ] Ensure `sample` contains no more than 3 rows — never expose the full dataset to the LLM.

## 3 — Implement Planner Node

File: `app/nodes/planner.py`

- [ ] Define `planner_node(state: AnalysisState) -> dict` that reads `query` and `execution_result`.
- [ ] Call `get_metadata()` on the loaded DataFrame to get column names, dtypes, and shape for context.
- [ ] Build a prompt instructing the LLM to decompose the query into an ordered sequence of structured operations, given the dataset metadata.
- [ ] Each operation dict must have: `operation` (str from `SUPPORTED_OPERATIONS`), `column` (str), and operation-specific params (`agg`, `condition`, `value`, `order`, etc.).
- [ ] Call `generate_structured()` with `REASONING_MODEL` and a schema expecting `{"steps": list[dict]}`.
- [ ] Cap the plan at `MAX_PLAN_STEPS` operations.
- [ ] On retry (`execution_result` has `"error"`): include the error message in the prompt so the LLM can revise.
- [ ] Handle empty or malformed LLM output by returning a single-step fallback plan: `[{"operation": "aggregate", "column": "*", "agg": "describe"}]`.
- [ ] Return `{"plan": steps}`.

## 4 — Implement Executor Node

File: `app/nodes/executor.py`

- [ ] Define `executor_node(state: AnalysisState) -> dict` that reads `plan`.
- [ ] Load the dataset into a DataFrame using `data_loader.load_dataset()`.
- [ ] Iterate through `plan` operations in order, applying each as a pandas transformation on the working DataFrame.
- [ ] Map each `operation` type to a handler function: `_apply_filter`, `_apply_group_by`, `_apply_sort`, `_apply_aggregate`, `_apply_pivot`, `_apply_merge`, `_apply_select`, `_apply_drop`, `_apply_rename`.
- [ ] Before each operation, validate that referenced columns exist in the current DataFrame. On missing column, set `error` and stop.
- [ ] On unknown operation type, set `error` with the unsupported operation name and stop.
- [ ] On success, return `{"execution_result": {"data": result.to_dict(), "columns": list, "shape": [rows, cols], "error": None}}`.
- [ ] On failure, return `{"execution_result": {"data": None, "columns": [], "shape": [], "error": error_message}}`.
- [ ] Never call `exec()` or `eval()`. All operations dispatch through the fixed handler map.

## 5 — Implement Analyzer Node

File: `app/nodes/analyzer.py`

- [ ] Define `analyzer_node(state: AnalysisState) -> dict` that reads `query`, `plan`, and `execution_result`.
- [ ] If `execution_result["error"]` is not None, return `{"explanation": ""}` — skip explanation on failed execution.
- [ ] Build a prompt containing the original query, the operations that were executed, and the computed results (not raw data rows).
- [ ] Instruct the LLM to produce a clear explanation answering the query, noting key findings and patterns.
- [ ] Call `generate_text()` with `EXPLANATION_MODEL`.
- [ ] Return `{"explanation": response_text}`.
- [ ] Handle empty LLM response by returning a fallback: `{"explanation": "Analysis complete. See raw results."}`.

## 6 — Implement Evaluator Node

File: `app/nodes/evaluator.py`

- [ ] Define `evaluator_node(state: AnalysisState) -> dict` that reads `query`, `plan`, `execution_result`, `explanation`, and `iteration`.
- [ ] If `execution_result["error"]` is not None and `iteration + 1 < MAX_ITERATIONS`, return `{"success": False, "iteration": state["iteration"] + 1}` to trigger replanning.
- [ ] If `execution_result["error"]` is None, build a prompt asking the LLM whether the explanation adequately answers the query and results are coherent.
- [ ] Call `generate_structured()` with `REASONING_MODEL` and schema `{"complete": bool, "reason": str}`.
- [ ] If `complete` is True, return `{"success": True, "iteration": state["iteration"] + 1}`.
- [ ] If `complete` is False and `iteration + 1 < MAX_ITERATIONS`, return `{"success": False, "iteration": state["iteration"] + 1}`.
- [ ] If `iteration + 1 >= MAX_ITERATIONS`, return `{"success": True, "iteration": state["iteration"] + 1}` to force termination with best available results.
- [ ] Return only `success` and `iteration` keys.

## 7 — Build Graph Transitions

File: `app/graph.py`

- [ ] Import `StateGraph`, `START`, `END` from `langgraph.graph`.
- [ ] Import node functions from `app.nodes.planner`, `app.nodes.executor`, `app.nodes.analyzer`, `app.nodes.evaluator`.
- [ ] Import `AnalysisState` from `app.state`.
- [ ] Create `StateGraph(AnalysisState)`.
- [ ] Add four nodes: `"planner"`, `"executor"`, `"analyzer"`, `"evaluator"`.
- [ ] Add linear edges: `START → planner`, `planner → executor`, `executor → analyzer`, `analyzer → evaluator`.
- [ ] Define `route_after_evaluator(state: AnalysisState) -> str` that returns `"end"` if `state["success"]` or `state["iteration"] >= MAX_ITERATIONS`, else `"planner"`.
- [ ] Register with `graph.add_conditional_edges("evaluator", route_after_evaluator, {"end": END, "planner": "planner"})`.
- [ ] Define `build_graph() -> CompiledGraph` that wires everything and calls `graph.compile()`.
- [ ] Write a unit test: assert `route_after_evaluator({"success": False, "iteration": 0, ...})` returns `"planner"`.
- [ ] Write a unit test: assert `route_after_evaluator({"success": True, ...})` returns `"end"`.
- [ ] Write a unit test: assert `route_after_evaluator({"success": False, "iteration": MAX_ITERATIONS, ...})` returns `"end"`.

