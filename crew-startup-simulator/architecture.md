# Architecture

## Overview

The AI Startup Team Simulator is a CrewAI-based sequential pipeline where four specialized agents collaborate to transform a raw startup idea into a complete execution plan. The pipeline begins with a brainstorming phase where three agents each propose a startup direction, then the CEO evaluates and selects the best approach. The chosen direction feeds into the core pipeline where each agent builds on the previous output. After all primary deliverables are produced, a peer review round runs where each agent critiques a different agent's output. CrewAI manages agent orchestration, task delegation, and output chaining — there is no custom routing logic.

Primary flow:

```
Idea → [PM, CTO, Engineer proposals] → CEO Selection → PM → CTO → Engineer → Peer Reviews (4) → Final Output
```

## Crew Configuration

All agents execute within a single `Crew` configured with `process=Process.sequential`. The pipeline runs exactly eleven steps: three proposals, one CEO selection, three core deliverables, and four peer reviews. There are no conditional branches or loops.

```python
crew = Crew(
    agents=[ceo, product_manager, cto, engineer],
    tasks=[
        pm_proposal, cto_proposal, eng_proposal,  # brainstorming
        selection_task,                             # CEO selects direction
        product_task, architecture_task, execution_task,  # core pipeline
        selection_review, product_review, architecture_review, execution_review,  # peer reviews
    ],
    process=Process.sequential,
    verbose=True,
)
```

### Why sequential

- Each agent depends on the full output of the previous agent. Parallel execution would produce disconnected outputs.
- The brainstorming proposals are independent but still run sequentially — CrewAI's sequential process keeps orchestration simple.
- A single linear pass keeps token usage predictable and avoids coordination overhead.
- The peer review round runs after all primary tasks so reviewers have full pipeline context.
- The pipeline can be extended later (e.g., adding a revision round after reviews) without changing the orchestration model.

## Agents

Each agent is a CrewAI `Agent` with a defined role, goal, and backstory that constrains its behavior. All agents share the same LLM configuration but serve distinct functions.

### CEO

Defines the startup vision, market positioning, and strategic direction.

- **Role:** Chief Executive Officer
- **Goal:** Transform the raw idea into a clear vision statement with target market, value proposition, competitive positioning, and success metrics.
- **Backstory:** Experienced startup founder who has built and scaled multiple companies. Thinks in terms of market opportunity, defensibility, and growth potential.
- **Model:** `gemini-3.1-pro-preview` — strategic reasoning requires evaluating market dynamics, competitive landscape, and long-term viability.
- **Output:** Vision document covering mission, target market, value proposition, competitive advantages, key success metrics, and go-to-market strategy.

### Product Manager

Translates the CEO's vision into a concrete product definition.

- **Role:** Head of Product
- **Goal:** Define the product scope, core features, user personas, and a prioritized roadmap based on the CEO's vision.
- **Backstory:** Senior product manager with experience shipping B2B and B2C products. Skilled at turning abstract strategy into specific, buildable features with clear acceptance criteria.
- **Model:** `gemini-3.1-pro-preview` — product scoping requires reasoning about user needs, feature dependencies, and prioritization tradeoffs.
- **Output:** Product specification covering user personas, core feature set (MVP), feature prioritization (MoSCoW or similar), user stories for top features, and a phased roadmap.

### CTO

Designs the technical architecture to support the product specification.

- **Role:** Chief Technology Officer
- **Goal:** Define the system architecture, technology stack, infrastructure requirements, and technical constraints based on the product specification.
- **Backstory:** Senior engineering leader who has designed systems at scale. Balances technical excellence with pragmatic delivery, favoring proven technologies for MVPs and reserving cutting-edge choices for genuine technical differentiators.
- **Model:** `gemini-3.1-pro-preview` — architecture decisions require reasoning about scalability, cost, team capabilities, and technical risk.
- **Output:** Technical architecture document covering system diagram, technology stack with rationale, data model overview, API design approach, infrastructure requirements, scalability strategy, and identified technical risks.

### Engineer

Converts the technical architecture into an actionable implementation plan.

