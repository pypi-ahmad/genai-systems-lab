# Autonomous Browser Agent

## Overview

An AI-powered browser automation agent that observes a web page, plans the next action, executes browser interactions, and loops until the task is complete or the step budget is exhausted. The project focuses on goal-driven navigation rather than test scripting.

## System Flow

The agent repeatedly gathers page state, decides on the next browser action, executes it through Playwright, records the result, and continues until it reaches a completion or stop condition.

```text
Goal -> Perception -> Planner -> Action Executor -> Browser State Update -> Memory -> Next Step
```

## Architecture

The implementation separates page observation, action planning, browser control, and run memory so the observe-plan-act loop remains explicit and debuggable.

| Module | Responsibility |
|--------|----------------|
| app/perception.py | Builds text and optional vision-based page observations. |
| app/planner.py | Chooses the next structured browser action from the current state. |
| app/actions.py | Executes supported browser actions such as open, click, and type. |
| app/browser.py | Owns the Playwright browser lifecycle and page interactions. |
| app/agent.py | Runs the full step loop and stores execution history. |

## Features

- Goal-driven browser automation with structured action selection.
- Playwright-backed execution for reliable page interaction.
- Run memory to avoid blind repetition across steps.
- Optional screenshot-based page observation path.

## Example Usage

### Shared API

```bash
curl -X POST http://127.0.0.1:8000/browser-agent/run \
  -H "Content-Type: application/json" \
  -d '{"input": "Search for recent AI papers on arxiv"}'
```

## Evaluation

```text
POST /eval/browser-agent
```

Primary metrics: task completion accuracy, step count, latency per action cycle, and failure rate.
