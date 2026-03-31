# Support Agent

## Overview

A LangGraph support workflow that classifies inbound requests, retrieves relevant context, generates a response, and decides whether the request should be escalated. The project focuses on controlled support routing rather than generic chat assistance.

## System Flow

A support request is classified, enriched with retrieved context, answered by a responder node, and checked by an evaluator that can escalate low-confidence cases instead of forcing an answer.

```text
Support Request -> Classifier -> Retriever -> Responder -> Evaluator -> Resolved Response or Escalation
```

## Architecture

The graph keeps request classification, retrieval, response generation, and escalation logic in distinct steps so support-specific routing remains explicit.

| Module | Responsibility |
|--------|----------------|
| graph.py | Defines the support workflow and escalation routing. |
| state.py | Tracks request details, retrieved context, and confidence state. |
| nodes/ | Contains classifier, retriever, responder, and evaluator nodes. |
| knowledge_base.py | Provides the support content used for retrieval. |
| main.py | Exposes `run(input, api_key)` for the shared runtime and API platform. |

## Features

- Graph-based support handling with explicit escalation paths.
- Retrieval-augmented response generation for grounded answers.
- Evaluator gate to avoid low-confidence responses.
- Useful for support automation and workflow routing experiments.

## Example Usage

### Shared API

```bash
curl -X POST http://127.0.0.1:8000/support-agent/run \
  -H "Content-Type: application/json" \
  -d '{"input": "Customer cannot access the billing dashboard after password reset"}'
```

## Evaluation

```text
POST /eval/support-agent
```

Primary metrics: response relevance, escalation accuracy, resolution rate, latency, and failure rate.
