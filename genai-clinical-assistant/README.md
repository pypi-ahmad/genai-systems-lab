# Clinical Decision Support System

## Overview

A clinical reasoning pipeline that extracts patient details, retrieves relevant conditions from a knowledge base, applies LLM reasoning, assigns deterministic confidence scores, and formats a clinical summary. It is intended as a structured decision-support prototype, not a diagnostic system.

## System Flow

The system takes patient input, converts it into structured symptoms and demographics, retrieves candidate conditions, evaluates them with a reasoning model, and returns a formatted report with confidence labels.

```text
Patient Input -> Extractor -> Retriever -> Reasoner -> Risk Evaluator -> Formatter -> Clinical Report
```

## Architecture

The codebase separates extraction, retrieval, reasoning, scoring, and presentation so both deterministic logic and LLM-backed analysis remain visible in the final result.

| Module | Responsibility |
|--------|----------------|
| app/extractor.py | Extracts symptoms and explicit patient details from free text. |
| app/retriever.py | Ranks candidate conditions from the local clinical knowledge base. |
| app/reasoner.py | Generates condition-level reasoning from patient context and retrieved candidates. |
| app/risk_evaluator.py | Assigns deterministic confidence scores and labels. |
| app/formatter.py | Formats the final clinical summary for review. |

## Features

- Structured patient information extraction from free-text descriptions.
- Knowledge-base-grounded condition retrieval.
- LLM reasoning combined with deterministic confidence scoring.
- Formatted output designed for review-oriented workflows.

## Example Usage

### Shared API

```bash
curl -X POST http://127.0.0.1:8000/clinical-decision-support/run \
  -H "Content-Type: application/json" \
  -d '{"input": "45-year-old male presenting with chest pain and shortness of breath"}'
```

## Evaluation

```text
POST /eval/clinical-decision-support
```

Primary metrics: diagnostic relevance, retrieval quality, confidence calibration, latency, and failure rate.
