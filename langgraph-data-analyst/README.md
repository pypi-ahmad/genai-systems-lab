# LangGraph Data Analyst

## Overview

A LangGraph-based data analysis agent that turns natural-language questions over CSV or Excel files into structured Markdown reports. The workflow plans an analysis strategy, generates and executes Python-based dataframe operations in a sandbox, validates the result, and returns findings, anomalies, and recommendations through a FastAPI endpoint.

## System Flow

The workflow receives a dataset path and a natural-language question, builds an analysis plan, generates and executes Python code in a sandboxed subprocess, validates the output through bounded retries, and produces a structured Markdown report with findings, anomalies, and recommendations.

```text
Dataset + Query -> Planner -> Executor -> Validator -> [retry or pass] -> Reporter -> Markdown Report
```

## Architecture

The implementation uses a LangGraph state machine to coordinate a multi-agent data analysis pipeline. The Planner breaks down the user query, the Executor runs sandboxed Python code against the dataset, the Validator checks the results and triggers retries when necessary, and the Reporter formats the final output. The entire workflow is exposed via a FastAPI endpoint.

| Module | Responsibility |
|--------|----------------|
| src/agents/planner.py | Produces a structured analysis plan from the user question. |
| src/agents/executor.py | Generates and runs analysis code against the dataset. |
| src/agents/validator.py | Checks whether the execution result answers the question and triggers bounded retries. |
| src/agents/reporter.py | Writes the final report with findings, anomalies, and recommendations. |
| src/graph/workflow.py | Wires the LangGraph state machine and retry loop. |
| src/tools/python_executor.py | Runs generated code in a subprocess sandbox. |
| src/tools/dataframe_tools.py | Loads and profiles CSV or Excel inputs. |
| src/api/app.py | Exposes the workflow through FastAPI. |

## Features

- Natural-language data analysis over CSV and Excel files.
- LangGraph orchestration with planner, executor, validator, and reporter stages.
- Sandboxed Python execution for dataframe operations and chart generation.
- Validation-driven retry loop to recover from failed or incomplete analyses.
- FastAPI interface for programmatic use in local or shared environments.

## Example Usage

### Shared API

```bash
curl -X POST http://127.0.0.1:8000/data-analyst/run \
  -H "Content-Type: application/json" \
  -d '{"input": "Show revenue breakdown by region and identify anomalies", "file_path": "data/sample.csv"}'
```

## Evaluation

```text
POST /eval/data-analyst
```

Primary metrics: execution success rate, report completeness, retry behavior, result correctness, latency, and failure rate.
