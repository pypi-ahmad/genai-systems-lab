# Tasks

## 1 — Define State Schema

File: `app/state.py`

- [ ] Define `SupportState` as a `TypedDict` with `total=False` and fields: `query` (str), `intent` (str), `retrieved_docs` (list[dict]), `response` (str), `confidence` (float), `escalate` (bool).
- [ ] Create `initial_state(query: str) -> SupportState` factory that sets `intent=""`, `retrieved_docs=[]`, `response=""`, `confidence=0.0`, `escalate=False`.
- [ ] Add module-level constants: `CONFIDENCE_THRESHOLD = 0.7`, `RETRIEVAL_TOP_K = 5`, `RELEVANCE_THRESHOLD = 0.3`.
- [ ] Add `CLASSIFICATION_MODEL = "gemini-3.1-pro-preview"` and `RESPONSE_MODEL = "gemini-3-flash-preview"` constants.
- [ ] Define `INTENT_LABELS = ["billing", "technical", "account", "returns", "general", "unknown"]` constant.

## 2 — Create Knowledge Base

File: `app/knowledge_base.py`

- [ ] Define `KnowledgeBase` class with `__init__(self, docs_path: str)` that loads articles from a JSON file into memory.
- [ ] Each article is a dict with keys: `title` (str), `content` (str), `category` (str), `embedding` (list[float]).
- [ ] Implement `search(self, query: str, intent: str, top_k: int = 5, threshold: float = 0.3) -> list[dict]` that computes cosine similarity between the query embedding and stored embeddings, filters by `intent` category, and returns the top-k results above threshold.
- [ ] Each result dict contains `title`, `content`, and `relevance_score`.
- [ ] Implement `_cosine_similarity(self, a: list[float], b: list[float]) -> float` as a static helper.
- [ ] Return an empty list when no articles match above the threshold.
- [ ] Handle missing or empty `docs_path` by initializing with an empty article list (no crash).

## 3 — Implement Classifier Node

File: `app/nodes/classifier.py`

- [ ] Define `classifier_node(state: SupportState) -> dict` that reads `state["query"]`.
- [ ] Build a prompt listing the allowed `INTENT_LABELS` and instructing the LLM to return exactly one label.
- [ ] Call `generate_structured()` with `CLASSIFICATION_MODEL` and a schema expecting `{"intent": str}`.
- [ ] Validate that the returned intent is in `INTENT_LABELS`; default to `"unknown"` if not.
- [ ] Return `{"intent": validated_intent}`.
- [ ] Handle empty query by returning `{"intent": "unknown"}` without calling the LLM.

## 4 — Implement Retriever Node

File: `app/nodes/retriever.py`

- [ ] Define `retriever_node(state: SupportState) -> dict` that reads `state["query"]` and `state["intent"]`.
- [ ] Import and instantiate `KnowledgeBase` (or accept an injected instance for testability).
- [ ] Call `knowledge_base.search(query, intent, top_k=RETRIEVAL_TOP_K, threshold=RELEVANCE_THRESHOLD)`.
- [ ] Return `{"retrieved_docs": results}`.
- [ ] If `intent` is `"unknown"`, search across all categories (do not filter by intent).
- [ ] Handle `KnowledgeBase` initialization errors gracefully by returning `{"retrieved_docs": []}`.

## 5 — Implement Responder Node

File: `app/nodes/responder.py`

- [ ] Define `responder_node(state: SupportState) -> dict` that reads `query`, `intent`, and `retrieved_docs`.
- [ ] Build a prompt injecting retrieved doc titles and contents as context, instructing the LLM to answer strictly from the provided material.
- [ ] Include tone instructions: professional, empathetic, cite article titles where applicable.
- [ ] Call `generate_text()` with `RESPONSE_MODEL`.
- [ ] Return `{"response": response_text}`.
- [ ] When `retrieved_docs` is empty, generate a fallback response acknowledging the issue and stating a human agent will follow up — no LLM call needed.

## 6 — Implement Evaluator Node

File: `app/nodes/evaluator.py`

- [ ] Define `evaluator_node(state: SupportState) -> dict` that reads `query`, `intent`, `retrieved_docs`, and `response`.
- [ ] Build an evaluation prompt asking the LLM to score the response on factual grounding (0–1), completeness (0–1), and tone (0–1).
- [ ] Call `generate_structured()` with `CLASSIFICATION_MODEL` and a schema expecting `{"grounding": float, "completeness": float, "tone": float}`.
- [ ] Compute `confidence` as the weighted average: `0.5 * grounding + 0.3 * completeness + 0.2 * tone`.
- [ ] Set `escalate = confidence < CONFIDENCE_THRESHOLD`.
- [ ] Return `{"confidence": confidence, "escalate": escalate}`.
- [ ] If the LLM call fails, default to `{"confidence": 0.0, "escalate": True}` (fail safe).

## 7 — Build Graph Transitions

File: `app/graph.py`

- [ ] Import `StateGraph`, `START`, `END` from `langgraph.graph`.
- [ ] Import node functions from `app.nodes.classifier`, `app.nodes.retriever`, `app.nodes.responder`, `app.nodes.evaluator`.
- [ ] Import `SupportState` from `app.state`.
- [ ] Create `StateGraph(SupportState)`.
- [ ] Add four nodes: `"classifier"`, `"retriever"`, `"responder"`, `"evaluator"`.
- [ ] Add linear edges: `START → classifier`, `classifier → retriever`, `retriever → responder`, `responder → evaluator`, `evaluator → END`.
- [ ] Define `build_graph() -> CompiledGraph` that wires everything and calls `graph.compile()`.
- [ ] Write a unit test: invoke the compiled graph with a mock state and assert all four nodes execute in order.

