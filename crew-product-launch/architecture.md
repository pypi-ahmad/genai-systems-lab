# Architecture

## Overview

The Product Launch Strategy Crew is a CrewAI-based sequential pipeline where four specialized agents collaborate to produce a complete go-to-market strategy for a product launch. Each agent builds on the output of the previous agent, creating a layered strategy that accumulates context at every step. The pipeline transforms a raw product description into market intelligence, customer personas, positioning strategy, and a full marketing execution plan. CrewAI manages agent orchestration, task sequencing, and output chaining.

Primary flow:

```
Product Description → Market Researcher → Customer Analyst → Product Strategist → Marketing Strategist → Launch Plan
```

## Crew Configuration

All agents execute within a single `Crew` configured with `process=Process.sequential`. The four tasks run in fixed order. There are no conditional branches or loops — the pipeline runs exactly four steps, once.

```python
crew = Crew(
    agents=[market_researcher, customer_analyst, product_strategist, marketing_strategist],
    tasks=[market_task, customer_task, positioning_task, gtm_task],
    process=Process.sequential,
    verbose=True,
)
```

### Why sequential

- Customer analysis needs market context to ground personas in real competitive dynamics rather than generic archetypes.
- Product positioning depends on both the competitive landscape and the target customer segments to identify defensible differentiation.
- The Marketing Strategist synthesizes all three upstream outputs — channels, messaging, and pricing cannot be defined without market data, personas, and positioning.
- A single linear pass keeps token usage predictable and avoids coordination overhead.

### Why layered strategy building

Each agent produces a structured deliverable that becomes context for all downstream agents. This layering means:

- The Customer Analyst sees the competitive landscape before defining personas, so segments map to real market gaps.
- The Product Strategist sees both market data and personas, so positioning targets validated needs against validated competitors.
- The Marketing Strategist sees everything, so GTM channels and messaging align with the full strategic picture rather than operating in isolation.

## Agents

Each agent is a CrewAI `Agent` with a defined role, goal, and backstory. Agents use the model assignment appropriate to their task complexity.

### Market Researcher

Analyzes the competitive landscape, market size, trends, and dynamics surrounding the product.

- **Role:** Senior Market Researcher
- **Goal:** Produce a structured market analysis covering industry landscape, competitor mapping, market sizing, growth trends, and key opportunities/threats for the product launch.
- **Backstory:** Market intelligence professional with 12 years in product-led companies. Specializes in competitive analysis, TAM/SAM/SOM estimation, and identifying market timing windows. Evaluates markets through both quantitative data and qualitative trend analysis.
- **Model:** `gemini-3.1-pro-preview` — market analysis requires multi-step reasoning across competitive dynamics, trend extrapolation, and market sizing.
- **Output:** Structured JSON — market report covering industry overview, competitor analysis (direct/indirect), market size estimates, growth drivers, barriers to entry, timing assessment, and key opportunities.

### Customer Analyst

Defines target customer segments and builds detailed personas grounded in the market context.

- **Role:** Senior Customer Analyst
- **Goal:** Define target customer segments with detailed personas, pain points, buying behavior, and decision criteria based on market research findings.
- **Backstory:** Customer research specialist with experience across B2B and B2C launches. Builds personas from behavioral data rather than demographics alone. Focuses on jobs-to-be-done, switching costs, and purchase triggers that drive actual adoption.
- **Model:** `gemini-3.1-pro-preview` — persona development requires reasoning about behavioral patterns, segment prioritization, and alignment with market gaps.
- **Output:** Structured JSON — customer analysis covering primary/secondary segments, persona profiles (demographics, psychographics, jobs-to-be-done, pain points), buying journey stages, decision criteria, and adoption barriers per segment.

### Product Strategist

Defines product positioning, messaging framework, and competitive differentiation.

- **Role:** Head of Product Strategy
- **Goal:** Define clear product positioning, core messaging, value propositions per segment, and competitive differentiation based on market analysis and customer personas.
- **Backstory:** Product strategist who has launched products from zero-to-one across SaaS, consumer, and platform businesses. Thinks in terms of positioning narratives — the intersection of what customers need, what competitors miss, and what the product uniquely delivers.
- **Model:** `gemini-3.1-pro-preview` — positioning requires synthesizing market gaps, customer needs, and competitive dynamics into a coherent strategic narrative.
- **Output:** Structured JSON — positioning strategy covering positioning statement, category definition, messaging framework (per segment), value propositions, competitive differentiators, and proof points.

### Marketing Strategist

