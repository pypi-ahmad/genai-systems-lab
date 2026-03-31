# Product Launch Crew

## Overview

A CrewAI launch-planning workflow that coordinates research, positioning, messaging, channel planning, and launch execution recommendations. The goal is a cohesive go-to-market plan rather than isolated marketing artifacts.

## System Flow

A product brief moves through market understanding, positioning, campaign planning, and launch sequencing so the final output combines strategy, messaging, and execution steps in one plan.

```text
Product Brief -> Market Research -> Positioning -> Messaging -> Channel Plan -> Launch Plan
```

## Architecture

The workflow is implemented as a sequential CrewAI crew with role-specific tasks that progressively refine the launch strategy from discovery through execution planning.

| Module | Responsibility |
|--------|----------------|
| agents.py | Defines the launch strategy, research, messaging, and campaign agents. |
| tasks.py | Defines the staged launch-planning tasks and deliverables. |
| crew.py | Builds the product launch crew and execution order. |
| main.py | Exposes `run(input, api_key)` for the shared runtime and API platform. |

## Features

- Sequential launch-planning workflow with clear role ownership.
- Combines positioning, messaging, and channel planning.
- Produces a single integrated go-to-market recommendation.
- Designed for repeatable planning from a compact product brief.

## Example Usage

### Shared API

```bash
curl -X POST http://127.0.0.1:8000/product-launch-crew/run \
  -H "Content-Type: application/json" \
  -d '{"input": "Launch a workflow automation product for mid-market operations teams"}'
```

## Evaluation

```text
POST /eval/product-launch-crew
```

Primary metrics: plan completeness, messaging quality, launch coherence, latency, and failure rate.
