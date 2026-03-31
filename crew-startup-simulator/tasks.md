# Tasks

## 1 — Define Agents

File: `app/agents.py`

- [ ] Import `Agent` from `crewai`.
- [ ] Define `REASONING_MODEL = "gemini-3.1-pro-preview"` and `SUMMARY_MODEL = "gemini-3-flash-preview"` constants.
- [ ] Create `build_ceo() -> Agent` with role `"Chief Executive Officer"`, goal to transform a raw idea into a vision with target market, value proposition, competitive positioning, and success metrics, and backstory as an experienced startup founder. Use `REASONING_MODEL`.
- [ ] Create `build_product_manager() -> Agent` with role `"Head of Product"`, goal to define product scope, core features, user personas, and a prioritized roadmap from the CEO's vision, and backstory as a senior PM who ships B2B/B2C products. Use `REASONING_MODEL`.
- [ ] Create `build_cto() -> Agent` with role `"Chief Technology Officer"`, goal to design system architecture, technology stack, and infrastructure requirements from the product spec, and backstory as a senior engineering leader who balances excellence with pragmatic delivery. Use `REASONING_MODEL`.
- [ ] Create `build_engineer() -> Agent` with role `"Lead Engineer"`, goal to produce a sprint-level implementation plan with task breakdown, milestones, and timeline from the architecture, and backstory as a staff engineer experienced in greenfield builds. Use `SUMMARY_MODEL`.
- [ ] Each builder function should return a fully configured `Agent` instance with `verbose=True`.

## 2 — Define Tasks

File: `app/tasks.py`

- [ ] Import `Task` from `crewai`.
- [ ] Create `build_vision_task(agent, idea: str) -> Task` that assigns the CEO agent to analyze the startup idea and produce a structured vision document. Set `expected_output` describing the required sections: mission, target market, value proposition, competitive advantages, success metrics, go-to-market strategy.
- [ ] Create `build_product_task(agent) -> Task` that assigns the PM agent to define the product specification. Set `expected_output` describing: user personas, MVP feature set, feature prioritization, user stories, phased roadmap.
- [ ] Create `build_architecture_task(agent) -> Task` that assigns the CTO agent to design the technical architecture. Set `expected_output` describing: system diagram, tech stack with rationale, data model, API design, infrastructure requirements, scalability strategy, technical risks.
- [ ] Create `build_execution_task(agent) -> Task` that assigns the Engineer agent to produce an implementation plan. Set `expected_output` describing: sprint breakdown, task list with estimates, dependency graph, milestones, risk mitigation, MVP definition of done.
- [ ] Each task description should instruct the agent to build on all prior context.

## 3 — Build Crew

File: `app/crew.py`

- [ ] Import `Crew`, `Process` from `crewai`.
- [ ] Import agent builders from `app.agents` and task builders from `app.tasks`.
- [ ] Define `build_crew(idea: str, verbose: bool = True) -> Crew`.
- [ ] Inside `build_crew`, instantiate all four agents using the builder functions.
- [ ] Inside `build_crew`, instantiate all four tasks using the builder functions, passing the corresponding agent and the `idea` string to the vision task.
- [ ] Construct and return a `Crew` with `process=Process.sequential`, passing agents and tasks in order: CEO → PM → CTO → Engineer.
- [ ] Pass `verbose` through to the `Crew` constructor.

## 4 — Run Workflow

File: `app/crew.py` (extend from task 3)

- [ ] Define `run(idea: str, verbose: bool = True) -> str` that calls `build_crew(idea, verbose)` and then `crew.kickoff()`.
- [ ] Extract the final output from the kickoff result.
- [ ] Return the full pipeline output as a string.
- [ ] Wrap `crew.kickoff()` in a try/except. On failure, raise `RuntimeError` with the agent name and error message.