Produces the go-to-market execution plan with channels, tactics, timeline, and budget allocation.

- **Role:** VP of Marketing
- **Goal:** Produce a detailed go-to-market plan with channel strategy, campaign tactics, launch timeline, budget allocation, and success metrics based on the full strategic context.
- **Backstory:** Growth marketing leader who has executed product launches from startup to enterprise scale. Balances brand-building with performance marketing. Plans backward from revenue targets and works in terms of funnel economics, channel ROI, and launch sequencing.
- **Model:** `gemini-3.1-pro-preview` — GTM planning requires reasoning across channels, budgets, timing dependencies, and metric projections while incorporating all prior strategic context.
- **Output:** Structured JSON — GTM plan covering channel strategy (organic/paid/partnerships), campaign concepts per segment, launch phases with timeline, budget allocation by channel, KPIs per phase, and risk contingencies.

## Tasks

Each CrewAI `Task` binds an agent to a specific deliverable. Tasks execute in order, and each task receives the output of all preceding tasks as context. All tasks require agents to return structured JSON matching a predefined schema. Schemas are embedded in task descriptions so the LLM sees the exact output shape expected.

### market_task

- **Agent:** Market Researcher
- **Description:** Analyze the market landscape, competitors, and dynamics for the product being launched.
- **Expected output:** JSON with keys: `industry_overview`, `competitors` (array of direct/indirect), `market_size` (TAM/SAM/SOM), `growth_drivers`, `barriers`, `timing_assessment`, `opportunities`.
- **Context:** Product description (user input).

### customer_task

- **Agent:** Customer Analyst
- **Description:** Define target customer segments and detailed personas based on market research findings.
- **Expected output:** JSON with keys: `segments` (array with priority), `personas` (array with demographics, psychographics, jobs_to_be_done, pain_points), `buying_journey`, `decision_criteria`, `adoption_barriers`.
- **Context:** Market Researcher's report.

### positioning_task

- **Agent:** Product Strategist
- **Description:** Define product positioning, messaging framework, and competitive differentiation based on market analysis and customer personas.
- **Expected output:** JSON with keys: `positioning_statement`, `category`, `messaging_framework` (per segment), `value_propositions`, `differentiators`, `proof_points`.
- **Context:** Market report + Customer analysis.

### gtm_task

- **Agent:** Marketing Strategist
- **Description:** Produce a detailed go-to-market execution plan with channels, tactics, timeline, and metrics based on the full strategic context.
- **Expected output:** JSON with keys: `channel_strategy`, `campaigns` (per segment), `launch_phases` (with timeline), `budget_allocation`, `kpis`, `contingencies`.
- **Context:** All prior outputs (market + customer + positioning).

## Structured Outputs

Every task returns a JSON object conforming to a predefined schema. This enables:

- **Programmatic consumption** — downstream agents, APIs, and dashboards can parse outputs without scraping text.
- **Validation** — each output can be checked for required keys before passing to the next agent.
- **Composability** — the final output is a collection of four coherent JSON documents that together form the complete launch strategy.

Schemas are defined as Python dicts in `tasks.py` and serialized into each task's description prompt. If the LLM returns markdown-fenced JSON, the output parser strips fences before parsing.

## Model Usage

| Model | Agents | Rationale |
|---|---|---|
| `gemini-3.1-pro-preview` | Market Researcher, Customer Analyst, Product Strategist, Marketing Strategist | All four tasks require analytical reasoning — market analysis, persona development, positioning synthesis, and GTM planning are high-stakes cognitive tasks |
| `gemini-3-flash-preview` | (available for summaries within agents) | Quick condensation of lengthy upstream context before passing to downstream tasks; used when context windows grow large in later pipeline stages |

### Cost and latency considerations

- The Market Researcher task produces the foundation — a detailed competitive and market analysis that all downstream agents depend on.
- The Customer Analyst and Product Strategist tasks are moderately sized but process growing context windows as upstream outputs accumulate.
- The Marketing Strategist task reasons across the largest context (three prior reports) but produces the most actionable output — the GTM execution plan.
- Total pipeline cost scales linearly with four sequential LLM calls. No retries or loops.

## Error Handling

- If any agent fails to return valid JSON, `main.py` falls back to displaying raw text output.
- CrewAI's built-in retry logic handles transient LLM failures (rate limits, timeouts).
- The `_parse_json` utility strips markdown fences and handles common LLM formatting quirks before `json.loads`.
- Missing schema keys in agent output are logged as warnings but do not halt the pipeline — partial output is still useful for downstream agents.