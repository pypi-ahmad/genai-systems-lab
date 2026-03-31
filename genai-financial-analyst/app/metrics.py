import pandas as pd


def compute_metrics(df: pd.DataFrame, rolling_window: int = 3) -> dict:
    if df.empty:
        raise ValueError("DataFrame is empty")

    revenue = df["revenue"]
    expenses = df["expenses"]

    total_revenue = float(revenue.sum())
    total_expenses = float(expenses.sum())
    net_profit = total_revenue - total_expenses

    metrics = {
        "total_revenue": total_revenue,
        "total_expenses": total_expenses,
        "net_profit": net_profit,
        "profit_margin": round(net_profit / total_revenue * 100, 2) if total_revenue else 0.0,
        "average_revenue": round(float(revenue.mean()), 2),
        "average_expenses": round(float(expenses.mean()), 2),
        "min_revenue": float(revenue.min()),
        "max_revenue": float(revenue.max()),
        "min_expenses": float(expenses.min()),
        "max_expenses": float(expenses.max()),
        "num_periods": len(df),
    }

    # Period-over-period revenue growth rates
    if len(df) >= 2:
        shifted = revenue.shift(1)
        growth = ((revenue - shifted) / shifted * 100).dropna()
        metrics["revenue_growth_rates"] = [round(g, 2) for g in growth.tolist()]
    else:
        metrics["revenue_growth_rates"] = []

    # Rolling average revenue
    if len(df) >= rolling_window:
        rolling = revenue.rolling(window=rolling_window).mean().dropna()
        metrics["revenue_rolling_avg"] = [round(v, 2) for v in rolling.tolist()]
    else:
        metrics["revenue_rolling_avg"] = []

    return metrics