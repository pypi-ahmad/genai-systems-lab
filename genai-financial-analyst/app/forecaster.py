import numpy as np
import pandas as pd


def forecast(df: pd.DataFrame, periods: int = 3, window: int = 3) -> dict:
    if len(df) < 2:
        raise ValueError("Need at least 2 data points to forecast")

    results = {}
    for col in ["revenue", "expenses"]:
        values = df[col].dropna().values.astype(float)
        if len(values) < 2:
            continue

        # Linear trend
        x = np.arange(len(values))
        slope, intercept = np.polyfit(x, values, 1)

        predicted = [
            round(float(slope * (len(values) + i) + intercept), 2)
            for i in range(periods)
        ]

        # Rolling average forecast
        w = min(window, len(values))
        rolling_avg = round(float(np.mean(values[-w:])), 2)

        # Trend direction (tolerance for floating point noise)
        if abs(slope) < 1e-9:
            slope = 0.0
            direction = "flat"
        elif slope > 0:
            direction = "upward"
        else:
            direction = "downward"

        results[col] = {
            "trend_direction": direction,
            "slope_per_period": round(float(slope), 2),
            "linear_forecast": predicted,
            "rolling_avg_forecast": rolling_avg,
            "last_value": round(float(values[-1]), 2),
        }

    return results