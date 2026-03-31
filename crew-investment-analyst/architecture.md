# Architecture

## Overview

The Investment Analysis Crew is a CrewAI-based sequential pipeline where four specialized agents collaborate to produce a structured investment recommendation. Each agent contributes a distinct analytical perspective — market positioning, financial health, risk exposure, and strategic synthesis. The Strategist receives all prior outputs and produces the final investment decision. CrewAI manages agent orchestration, task sequencing, and output chaining.

Primary flow:

```
Ticker/Company → Market Analyst → Financial Analyst → Risk Analyst → Strategist → Recommendation
```

## Crew Configuration

All agents execute within a single `Crew` configured with `process=Process.sequential`. The four tasks run in fixed order. There are no conditional branches or loops — the pipeline runs exactly four steps, once.

```python
crew = Crew(
    agents=[market_analyst, financial_analyst, risk_analyst, strategist],
    tasks=[market_task, financial_task, risk_task, strategy_task],
    process=Process.sequential,
    verbose=True,
)
```

### Why sequential

- Financial analysis needs market context to interpret metrics relative to industry dynamics.
- Risk assessment needs both market and financial outputs to identify exposure areas.
- The Strategist synthesizes all three perspectives — it cannot run until they are complete.
- A single linear pass keeps token usage predictable and avoids coordination overhead.

## Agents

Each agent is a CrewAI `Agent` with a defined role, goal, and backstory. Agents share the LLM configuration specified by their model assignment but serve distinct analytical functions.

### Market Analyst

Evaluates macro and industry-level conditions surrounding the investment target.

- **Role:** Senior Market Analyst
- **Goal:** Assess industry trends, competitive landscape, market size, and growth drivers relevant to the investment target.
- **Backstory:** Equity research analyst with 15 years covering multiple sectors. Specialized in identifying inflection points, secular trends, and competitive moats. Evaluates markets through both top-down macro and bottom-up industry lens.
- **Model:** `gemini-3.1-pro-preview` — market analysis requires reasoning across macro indicators, competitive dynamics, and trend extrapolation.
- **Output:** Market report covering industry overview, growth drivers, competitive positioning, addressable market size, headwinds/tailwinds, and sector outlook.

### Financial Analyst

Evaluates quantitative financial health and valuation of the target.

- **Role:** Senior Financial Analyst
- **Goal:** Analyze key financial metrics, valuation multiples, cash flow health, and profitability trends to determine financial strength.
- **Backstory:** CFA charterholder with deep experience in fundamental analysis. Reads financial statements the way a mechanic reads engine diagnostics — identifying stress points, efficiency patterns, and sustainability of earnings.
- **Model:** `gemini-3.1-pro-preview` — financial evaluation requires multi-step reasoning across income statements, balance sheets, and cash flow dynamics.
- **Output:** Financial assessment covering revenue trends, profitability margins, debt/equity structure, cash flow analysis, valuation multiples (P/E, EV/EBITDA, P/FCF), and peer comparison.

### Risk Analyst

Identifies and quantifies risk factors across market, financial, and operational dimensions.

- **Role:** Senior Risk Analyst
- **Goal:** Identify material risks spanning market, financial, regulatory, and operational domains, and assess their probability and potential impact.
- **Backstory:** Risk management professional who has worked across hedge funds and institutional investors. Thinks in terms of downside scenarios, tail risks, and correlation exposures. Skeptical by disposition — the job is to find what can go wrong.
- **Model:** `gemini-3.1-pro-preview` — risk identification requires nuanced reasoning about dependencies, edge cases, and second-order effects.
- **Output:** Risk report covering identified risks (categorized by type), probability/impact assessment for each, concentration risks, regulatory exposure, and suggested mitigations.

### Strategist

Synthesizes all prior analyses into a final investment recommendation.

- **Role:** Chief Investment Strategist
- **Goal:** Integrate market, financial, and risk analyses into a clear investment recommendation with conviction level, position sizing guidance, and entry/exit criteria.
- **Backstory:** Portfolio manager who has allocated capital across cycles. Balances quantitative rigor with qualitative judgment. Focuses on asymmetric risk/reward and catalysts that drive re-rating.
- **Model:** `gemini-3.1-pro-preview` — the synthesis step is the highest-stakes reasoning task, integrating three separate analytical perspectives into a coherent decision.
- **Output:** Investment recommendation covering thesis summary, conviction level (high/medium/low), recommended action (buy/hold/sell/avoid), key catalysts, position sizing rationale, entry/exit criteria, and time horizon.

