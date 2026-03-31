# Multi-Agent Research System

## Overview

A LangGraph-based research workflow that decomposes a query into tasks, gathers findings, critiques the draft, rewrites when needed, and produces multi-format outputs with quality metrics. It is the flagship project in the repository for graph-based iterative reasoning.

## System Flow

The workflow plans a research agenda, generates findings for each task, critiques the output, loops through revisions when necessary, writes the final report, and optionally formats it for additional channels such as blog posts or social content.

```text
Query -> Planner -> Researcher -> Critic -> Writer -> Editor -> Originality Check -> Formatter -> Output
```

## Architecture

The implementation is organized around a LangGraph state machine with instrumented nodes, explicit revision loops, quality scoring, and service layers for both API and UI access.

| Module | Responsibility |
|--------|----------------|
| app/graph.py | Builds the LangGraph workflow and conditional routing logic. |
| app/nodes/ | Contains planner, researcher, critic, writer, editor, and formatter nodes. |
| app/service.py | Runs the workflow and returns structured outputs with metrics. |
| app/metrics.py | Computes quality, originality, and format coverage metrics. |
| app/api.py | Exposes a dedicated FastAPI service for research runs. |

## Features

- LangGraph workflow with explicit revision and quality gates.
- Per-node instrumentation and execution trace reporting.
- Originality and editorial checks before final output formatting.
- Multi-format output generation alongside structured evaluation metrics.

## Example Usage

### Shared API

```bash
curl -X POST http://127.0.0.1:8000/multi-agent-research/run \
  -H "Content-Type: application/json" \
  -d '{"input": "Compare transformer architectures for code generation"}'
```

## Evaluation

```text
POST /eval/multi-agent-research
```

Primary metrics: quality score, originality score, format coverage, failure rate, and per-node latency.