- **Role:** Lead Engineer
- **Goal:** Produce a detailed execution plan with sprint-level breakdown, task assignments, milestones, and delivery timeline based on the technical architecture.
- **Backstory:** Staff engineer experienced in greenfield builds and team leadership. Focuses on incremental delivery, risk mitigation through early integration, and realistic time estimates.
- **Model:** `gemini-3-flash-preview` — execution planning is a structured synthesis task; speed matters more than deep reasoning since the hard decisions are already made.
- **Output:** Implementation plan covering sprint breakdown (2-week sprints), task list per sprint with effort estimates, dependency graph, milestone definitions, risk mitigation actions, and definition of done for MVP.

## Tasks

Each CrewAI `Task` binds an agent to a specific deliverable. Tasks execute in order, and each task receives the output of all preceding tasks as context. All tasks require agents to return structured JSON matching a predefined schema. The schemas are embedded in each task's description so the LLM sees the exact shape expected.

### Brainstorming Phase

Three agents independently propose a startup direction from their unique perspectives before any detailed planning begins.

#### proposal_task (×3)

- **Agents:** Product Manager, CTO, Lead Engineer (one task each)
- **Description:** Propose one compelling startup direction from the agent's professional perspective.
- **Expected output:** JSON object with keys: `angle`, `target_market`, `differentiator`, `monetization`, `risks`, `rationale`.
- **Context:** Raw startup idea (user input).

#### selection_task

- **Agent:** CEO
- **Description:** Evaluate all three proposals and select the strongest direction, synthesize elements, or modify a proposal. Produce the strategic vision.
- **Expected output:** JSON object with keys: `selected_proposal`, `reasoning`, `mission`, `target_market`, `value_proposition`, `competitive_advantages`, `success_metrics`, `go_to_market`.
- **Context:** All three proposal outputs.

### Core Pipeline

### product_task

- **Agent:** Product Manager
- **Description:** Based on the CEO's selected direction, define the product specification.
- **Expected output:** JSON object with keys: `personas`, `mvp_features`, `user_stories`, `roadmap`.
- **Context:** CEO's selection document.

### architecture_task

- **Agent:** CTO
- **Description:** Based on the product specification, design the technical architecture.
- **Expected output:** JSON object with keys: `system_overview`, `tech_stack`, `data_model`, `api_design`, `infrastructure`, `scalability`, `risks`.
- **Context:** CEO's vision + PM's product spec.

### execution_task

- **Agent:** Engineer
- **Description:** Based on the technical architecture, produce a detailed implementation plan.
- **Expected output:** JSON object with keys: `sprints`, `milestones`, `dependencies`, `risks`, `mvp_definition_of_done`.
- **Context:** All prior outputs (vision + product spec + architecture).

## Peer Review Round

After all four primary tasks complete, each agent peer-reviews a different agent's deliverable. Reviews evaluate completeness, feasibility, internal consistency, and alignment with the overall plan. Each review returns a JSON object with keys: `strengths`, `weaknesses`, `gaps`, `recommendations`.

| Review Task | Reviewer | Reviews | Rationale |
|---|---|---|---|
| `selection_review` | Product Manager | CEO's Selection & Vision | PM validates that the chosen direction translates to buildable product goals |
| `product_review` | CTO | PM's Product Specification | CTO validates technical feasibility of proposed features |
| `architecture_review` | Engineer | CTO's Technical Architecture | Engineer validates buildability and effort assumptions |
| `execution_review` | CEO | Engineer's Execution Plan | CEO validates timeline aligns with strategic goals |

Reviews are built using `build_review_task(reviewer, target_task, target_role)` — a generic task builder that adapts the critique prompt to the target role. Each review task receives the original task's output as context.

## Model Usage

| Model | Agents | Rationale |
|---|---|---|
| `gemini-3.1-pro-preview` | CEO, Product Manager, CTO | Strategic reasoning, product scoping, and architecture design all require strong analytical capabilities |
| `gemini-3-flash-preview` | Engineer | Implementation planning is a structured synthesis task — speed and fluency matter more than deep reasoning |

### Cost and latency considerations

- The CEO and CTO tasks produce the most tokens since their outputs are detailed strategic and technical documents.
- The Engineer task uses the cheaper, faster model since its job is to organize decisions already made by upstream agents into a structured plan.
- Peer review tasks reuse each agent's assigned model — reviews are shorter than primary outputs so the marginal cost is modest.
- Total pipeline runs eleven LLM calls in sequence (3 proposals + 1 selection + 3 core + 4 reviews). Expect 90–180 seconds end-to-end depending on output length.

