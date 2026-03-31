# Tasks

## 1 — Define Agents

File: `app/agents.py`

- [ ] Import `Agent` from `crewai`.
- [ ] Define `RESEARCH_MODEL = "gemini-3.1-pro-preview"` and `FAST_MODEL = "gemini-3-flash-preview"` constants.
- [ ] Create `build_researcher() -> Agent` with role `"Senior Research Analyst"`, goal to produce a comprehensive research brief with verified facts, data points, and source references, and `llm=RESEARCH_MODEL`.
- [ ] Create `build_writer() -> Agent` with role `"Content Writer"`, goal to create an engaging article from the research brief with clear structure and narrative, and `llm=RESEARCH_MODEL`.
- [ ] Create `build_editor() -> Agent` with role `"Senior Editor"`, goal to polish the draft into publication-quality content — fix structure, tighten prose, ensure factual accuracy, and `llm=FAST_MODEL`.
- [ ] Create `build_seo_expert() -> Agent` with role `"SEO Specialist"`, goal to optimize headings, meta description, keyword density, and readability while preserving editorial quality, and `llm=FAST_MODEL`.
- [ ] Each builder should set `backstory`, `verbose=True`, and `allow_delegation=False`.

## 2 — Define Tasks

File: `app/tasks.py`

- [ ] Import `Task` from `crewai` and agent builders from `app.agents`.
- [ ] Create `build_research_task(agent, topic: str) -> Task` with a description template that includes `{topic}` and `expected_output="A structured research brief with key findings, statistics, and sources"`.
- [ ] Create `build_writing_task(agent) -> Task` with description instructing the agent to transform the research brief into a complete Markdown article (title, intro, body sections, conclusion) and `expected_output="Complete article draft in Markdown"`.
- [ ] Create `build_editing_task(agent) -> Task` with description instructing the agent to refine grammar, clarity, tone, and factual consistency and `expected_output="Polished, publication-ready article"`.
- [ ] Create `build_seo_task(agent) -> Task` with description instructing the agent to optimize headings, add meta description, check keyword density, and score readability and `expected_output="SEO-optimized article with metadata block"`.
- [ ] Each task builder returns a `Task` instance — it does not call the LLM.

## 3 — Build Crew

File: `app/crew.py`

- [ ] Import `Crew`, `Process` from `crewai`.
- [ ] Import agent builders from `app.agents` and task builders from `app.tasks`.
- [ ] Define `build_crew(topic: str) -> Crew`.
- [ ] Inside `build_crew`: instantiate all four agents using their builders.
- [ ] Inside `build_crew`: instantiate all four tasks, passing the corresponding agent and `topic` where needed.
- [ ] Assemble `Crew(agents=[...], tasks=[...], process=Process.sequential, verbose=True)`.
- [ ] Return the assembled `Crew` instance (do not call `kickoff`).

## 4 — Execute Pipeline

File: `app/crew.py` (extend from task 3)

- [ ] Define `run_pipeline(topic: str) -> str` that calls `build_crew(topic)` and then `crew.kickoff(inputs={"topic": topic})`.
- [ ] Extract the final output string from the kickoff result.
- [ ] Return the output string.
- [ ] Catch exceptions from `kickoff`, print the error to stderr, and re-raise.

