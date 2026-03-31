# Tasks

## 1. Setup Database (DuckDB)

- Create a local DuckDB database file for the project.
- Add a small database initialization script that opens the DuckDB connection.
- Define a repeatable project path convention for database assets.
- Add a task to reset or recreate the database for local development.

## 2. Create Sample Dataset

- Define a minimal sample domain for testing NL-to-SQL flows.
- Create one CSV or SQL seed file per sample table.
- Add a loader script that imports the sample data into DuckDB.
- Verify that seeded tables contain rows after initialization.

## 3. Implement Schema Extraction

- Add a module that lists all tables from DuckDB.
- Add a function that extracts columns and types for each table.
- Normalize the extracted schema into a single structured format.
- Add a formatter that converts the schema into prompt-friendly text.

## 4. Build LLM Wrapper

- Create a Gemini client wrapper using shared configuration.
- Add a method for SQL-generation requests.
- Add a method for result-summarization requests.
- Add structured logging for model name, latency, and errors.

## 5. Implement SQL Generation

- Define the prompt template for converting natural language to DuckDB SQL.
- Inject schema context into the SQL-generation prompt.
- Constrain output to a single SQL statement.
- Add a parser that extracts only the SQL text from the LLM response.

## 6. Implement SQL Validation

- Add a validator that rejects empty or malformed SQL.
- Block non-read-only statements such as `DROP`, `DELETE`, and `UPDATE`.
- Reject multi-statement SQL.
- Verify that referenced tables and columns exist in the extracted schema.
- Add a DuckDB-compatibility validation step before execution.

## 7. Implement Retry Mechanism

- Define a standard error payload for validation and execution failures.
- Add a retry loop for SQL generation failures.
- Feed validation or execution errors back into the next generation attempt.
- Stop retries after a fixed maximum number of attempts.
- Record retry count and final failure reason in logs.

## 8. Execute Queries

- Add a query executor that runs validated SQL against DuckDB.
- Return rows in a structured format suitable for downstream summarization.
- Capture row count and execution timing metadata.
- Handle database errors without exposing raw internals to the user.

## 9. Summarize Results

- Define the summarization prompt using the original question and query results.
- Call `gemini-3-flash-preview` for result summarization.
- Ensure summaries remain grounded in the returned dataset.
- Return both raw results and the generated natural language summary.

