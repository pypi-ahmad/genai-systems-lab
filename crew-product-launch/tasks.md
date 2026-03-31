# Tasks

## 1 — Define Agents

File: `app/agents.py`

- [ ] Import `Agent` from `crewai`.
- [ ] Define `REASONING_MODEL = "gemini/gemini-3.1-pro-preview"` and `SUMMARY_MODEL = "gemini/gemini-3-flash-preview"` constants.
- [ ] Create `build_market_researcher() -> Agent` with role `"Senior Market Researcher"`, goal to produce a structured market analysis covering industry landscape, competitor mapping, market sizing, growth trends, and key opportunities/threats for the product launch, and backstory as a market intelligence professional with 12 years in product-led companies specializing in competitive analysis and TAM/SAM/SOM estimation. Use `REASONING_MODEL`.
- [ ] Create `build_customer_analyst() -> Agent` with role `"Senior Customer Analyst"`, goal to define target customer segments with detailed personas, pain points, buying behavior, and decision criteria based on market research findings, and backstory as a customer research specialist who builds personas from behavioral data focusing on jobs-to-be-done and purchase triggers. Use `REASONING_MODEL`.
- [ ] Create `build_product_strategist() -> Agent` with role `"Head of Product Strategy"`, goal to define clear product positioning, core messaging, value propositions per segment, and competitive differentiation based on market analysis and customer personas, and backstory as a product strategist who has launched products from zero-to-one across SaaS, consumer, and platform businesses. Use `REASONING_MODEL`.
- [ ] Create `build_marketing_strategist() -> Agent` with role `"VP of Marketing"`, goal to produce a detailed go-to-market plan with channel strategy, campaign tactics, launch timeline, budget allocation, and success metrics, and backstory as a growth marketing leader who plans backward from revenue targets and works in terms of funnel economics and channel ROI. Use `REASONING_MODEL`.
- [ ] Each builder function should return a fully configured `Agent` instance with `verbose=True`.

## 2 — Define Tasks

File: `app/tasks.py`

- [ ] Import `Task` from `crewai`.
- [ ] Define `MARKET_SCHEMA` as a dict with keys: `industry_overview`, `competitors`, `market_size`, `growth_drivers`, `barriers`, `timing_assessment`, `opportunities`.
- [ ] Define `CUSTOMER_SCHEMA` as a dict with keys: `segments`, `personas`, `buying_journey`, `decision_criteria`, `adoption_barriers`.
- [ ] Define `POSITIONING_SCHEMA` as a dict with keys: `positioning_statement`, `category`, `messaging_framework`, `value_propositions`, `differentiators`, `proof_points`.
- [ ] Define `GTM_SCHEMA` as a dict with keys: `channel_strategy`, `campaigns`, `launch_phases`, `budget_allocation`, `kpis`, `contingencies`.
- [ ] Create `build_market_task(agent, product: str) -> Task` that assigns the Market Researcher agent to analyze the market landscape, competitors, and dynamics for the product. Embed `MARKET_SCHEMA` as JSON in the description. Set `expected_output` requiring structured JSON matching the schema.
- [ ] Create `build_customer_task(agent, market_task) -> Task` that assigns the Customer Analyst agent to define target segments and personas based on market research. Embed `CUSTOMER_SCHEMA` as JSON in the description. Set `context=[market_task]`. Set `expected_output` requiring structured JSON.
- [ ] Create `build_positioning_task(agent, market_task, customer_task) -> Task` that assigns the Product Strategist agent to define positioning and messaging based on market analysis and customer personas. Embed `POSITIONING_SCHEMA` as JSON in the description. Set `context=[market_task, customer_task]`. Set `expected_output` requiring structured JSON.
- [ ] Create `build_gtm_task(agent, market_task, customer_task, positioning_task) -> Task` that assigns the Marketing Strategist agent to produce a GTM execution plan. Embed `GTM_SCHEMA` as JSON in the description. Set `context=[market_task, customer_task, positioning_task]`. Set `expected_output` requiring structured JSON.

## 3 — Build Crew

File: `app/crew.py`

- [ ] Import `Crew`, `Process` from `crewai`.
- [ ] Import agent builders from `app.agents` and task builders from `app.tasks`.
- [ ] Define `build_crew(product: str, verbose: bool = True) -> Crew`.
- [ ] Inside `build_crew`, instantiate all four agents using the builder functions.
- [ ] Inside `build_crew`, instantiate all four tasks using the builder functions, passing the corresponding agent, `product` string to the market task, and upstream tasks as context to each subsequent task.
- [ ] Construct and return a `Crew` with `process=Process.sequential`, passing agents and tasks in order: Market Researcher → Customer Analyst → Product Strategist → Marketing Strategist.
- [ ] Pass `verbose` through to the `Crew` constructor.

## 4 — Execute Workflow

File: `app/crew.py` (extend from task 3)

- [ ] Define `run(product: str, verbose: bool = True) -> str` that calls `build_crew(product, verbose)` and then `crew.kickoff()`.
- [ ] Extract the final output from the kickoff result.
- [ ] Return the full pipeline output as a string.
- [ ] Wrap `crew.kickoff()` in a try/except. On failure, raise `RuntimeError` with the agent name and error message.

