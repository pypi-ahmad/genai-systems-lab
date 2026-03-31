# Architecture

## Overview

The AI Financial Analyst Agent is a pipeline system that ingests structured financial data, computes key performance indicators, applies LLM-based reasoning to interpret trends, and produces readable financial reports. An optional forecasting stage predicts future trends based on historical metrics.

Primary flow:

`CSV Data → Data Loader → Metrics Engine → Analyzer (LLM) → Reporter (LLM) → Financial Report`

Optional extension:

`Metrics Engine → Forecaster → Analyzer`

## Component Responsibilities

### Data Loader

- Loads CSV financial data from disk into a normalized internal format.
- Validates required columns and data types on ingestion.
- Handles missing values, duplicates, and basic data cleaning.
- Returns structured records (list of dicts or similar) ready for downstream computation.

### Metrics Engine

- Computes key financial KPIs from the loaded data.
- Standard metrics include: total revenue, period-over-period growth rate, moving averages, profit margins, and expense ratios.
- Accepts configurable metric definitions so new KPIs can be added without code changes.
- Returns a structured metrics dictionary with labeled values and their time periods.

### Analyzer (LLM)

- Receives computed metrics and interprets them in business context.
- Identifies trends, anomalies, risks, and opportunities from the numbers.
- Compares current-period performance against historical baselines.
- Produces structured analytical findings (key takeaways, risk flags, performance summary).

### Reporter (LLM)

- Takes analytical findings and formats them into a readable financial report.
- Organizes output into sections: executive summary, detailed metrics, trend analysis, and recommendations.
- Generates clear, professional language suitable for stakeholder review.

### Forecaster (Optional)

- Predicts future values for key metrics based on historical data.
- Uses simple statistical methods (moving averages, linear regression) or LLM-assisted projection.
- Returns forecast values with time horizons and confidence indicators.
- Feeds predictions into the Analyzer for interpretation alongside historical metrics.

## System Flow

### 1. Data Ingestion

The Data Loader reads one or more CSV files, validates the schema, cleans the data, and returns normalized records.

### 2. Metric Computation

The Metrics Engine processes the loaded data and computes all configured KPIs. Results are returned as a structured dictionary keyed by metric name.

### 3. Forecasting (Optional)

If enabled, the Forecaster takes historical metric values and produces forward-looking predictions. These are appended to the metrics payload before analysis.

### 4. Analysis

The Analyzer receives the full metrics payload (historical and optionally forecasted) and uses LLM reasoning to interpret the numbers. It produces structured findings: key trends, risk flags, and performance observations.

### 5. Report Generation

The Reporter takes the analytical findings and generates a formatted financial report. The output is a complete, human-readable document organized by section.

## Model Usage

### `gemini-3.1-pro-preview`

Use for reasoning-heavy interpretation of financial data.

Recommended responsibilities:

- Analyzer: interpreting metrics, identifying trends and anomalies, assessing risk
- Forecaster: LLM-assisted projection reasoning (if applicable)

### `gemini-3-flash-preview`

Use for structured text generation and formatting.

Recommended responsibilities:

- Reporter: generating the final financial report
- Any lightweight summarization of intermediate results

This allocation keeps deep analytical reasoning on the stronger model and uses the faster model for report synthesis and formatting.

## Production-Oriented Design Notes

- Data Loader should fail fast on schema violations with clear error messages.
- Metrics Engine should be stateless — given the same input data, it must produce identical output.
- Analyzer prompts should include the raw metric values and their labels so the LLM can ground its reasoning in actual numbers.
- Reporter output should follow a consistent template so reports are comparable across runs.
- All stages should emit structured artifacts (dicts/JSON) so each downstream stage can operate deterministically.
- Logging should capture input file paths, computed metrics, and LLM call metadata for auditability.
- Metric definitions and report templates should be configurable without code changes.

## High-Level Architecture Summary

The system is organized as a linear pipeline with an optional forecasting branch. The Data Loader handles ingestion and validation, the Metrics Engine computes KPIs, the Analyzer applies LLM reasoning to interpret the numbers, and the Reporter produces the final document. The Forecaster optionally extends the pipeline with forward-looking predictions. Each component has a single responsibility, operates on structured inputs and outputs, and can be tested and upgraded independently.