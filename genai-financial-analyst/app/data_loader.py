import os

import pandas as pd


REQUIRED_COLUMNS = {"date", "revenue", "expenses"}


def load_data(file_path: str) -> pd.DataFrame:
    if not os.path.isfile(file_path):
        raise ValueError(f"File not found: {file_path}")

    df = pd.read_csv(file_path)

    # Strip whitespace from column headers
    df.columns = df.columns.str.strip().str.lower()

    # Validate required columns
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}")

    # Strip whitespace from string values
    str_cols = df.select_dtypes(include="object").columns
    df[str_cols] = df[str_cols].apply(lambda col: col.str.strip())

    # Coerce numeric columns
    for col in ["revenue", "expenses"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Drop rows where all numeric fields are missing
    numeric_cols = df.select_dtypes(include="number").columns
    df = df.dropna(subset=numeric_cols, how="all")

    if df.empty:
        raise ValueError("No valid data rows after cleaning")

    # Parse and sort by date
    df["date"] = pd.to_datetime(df["date"], format="mixed", dayfirst=False)
    df = df.sort_values("date").reset_index(drop=True)

    return df