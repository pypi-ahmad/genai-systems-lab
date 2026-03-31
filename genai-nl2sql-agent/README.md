# NL2SQL Agent

## Overview

A natural-language-to-SQL workflow that translates user questions into safe DuckDB queries, validates the generated SQL, executes it, and summarizes the result. The project focuses on safe read-only analytics over a known schema.

## System Flow

A user question is grounded against the live schema, converted into SQL, validated for safety and shape, executed against DuckDB, and summarized into a concise answer from the returned rows.

```text
Natural Language Query -> Schema Loader -> SQL Generator -> Validator -> DuckDB Executor -> Result Summarizer
```

## Architecture

The implementation isolates schema loading, SQL generation, validation, execution, and summarization so the LLM output is checked before any query runs.

| Module | Responsibility |
|--------|----------------|
| app/schema.py | Builds the DuckDB schema description and sample in-memory database. |
| app/sql_generator.py | Generates DuckDB-compatible read-only SQL from the user request. |
| app/validator.py | Rejects unsafe or malformed SQL before execution. |
| app/executor.py | Executes validated SQL against DuckDB. |
| app/agent.py | Orchestrates retries, execution, and result summarization. |

## Features

- Schema-grounded SQL generation from natural language questions.
- Read-only validation to block mutating SQL statements.
- DuckDB-backed execution with structured results.
- Natural-language result summary generated from returned rows only.

## Example Usage

### Shared API

```bash
curl -X POST http://127.0.0.1:8000/nl2sql-agent/run \
  -H "Content-Type: application/json" \
  -d '{"input": "top customers by revenue"}'
```

## Evaluation

```text
POST /eval/nl2sql-agent
```

Primary metrics: SQL correctness, execution success rate, result accuracy, latency, and failure rate.
