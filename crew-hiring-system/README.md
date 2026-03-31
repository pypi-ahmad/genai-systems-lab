# Hiring Decision Crew

## Overview

A CrewAI hiring workflow that evaluates candidates through screening, technical assessment, behavioral assessment, decision synthesis, and bias review. The project is intended for structured, multi-perspective hiring analysis.

## System Flow

A candidate profile moves through successive evaluators, each adding a focused assessment before a hiring manager synthesizes the final recommendation and a bias auditor checks for review quality risks.

```text
Resume -> Screener -> Technical Interviewer -> Behavioral Interviewer -> Hiring Manager -> Bias Auditor -> Decision
```

## Architecture

The codebase uses specialized CrewAI roles with structured task outputs so each decision stage feeds a downstream evaluator without requiring custom graph logic.

| Module | Responsibility |
|--------|----------------|
| agents.py | Defines the screening, interview, decision, and bias-audit agents. |
| tasks.py | Defines the ordered hiring evaluation tasks and schemas. |
| crew.py | Builds the CrewAI workflow used for candidate review. |
| main.py | Provides the runnable entrypoint and result formatting. |

## Features

- Five-stage candidate review pipeline with explicit role boundaries.
- Separate technical and behavioral evaluation paths.
- Bias audit stage before final recommendation output.
- Structured handoffs that make the review process easier to trace.

## Example Usage

### Shared API

```bash
curl -X POST http://127.0.0.1:8000/hiring-crew/run \
  -H "Content-Type: application/json" \
  -d '{"input": "Senior backend engineer with Python, FastAPI, and distributed systems experience"}'
```

## Evaluation

```text
POST /eval/hiring-crew
```

Primary metrics: screening quality, evaluation consistency, bias detection rate, latency, and failure rate.