## Data Flow

```
User Input (idea string)
    │
    ▼
┌──────────────────────────────────────────────┐
│          Brainstorming Phase                 │
│  ┌────────────┐ ┌───────┐ ┌──────────────┐  │
│  │     PM     │ │  CTO  │ │   Engineer   │  │
│  │  proposal  │ │ prop. │ │   proposal   │  │
│  └─────┬──────┘ └───┬───┘ └──────┬───────┘  │
│        └────────────┼────────────┘           │
└─────────────────────┼────────────────────────┘
                      ▼
               ┌─────────────┐
               │     CEO     │
               │  Selection  │
               └──────┬──────┘
                      │  selected direction
                      ▼
             ┌──────────────────┐
             │  Product Manager │
             │   product spec   │
             └────────┬─────────┘
                      │
                      ▼
               ┌─────────────┐
               │     CTO     │
               │  arch. doc  │
               └──────┬──────┘
                      │
                      ▼
              ┌────────────────┐
              │   Engineer     │
              │ execution plan │
              └───────┬────────┘
                      │
                      ▼
            ┌─────────────────┐
            │  Peer Reviews   │
            │  PM → Selection │
            │  CTO → Product  │
            │  Eng → Arch     │
            │  CEO → Exec     │
            └────────┬────────┘
                     │
                     ▼
               Final Output
```

The brainstorming phase lets each agent propose a direction from their unique perspective before any detailed planning begins. The CEO then evaluates all proposals and selects or synthesizes the best approach, ensuring the team's diverse viewpoints inform the strategic direction. Each agent receives the full accumulated context — not just the immediately preceding output. The peer review round adds cross-functional validation — each reviewer brings their own expertise to critique a different role's work.

## Production Design Notes

### Output structure

- All agents return JSON objects matching predefined schemas defined in `tasks.py` (`PROPOSAL_SCHEMA`, `SELECTION_SCHEMA`, `PRODUCT_SCHEMA`, `ARCHITECTURE_SCHEMA`, `EXECUTION_SCHEMA`, `REVIEW_SCHEMA`).
- Each task's description embeds the full JSON schema so the LLM sees the expected shape.
- `main.py` normalizes each task's raw output as JSON when possible and otherwise preserves the raw text in the structured response.
- Final output is eleven labeled JSON sections — three proposals, one CEO selection, three core deliverables, and four peer reviews.

### Error handling

- Wrap `crew.kickoff()` in a try/except. If any agent fails, log which agent failed and the partial outputs collected so far.
- CrewAI's built-in retry mechanism handles transient LLM failures. Configure `max_retry_limit` on the crew for additional resilience.

### Observability

- Enable `verbose=True` on the crew to log agent reasoning and task transitions during development.
- Log each task's input length, output length, and execution time for cost tracking.
- Store the full pipeline output (all four documents) as a JSON artifact for post-run analysis.

### Configuration

Key parameters should be externalized:

| Parameter | Default | Purpose |
|---|---|---|
| `REASONING_MODEL` | `gemini-3.1-pro-preview` | Model for CEO, PM, CTO |
| `SUMMARY_MODEL` | `gemini-3-flash-preview` | Model for Engineer |
| `VERBOSE` | `True` | Enable crew execution logging |
| `MAX_RETRY_LIMIT` | `3` | Retry limit for failed LLM calls |

### Testing

- Each agent can be tested in isolation by constructing a `Task` with hardcoded context and asserting the output structure.
- Integration test the full crew with a mock LLM that returns canned responses per agent role, verifying all four stages execute and the final output contains sections from each agent.
- Test edge cases: empty idea string (should fail fast), very long idea (should still produce bounded output), and LLM timeout (should retry or fail gracefully).

## Summary

The system is a four-agent CrewAI sequential pipeline with a peer review round. The CEO sets strategic direction, the Product Manager defines what to build, the CTO designs how to build it, and the Engineer plans the execution. After all four primary deliverables are produced, each agent peer-reviews a different agent's output — PM reviews the vision, CTO reviews the product spec, Engineer reviews the architecture, and CEO reviews the execution plan. State flows forward through CrewAI's task chaining — no custom orchestrator, no branching logic. The stronger reasoning model handles strategy and architecture; the faster model handles execution planning. The review round adds eight tasks total (4 primary + 4 reviews) for cross-functional quality assurance.
