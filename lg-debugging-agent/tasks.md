# Tasks

## 1 — Define State Schema

File: `app/state.py`

- [ ] Define `DebuggingState` as a `TypedDict` with fields: `input_code` (str), `error_message` (str), `analysis` (str), `fixed_code` (str), `test_result` (str), `iteration` (int), `is_resolved` (bool).
- [ ] Create `initial_state(input_code: str, error_message: str) -> DebuggingState` factory that sets `analysis=""`, `fixed_code=""`, `test_result=""`, `iteration=0`, `is_resolved=False`.
- [ ] Add module-level constants: `MAX_ITERATIONS = 3`, `EXEC_TIMEOUT = 10`, `EXEC_MEMORY_LIMIT = 256`.
- [ ] Add `REASONING_MODEL = "gemini-3.1-pro-preview"` and `EXPLANATION_MODEL = "gemini-3-flash-preview"` constants.

## 2 — Implement Analyzer Node

File: `app/nodes/analyzer.py`

- [ ] Define `analyzer_node(state: DebuggingState) -> dict` that reads `input_code` and `error_message`.
- [ ] Build a prompt instructing the LLM to classify the error (syntax, runtime, logic, type), identify the faulty code region, explain why it fails, and recommend a fix strategy.
- [ ] Call `generate_text()` with `REASONING_MODEL`.
- [ ] Return `{"analysis": response_text}`.
- [ ] Handle empty or malformed LLM output by returning a generic "unable to diagnose" analysis.

## 3 — Implement Fixer Node

File: `app/nodes/fixer.py`

- [ ] Define `fixer_node(state: DebuggingState) -> dict` that reads `input_code`, `error_message`, `analysis`, `test_result`, and `iteration`.
- [ ] On first pass (`iteration == 0`): build a prompt with the original code, error, and analysis, requesting a corrected version.
- [ ] On retry pass (`iteration > 0`): include the previous `test_result` in the prompt so the LLM knows why the last fix failed.
- [ ] Call `generate_text()` with `REASONING_MODEL`.
- [ ] Extract the code block from the response (strip markdown fences if present).
- [ ] Return `{"fixed_code": extracted_code}`.
- [ ] If no code block is found in the response, return the raw response as `fixed_code`.

## 4 — Implement Tester Node

File: `app/nodes/tester.py`

- [ ] Define `tester_node(state: DebuggingState) -> dict` that reads `fixed_code`.
- [ ] Write `fixed_code` to a temporary file inside a `tempfile.mkdtemp()` directory.
- [ ] Execute the file using `subprocess.run()` with `timeout=EXEC_TIMEOUT`, `capture_output=True`, `text=True`.
- [ ] Set `cwd` to the temp directory and strip sensitive environment variables from `env`.
- [ ] Build a result string from stdout, stderr, and exit code.
- [ ] Return `{"test_result": result_string}`.
- [ ] On `subprocess.TimeoutExpired`, return `{"test_result": "TIMEOUT: execution exceeded {EXEC_TIMEOUT}s"}`.
- [ ] On any other `subprocess` exception, return `{"test_result": f"EXECUTION ERROR: {str(e)}"}`.
- [ ] Clean up the temp directory after execution.

## 5 — Implement Evaluator Node

File: `app/nodes/evaluator.py`

- [ ] Define `evaluator_node(state: DebuggingState) -> dict` that reads `input_code`, `error_message`, `fixed_code`, `test_result`, and `iteration`.
- [ ] If `test_result` shows exit code 0 and no errors in stderr, return `{"is_resolved": True}`.
- [ ] If the test failed and `iteration + 1 < MAX_ITERATIONS`, build a prompt asking the LLM to explain why the fix failed and what to try next.
- [ ] Call `generate_text()` with `REASONING_MODEL` for the failure explanation.
- [ ] Return `{"is_resolved": False, "iteration": state["iteration"] + 1, "analysis": state["analysis"] + "\n\n" + failure_context}`.
- [ ] If `iteration + 1 >= MAX_ITERATIONS`, return `{"is_resolved": True, "iteration": state["iteration"] + 1}` to force termination.

## 6 — Build Graph Transitions

File: `app/graph.py`

- [ ] Import `StateGraph`, `START`, `END` from `langgraph.graph`.
- [ ] Import node functions from `app.nodes.analyzer`, `app.nodes.fixer`, `app.nodes.tester`, `app.nodes.evaluator`.
- [ ] Import `DebuggingState` from `app.state`.
- [ ] Create `StateGraph(DebuggingState)`.
- [ ] Add four nodes: `"analyzer"`, `"fixer"`, `"tester"`, `"evaluator"`.
- [ ] Add linear edges: `START → analyzer`, `analyzer → fixer`, `fixer → tester`, `tester → evaluator`.
- [ ] Define `build_graph() -> CompiledGraph` that wires everything and calls `graph.compile()`.

## 7 — Add Retry Loop

File: `app/graph.py` (extend from task 6)

- [ ] Define `route_after_evaluator(state: DebuggingState) -> str` that returns `"end"` if `state["is_resolved"]` or `state["iteration"] >= MAX_ITERATIONS`, else `"fixer"`.
- [ ] Register with `graph.add_conditional_edges("evaluator", route_after_evaluator, {"end": END, "fixer": "fixer"})`.
- [ ] Write a unit test: assert `route_after_evaluator({"is_resolved": False, "iteration": 0, ...})` returns `"fixer"`.
- [ ] Write a unit test: assert `route_after_evaluator({"is_resolved": True, ...})` returns `"end"`.
- [ ] Write a unit test: assert `route_after_evaluator({"is_resolved": False, "iteration": MAX_ITERATIONS, ...})` returns `"end"`.