## Tasks

Each CrewAI `Task` binds an agent to a specific deliverable. Tasks execute in order, and each task receives the output of all preceding tasks as context.

### market_task

- **Agent:** Market Analyst
- **Description:** Analyze the industry and competitive landscape for the target company.
- **Expected output:** Market report with sections: industry overview, growth drivers, competitive positioning, market size, headwinds/tailwinds, sector outlook.
- **Context:** User input (ticker or company name with optional notes).

### financial_task

- **Agent:** Financial Analyst
- **Description:** Evaluate the financial health, profitability, and valuation of the target.
- **Expected output:** Financial assessment with sections: revenue trends, margins, debt structure, cash flow, valuation multiples, peer comparison.
- **Context:** Market Analyst's report.

### risk_task

- **Agent:** Risk Analyst
- **Description:** Identify and assess material risks across all dimensions using the market and financial analyses.
- **Expected output:** Risk report with sections: risk inventory (type, probability, impact), concentration risks, regulatory exposure, mitigations.
- **Context:** Market report + Financial assessment.

### strategy_task

- **Agent:** Strategist
- **Description:** Synthesize all prior analyses into a final investment recommendation.
- **Expected output:** Investment recommendation with sections: thesis, conviction level, action, catalysts, position sizing, entry/exit, time horizon.
- **Context:** All prior outputs (market + financial + risk).

## Model Usage

| Model | Agents | Rationale |
|---|---|---|
| `gemini-3.1-pro-preview` | Market Analyst, Financial Analyst, Risk Analyst, Strategist | All four tasks require analytical reasoning — market dynamics, financial modeling, risk assessment, and investment synthesis are high-stakes cognitive tasks |
| `gemini-3-flash-preview` | (used for summaries within agents if needed) | Quick condensation of lengthy context windows before passing to downstream tasks |

### Cost and latency considerations

- The Market Analyst and Financial Analyst tasks produce the longest outputs — detailed analytical reports with supporting evidence.
- The Risk Analyst task is moderately sized but requires processing two prior reports as context.
- The Strategist task produces the shortest output but reasons across the largest context window (three prior reports).
- Total pipeline runs four LLM calls in sequence. Expect 40–80 seconds end-to-end depending on output length.
- `gemini-3-flash-preview` can be used as an optional summarization step if upstream outputs exceed context limits, but the default pipeline passes full outputs.

## Data Flow

```
User Input (ticker / company)
    │
    ▼
┌──────────────────┐
│  Market Analyst  │
│  (industry,      │
│   competition)   │
└──────────────────┘
         │
    market report
         │
         ▼
┌──────────────────┐
│ Financial Analyst│
│  (metrics,       │
│   valuation)     │
└──────────────────┘
         │
  financial assessment
         │
         ▼
┌──────────────────┐
│   Risk Analyst   │
│  (risks,         │
│   mitigations)   │
└──────────────────┘
         │
     risk report
         │
         ▼
┌──────────────────┐
│    Strategist    │
│  (synthesis,     │
│   recommendation)│
└──────────────────┘
         │
  investment recommendation
         │
         ▼
    Final Output
```

## Error Handling

- **LLM failure:** CrewAI retries failed LLM calls with exponential backoff. If a task fails after retries, the crew raises and `main.py` reports the error.
- **Empty output:** If an agent returns an empty or malformed response, downstream agents receive it as-is. The Strategist should note incomplete inputs in its recommendation.
- **Context overflow:** If accumulated context exceeds model limits, use `gemini-3-flash-preview` to summarize prior outputs before passing to the next task.

## Extension Points

- **Tool integration:** Agents can be extended with CrewAI tools (e.g., web search for live market data, API calls for financial data providers).
- **Peer review round:** Add review tasks where each analyst critiques another's output, following the pattern established in the crew-startup-simulator project.
- **Multi-asset comparison:** Run parallel crews for multiple tickers and add a comparison Strategist that ranks them.
- **Human-in-the-loop:** Add a gate after the Risk Analyst where a human reviewer can approve or reject before the Strategist runs.