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
| nodes/tester.py | Runs generated Python in an ordinary subprocess for trusted local experiments. It is not a security sandbox. |
| main.py | Exposes `run(input, api_key)` for direct trusted-local use. |

## Features

- Graph-controlled fix-test-evaluate loop.
- Explicit evaluator-based retry decisions.
- Separation between bug analysis and validation execution.
- Structured workflow suited to debugging automation experiments.

## Example Usage

### Trusted local use

This project executes generated Python with the current process user's environment, filesystem, and network permissions. The shared runner and API therefore disable it by default and always disable it in production.

To opt in for trusted development only, set `GENAI_SYSTEMS_LAB_ENABLE_UNSAFE_AGENTS=true` while `APP_ENV` is not `prod`, then call:

```bash
curl -X POST http://127.0.0.1:8000/debugging-agent/run \
  -H "Content-Type: application/json" \
  -d '{"input": "Function crashes on empty input and should return an empty list"}'
```

## Evaluation

The evaluation route is subject to the same trusted-development opt-in.

```text
POST /eval/debugging-agent
```

Primary metrics: bug resolution rate, retry count, test pass rate, latency, and failure rate.
