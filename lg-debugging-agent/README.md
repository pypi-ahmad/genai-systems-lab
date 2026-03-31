# Debugging Agent

## Overview

A LangGraph debugging workflow that analyzes faulty code, proposes a fix, runs tests, and loops through evaluation until the issue is resolved or the retry budget is exhausted. The project focuses on graph-controlled iterative debugging.

## System Flow

The workflow inspects the bug report or failing code, generates a candidate fix, runs validation or tests, and uses an evaluator node to decide whether another repair cycle is required.

```text
Bug Report -> Analyzer -> Fixer -> Tester -> Evaluator -> Retry or Resolved Output
```

## Architecture

The implementation separates bug analysis, fix generation, validation, and routing logic so the repair cycle remains explicit and testable inside the graph.

| Module | Responsibility |
|--------|----------------|
| graph.py | Builds the LangGraph loop for iterative debugging. |
| state.py | Stores bug context, proposed fixes, and evaluation state. |
| nodes/ | Contains analyzer, fixer, tester, and evaluator nodes. |
| sandbox.py | Runs tests or validation in a controlled environment. |
| main.py | Exposes `run(input, api_key)` for the shared runtime and API platform. |

## Features

- Graph-controlled fix-test-evaluate loop.
- Explicit evaluator-based retry decisions.
- Separation between bug analysis and validation execution.
- Structured workflow suited to debugging automation experiments.

## Example Usage

### Shared API

```bash
curl -X POST http://127.0.0.1:8000/debugging-agent/run \
  -H "Content-Type: application/json" \
  -d '{"input": "Function crashes on empty input and should return an empty list"}'
```

## Evaluation

```text
POST /eval/debugging-agent
```

Primary metrics: bug resolution rate, retry count, test pass rate, latency, and failure rate.
