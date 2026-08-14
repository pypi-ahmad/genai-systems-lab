# Architecture

## Overview

The system accepts a natural language question, converts it into safe read-only SQL, executes the query on DuckDB, and returns both raw results and an LLM-generated summary. The design separates generation, validation, execution, and summarization so each step can be controlled, audited, and retried independently.

## Core Components

### LLM Interface (Gemini)

Provides a single integration layer for model calls, prompt templates, request metadata, retries, and response logging. It routes tasks to the appropriate model:

- `gemini-3.7-flash` for reasoning-heavy SQL generation
- `gemini-3.5-flash-lite` for result summarization

### Schema Loader

Loads database metadata required for prompt grounding and validation. This includes table names, column names, types, and optional semantic hints. The schema loader should expose a normalized schema representation that is shared by the generator and validator.

### SQL Generator

Transforms the user’s natural language request into SQL using the loaded schema and structured prompting. Output should be constrained to a single DuckDB-compatible read-only statement.

### SQL Validator

Checks generated SQL before execution. Validation should enforce:

- Exactly one DuckDB-parsed `SELECT` is allowed.
- Base tables are limited to `customers` and `orders`; table functions, CTEs, nested queries, external catalogs, and unknown functions are rejected.
- Expression and aggregate functions use an explicit allowlist, and DuckDB binds referenced columns against the live schema.
- The executor repeats validation, caps returned rows, and uses a connection with external access and extension loading disabled.

### Query Executor

Executes validated SQL against DuckDB and returns structured results, execution metadata, and execution errors. This layer should isolate database access and provide deterministic error handling.

### Result Summarizer

Takes the user’s original question and the query result set, then produces a concise natural language answer using `gemini-3.5-flash-lite`. The summary should be grounded only in returned data and should not invent unsupported conclusions.

## End-to-End Flow

`NL Query -> SQL -> Validation -> Execution -> Summary`

1. The user submits a natural language query.
2. The schema loader provides the current database schema context.
3. The SQL generator uses `gemini-3.7-flash` to produce DuckDB SQL.
4. The SQL validator checks syntax class, schema usage, and safety rules.
5. If valid, the query executor runs the SQL on DuckDB.
6. The result summarizer uses `gemini-3.5-flash-lite` to convert result rows into a user-facing summary.
7. The system returns both structured results and the summary.

## Safety and Reliability

### Read-Only Enforcement

The validator uses DuckDB's serialized AST rather than SQL text patterns. Unknown statement, table, expression, and function shapes fail closed. The executor revalidates so direct callers cannot bypass the orchestration-layer check.

### Retry Mechanism

If SQL generation or execution fails, the system should perform a bounded retry loop:

1. Capture the validation or execution error.
2. Feed the error and schema context back into the SQL generator.
3. Regenerate SQL with explicit correction guidance.
4. Re-validate before any new execution attempt.

Retries should be limited to avoid loops and to preserve predictable latency.

### Observability

Each stage should emit structured logs for prompt input, generated SQL, validation decisions, execution time, row counts, errors, and retry attempts. This is required for debugging, auditability, and safe production operations.

## Production Notes

The architecture is intentionally modular so model changes, validation hardening, and executor upgrades can happen without coupling all layers together. In production, the validator and executor should be treated as enforcement boundaries, not as optional helpers around the LLM.
