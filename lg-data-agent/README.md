# Data Analysis Agent

## Overview

A LangGraph data analysis workflow that plans tabular operations, executes them deterministically, interprets the results, and loops through an evaluator until the analysis is sufficient. The project is aimed at structured data reasoning with controlled retries.

## System Flow

The workflow generates an analysis plan, executes the plan over a dataset, interprets the result, evaluates quality, and re-enters the loop when the analysis is incomplete or incorrect.

```text
Query + Data -> Planner -> Executor -> Analyzer -> Evaluator -> Retry or Output
```

## Architecture

The project uses a LangGraph state machine with separate planning, execution, interpretation, and evaluation nodes so retry decisions remain explicit in the graph.

| Module | Responsibility |
|--------|----------------|
| graph.py | Defines the LangGraph workflow and evaluator loop. |
| state.py | Defines the workflow state passed between nodes. |
| nodes/ | Contains planner, executor, analyzer, and evaluator nodes. |
| data_loader.py | Loads tabular datasets for analysis. |
| chart.py | Generates charts and visualization artifacts when needed. |

## Features

- LangGraph retry loop gated by an evaluator node.
- Deterministic execution path for planned analysis steps.
- LLM-backed interpretation layered on top of computed results.
- Visualization support for analytical outputs.

## Example Usage

### Shared API

```bash
curl -X POST http://127.0.0.1:8000/data-analysis-agent/run \
  -H "Content-Type: application/json" \
  -d '{"input": "Analyze sales trends --data data/sales.csv"}'
```

## Evaluation

```text
POST /eval/data-analysis-agent
```

Primary metrics: analysis accuracy, code execution success rate, iteration count, latency, and failure rate.
