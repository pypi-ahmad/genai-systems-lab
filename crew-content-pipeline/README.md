# Content Pipeline

## Overview

A CrewAI content production workflow that moves a topic through research, drafting, editing, and SEO optimization. The project is designed for structured marketing content generation with clear stage-by-stage handoffs between specialized agents.

## System Flow

The system starts from a content brief, gathers source material, drafts the article, refines the copy, and applies SEO-focused improvements before returning the final asset.

```text
Topic -> Researcher -> Writer -> Editor -> SEO Specialist -> Final Content
```

## Architecture

The implementation is organized around CrewAI agents and tasks, with a thin orchestration layer that assembles the sequential crew and exposes a runnable entrypoint.

| Module | Responsibility |
|--------|----------------|
| agents.py | Defines the researcher, writer, editor, and SEO specialist roles. |
| tasks.py | Defines the ordered task chain and expected outputs for each stage. |
| crew.py | Assembles the sequential CrewAI pipeline. |
| main.py | Exposes `run(input, api_key)` for the shared runtime and API platform. |

## Features

- Four-stage content workflow with explicit role separation.
- Sequential handoffs that preserve context between agents.
- Editorial and SEO review before final output.
- Structured pipeline suitable for repeatable content generation.

## Example Usage

### Shared API

```bash
curl -X POST http://127.0.0.1:8000/content-pipeline/run \
  -H "Content-Type: application/json" \
  -d '{"input": "Guide to building retrieval-augmented generation systems"}'
```

## Evaluation

```text
POST /eval/content-pipeline
```

Primary metrics: content quality, SEO alignment, stage completion, latency, and failure rate.
