# Financial Analyst Agent

## Overview

An AI-powered financial analysis pipeline that transforms CSV data into metrics, trend analysis, optional forecasts, and a structured report. The project combines deterministic metric computation with LLM-backed interpretation and reporting.

## System Flow

The workflow loads a financial dataset, computes core metrics, optionally forecasts future periods, analyzes trends and anomalies, and formats the output into a concise stakeholder-ready report.

```text
CSV Data -> Data Loader -> Metrics Engine -> Analyzer -> Reporter -> Financial Report
```

## Architecture

The implementation keeps numeric computation, forecasting, interpretation, and report generation in separate modules so financial logic stays inspectable and testable.

| Module | Responsibility |
|--------|----------------|
| app/data_loader.py | Loads and cleans CSV financial data. |
| app/metrics.py | Computes KPIs such as revenue, margin, and growth rates. |
| app/forecaster.py | Produces optional forward-looking metric forecasts. |
| app/analyzer.py | Interprets trends and anomalies using LLM reasoning. |
| app/reporter.py | Formats a concise executive-style financial report. |

## Features

- Deterministic KPI computation from structured CSV inputs.
- Optional forecasting for forward-looking analysis.
- LLM-assisted trend and anomaly interpretation grounded in metrics.
- Report generation optimized for stakeholder summaries.

## Example Usage

### Shared API

```bash
curl -X POST http://127.0.0.1:8000/financial-analyst-agent/run \
  -H "Content-Type: application/json" \
  -d '{"input": "data/fintech_saas_financials.csv --forecast 3"}'
```

## Evaluation

```text
POST /eval/financial-analyst-agent
```

Primary metrics: metric computation accuracy, analysis relevance, forecast quality, latency, and failure rate.
