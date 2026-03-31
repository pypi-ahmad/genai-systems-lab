# Investment Analyst Crew

## Overview

A CrewAI investment research workflow that evaluates opportunities through market analysis, financial reasoning, risk review, strategic positioning, and adversarial challenge. It is built for structured investment memos rather than open-ended chat responses.

## System Flow

The workflow starts from an investment target, builds the business and market case, pressure-tests the opportunity through risk analysis, and finishes with a recommendation shaped by both supportive and skeptical perspectives.

```text
Opportunity -> Market Analyst -> Financial Analyst -> Risk Analyst -> Strategist -> Red Team Reviewer -> Investment Memo
```

## Architecture

The project uses a linear CrewAI process where each specialist adds a new layer of analysis, allowing the final recommendation to reflect both upside and downside reasoning.

| Module | Responsibility |
|--------|----------------|
| agents.py | Defines market, finance, risk, strategy, and adversarial reviewer agents. |
| tasks.py | Defines the staged analysis tasks and expected memo structure. |
| crew.py | Assembles the sequential investment evaluation crew. |
| main.py | Runs the workflow and formats the final output. |

## Features

- Multi-perspective investment analysis with staged reasoning.
- Dedicated risk and red-team review before recommendation output.
- Sequential context handoff across specialist agents.
- Structured memo generation for repeatable opportunity evaluation.

## Example Usage

### Shared API

```bash
curl -X POST http://127.0.0.1:8000/investment-crew/run \
  -H "Content-Type: application/json" \
  -d '{"input": "Evaluate a Series B investment in an AI compliance automation startup"}'
```

## Evaluation

```text
POST /eval/investment-crew
```

Primary metrics: investment thesis quality, risk coverage, recommendation consistency, latency, and failure rate.
