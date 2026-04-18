# Research Graph

## Overview

A LangGraph-based research workflow that decomposes a question into a short plan, generates focused findings, critiques their quality, and writes a concise research brief.

## System Flow

```text
Query -> Planner -> Researcher -> Critic -> Writer -> Final Report
```

## Features

- Graph-backed execution using LangGraph.
- Four explicit research stages with step-level instrumentation.
- Standardized `run(input, api_key)` entrypoint for the shared platform runner.

## Example Usage

### Shared API

```bash
curl -X POST http://127.0.0.1:8000/research-graph/run \
  -H "Authorization: Bearer <jwt>" \
  -H "X-API-Key: <your_api_key_here>" \
  -H "Content-Type: application/json" \
  -d '{"input": "Research recent approaches to agent memory systems"}'
```
