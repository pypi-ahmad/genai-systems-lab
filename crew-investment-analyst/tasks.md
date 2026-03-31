# Tasks

## 1 — Define Agents

File: `app/agents.py`

- [ ] Import `Agent` from `crewai`.
- [ ] Define `REASONING_MODEL = "gemini-3.1-pro-preview"` and `SUMMARY_MODEL = "gemini-3-flash-preview"` constants.
- [ ] Create `build_market_analyst() -> Agent` with role `"Senior Market Analyst"`, goal to assess industry trends, competitive landscape, market size, and growth drivers for the investment target, and backstory as an equity research analyst with 15 years covering multiple sectors. Use `REASONING_MODEL`.
- [ ] Create `build_financial_analyst() -> Agent` with role `"Senior Financial Analyst"`, goal to analyze key financial metrics, valuation multiples, cash flow health, and profitability trends, and backstory as a CFA charterholder with deep experience in fundamental analysis. Use `REASONING_MODEL`.
- [ ] Create `build_risk_analyst() -> Agent` with role `"Senior Risk Analyst"`, goal to identify material risks spanning market, financial, regulatory, and operational domains with probability and impact assessment, and backstory as a risk management professional from hedge funds and institutional investors. Use `REASONING_MODEL`.
- [ ] Create `build_strategist() -> Agent` with role `"Chief Investment Strategist"`, goal to synthesize all prior analyses into a clear investment recommendation with conviction level, position sizing guidance, and entry/exit criteria, and backstory as a portfolio manager who has allocated capital across cycles. Use `REASONING_MODEL`.
- [ ] Each builder function should return a fully configured `Agent` instance with `verbose=True`.

## 2 — Define Tasks

File: `app/tasks.py`

- [ ] Import `Task` from `crewai`.
- [ ] Create `build_market_task(agent, target: str) -> Task` that assigns the Market Analyst agent to analyze the industry and competitive landscape for the target company. Set `expected_output` describing the required sections: industry overview, growth drivers, competitive positioning, addressable market size, headwinds/tailwinds, sector outlook.
- [ ] Create `build_financial_task(agent) -> Task` that assigns the Financial Analyst agent to evaluate financial health, profitability, and valuation. Set `expected_output` describing: revenue trends, profitability margins, debt/equity structure, cash flow analysis, valuation multiples (P/E, EV/EBITDA, P/FCF), peer comparison.
- [ ] Create `build_risk_task(agent) -> Task` that assigns the Risk Analyst agent to identify and assess material risks using the market and financial analyses. Set `expected_output` describing: risk inventory (type, probability, impact), concentration risks, regulatory exposure, suggested mitigations.
- [ ] Create `build_strategy_task(agent) -> Task` that assigns the Strategist agent to synthesize all prior analyses into a final investment recommendation. Set `expected_output` describing: thesis summary, conviction level (high/medium/low), recommended action (buy/hold/sell/avoid), key catalysts, position sizing rationale, entry/exit criteria, time horizon.
- [ ] Each task description should instruct the agent to build on all prior context.

## 3 — Build Crew

File: `app/crew.py`

- [ ] Import `Crew`, `Process` from `crewai`.
- [ ] Import agent builders from `app.agents` and task builders from `app.tasks`.
- [ ] Define `build_crew(target: str, verbose: bool = True) -> Crew`.
- [ ] Inside `build_crew`, instantiate all four agents using the builder functions.
- [ ] Inside `build_crew`, instantiate all four tasks using the builder functions, passing the corresponding agent and the `target` string to the market task.
- [ ] Construct and return a `Crew` with `process=Process.sequential`, passing agents and tasks in order: Market Analyst → Financial Analyst → Risk Analyst → Strategist.
- [ ] Pass `verbose` through to the `Crew` constructor.

## 4 — Execute Workflow

File: `app/crew.py` (extend from task 3)

- [ ] Define `run(target: str, verbose: bool = True) -> str` that calls `build_crew(target, verbose)` and then `crew.kickoff()`.
- [ ] Extract the final output from the kickoff result.
- [ ] Return the full pipeline output as a string.
- [ ] Wrap `crew.kickoff()` in a try/except. On failure, raise `RuntimeError` with the agent name and error message.

