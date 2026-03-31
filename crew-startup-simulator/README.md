# Startup Simulator

## Overview

A CrewAI startup simulation that asks multiple functional leaders to propose, select, and refine a business idea before reviewing the resulting product, architecture, and execution plan. It is designed to model cross-functional startup decision-making.

## System Flow

The workflow begins with independent proposals from product, engineering, and leadership perspectives, selects a direction, then expands that decision into product, architecture, execution, and peer-review outputs.

```text
Idea Prompt -> PM / CTO / Engineer Proposals -> CEO Selection -> Product Spec -> Architecture -> Execution Plan -> Peer Reviews
```

## Architecture

The project uses a phased CrewAI pipeline with proposal, selection, execution, and review stages so each artifact reflects a distinct role and critique cycle.

| Module | Responsibility |
|--------|----------------|
| agents.py | Defines the CEO, product, engineering, and technical leadership roles. |
| tasks.py | Defines the proposal, selection, planning, and review tasks. |
| crew.py | Builds the full multi-phase startup simulation crew. |
| main.py | Runs the simulation and prints each staged result. |

## Features

- Independent proposal generation from multiple startup roles.
- Decision synthesis before downstream planning begins.
- Cross-functional peer review of generated artifacts.
- Useful for comparing how different role perspectives shape execution.

## Example Usage

### Shared API

```bash
curl -X POST http://127.0.0.1:8000/startup-simulator/run \
  -H "Content-Type: application/json" \
  -d '{"input": "Create a startup concept for AI-assisted procurement operations"}'
```

## Evaluation

```text
POST /eval/startup-simulator
```

Primary metrics: proposal quality, decision coherence, review coverage, latency, and failure rate.
