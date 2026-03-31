# Tasks

## Load Financial Dataset

- Create `load_csv(filepath)` in `app/data_loader.py` that reads a CSV file and returns a list of row dicts.
- Validate that required columns exist on load (e.g. `date`, `revenue`, `expenses`).
- Strip whitespace from column headers and string values.
- Skip rows where all numeric fields are missing.
- Raise `ValueError` with a clear message if the file path is invalid or the CSV is empty after cleaning.
- Sort rows by date in ascending order before returning.

## Compute Metrics

- Create `compute_metrics(rows)` in `app/metrics.py` that accepts cleaned row dicts and returns a metrics dictionary.
- Compute total revenue and total expenses across all rows.
- Compute net profit (revenue minus expenses).
- Compute period-over-period revenue growth rate as a list of percentages.
- Compute a rolling average for revenue over a configurable window size (default 3).
- Compute profit margin percentage (net profit / total revenue).
- Return all metrics as a flat dictionary with descriptive string keys.

## Analyze Trends

- Create `analyze(metrics)` in `app/analyzer.py` that sends metrics to the LLM for interpretation.
- Build a prompt that includes all metric values with their labels.
- Instruct the LLM to identify key trends, anomalies, risks, and opportunities.
- Use `gemini-3.1-pro-preview` for the analysis call.
- Return the LLM response as a structured findings string.

## Generate Report

- Create `generate_report(findings, metrics)` in `app/reporter.py` that produces a formatted financial report.
- Build a prompt that includes the analytical findings and raw metric values.
- Instruct the LLM to organize output into sections: executive summary, key metrics, trend analysis, and recommendations.
- Use `gemini-3-flash-preview` for the report generation call.
- Return the report as a plain text string.

## Add Forecasting

- Create `forecast(rows, metric_name, periods)` in `app/forecaster.py` that predicts future values for a given metric.
- Implement a simple linear regression over the historical values of the specified metric.
- Return a list of dicts with `period` and `predicted_value` keys.
- Handle edge cases: fewer than 2 data points should raise `ValueError`.
- Optionally support a moving-average fallback when linear regression is not suitable.

