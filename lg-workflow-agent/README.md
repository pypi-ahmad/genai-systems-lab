# Workflow Agent

## Overview

A LangGraph workflow runner that plans a multi-step task, executes it with checkpoints, validates intermediate progress, and supports controlled continuation across steps. The project focuses on durable stateful execution rather than a single-pass response.

## System Flow

A task request is converted into steps, executed through a graph, validated at each stage, checkpointed for recovery, and resumed or completed depending on the state of execution.

```text
Task Request -> Planner -> Executor -> Validator -> Checkpoint -> Next Step or Resume -> Final Output
```

## Architecture

The implementation centers on a stateful LangGraph workflow with checkpointing and resume behavior so longer-running tasks can be inspected and recovered instead of rerun from scratch.

| Module | Responsibility |
|--------|----------------|
| graph.py | Defines the state machine and checkpoint-aware routing. |
| state.py | Stores workflow steps, progress, and recovery data. |
| nodes/ | Contains planner, executor, validator, and checkpoint nodes. |
| checkpoint.py | Handles persistence and resume support for workflow state. |
| main.py | Exposes `run(input, api_key)` for the shared runtime and API platform. |

## Features

- Checkpoint-aware LangGraph execution for multi-step tasks.
- Validation between steps instead of a single final check.
- Resume support for interrupted or staged workflow runs.
- Clear separation between planning, execution, and state persistence.

## Example Usage

### Shared API

```bash
curl -X POST http://127.0.0.1:8000/workflow-agent/run \
  -H "Content-Type: application/json" \
  -d '{"input": "Run a multi-step onboarding workflow for a new enterprise customer"}'
```

## Evaluation

```text
POST /eval/workflow-agent
```

Primary metrics: step completion rate, checkpoint recovery success, latency, and failure rate.
