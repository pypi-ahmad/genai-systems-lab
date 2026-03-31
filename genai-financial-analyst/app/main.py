from __future__ import annotations

from app.data_loader import load_data
from app.metrics import compute_metrics
from app.analyzer import analyze_metrics
from app.reporter import generate_report
from app.forecaster import forecast
from shared.api.step_events import emit_step
from shared.config import set_byok_api_key, reset_byok_api_key


def run(input: str, api_key: str) -> dict:
    """Run financial analysis and return structured output.

    Input format: ``<csv_path>`` or ``<csv_path> --forecast <periods>``.
    If input contains no path-like token, it is treated as an analysis query
    against the default data directory.
    """
    token = set_byok_api_key(api_key)
    try:
        parts = input.split()
        file_path = parts[0] if parts else None
        forecast_periods = 0
        if "--forecast" in parts:
            idx = parts.index("--forecast")
            if idx + 1 < len(parts) and parts[idx + 1].isdigit():
                forecast_periods = int(parts[idx + 1])

        emit_step("metrics", "running")
        df = load_data(file_path)
        metrics = compute_metrics(df)
        emit_step("metrics", "done")

        forecast_result = None
        if forecast_periods > 0:
            emit_step("forecaster", "running")
            forecast_result = forecast(df, periods=forecast_periods)
            emit_step("forecaster", "done")

        emit_step("trends", "running")
        analysis = analyze_metrics(metrics, df)
        emit_step("trends", "done")

        emit_step("writer", "running")
        report = generate_report(analysis)
        emit_step("writer", "done")

        result: dict = {"metrics": metrics, "analysis": analysis, "report": report}
        if forecast_result is not None:
            result["forecast"] = forecast_result
        return result
    finally:
        reset_byok_api_key(token)