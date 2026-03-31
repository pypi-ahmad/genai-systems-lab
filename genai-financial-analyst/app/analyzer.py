import json

import pandas as pd

from shared.llm.gemini import generate_text


MODEL = "gemini-3.1-pro-preview"
SAMPLE_ROWS = 5


def analyze_metrics(metrics: dict, df: pd.DataFrame) -> str:
    metrics_block = json.dumps(metrics, indent=2, default=str)

    sample = df.head(SAMPLE_ROWS).to_string(index=False)

    prompt = f"""You are a senior financial analyst. You are given computed financial metrics and a sample of the underlying data.

## Computed Metrics
{metrics_block}

## Sample Data (first {min(SAMPLE_ROWS, len(df))} of {len(df)} rows)
{sample}

Analyze this financial data and provide:

1. **Trends**: Identify clear directional patterns in revenue, expenses, and profit over time. Reference specific numbers and periods.
2. **Anomalies**: Flag any unusual spikes, drops, or inconsistencies in the data. Explain why they stand out.
3. **Insights**: Provide actionable business insights based on the metrics. Be specific — cite the metric values that support each insight.

Rules:
- Ground every observation in the actual numbers provided.
- Do NOT make up data or assume values not present.
- Be concise and direct. No filler language.
- Structure your response with clear headings for Trends, Anomalies, and Insights."""

    return generate_text(prompt, MODEL)