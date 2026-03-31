import os

import pandas as pd

SUPPORTED_FORMATS = ["csv", "json", "parquet"]

SAMPLE_DATA = [
    {"date": "2024-01-01", "revenue": 1200, "region": "North"},
    {"date": "2024-01-01", "revenue": 950, "region": "South"},
    {"date": "2024-02-01", "revenue": 1350, "region": "North"},
    {"date": "2024-02-01", "revenue": 1100, "region": "South"},
    {"date": "2024-03-01", "revenue": 1500, "region": "North"},
    {"date": "2024-03-01", "revenue": 980, "region": "South"},
    {"date": "2024-04-01", "revenue": 1600, "region": "North"},
    {"date": "2024-04-01", "revenue": 1250, "region": "South"},
]


def load_data(file_path: str | None = None) -> pd.DataFrame:
    """Load a dataset from file or return built-in sample data."""
    if file_path is None:
        return _load_sample()

    ext = os.path.splitext(file_path)[1].lower().lstrip(".")
    if ext not in SUPPORTED_FORMATS:
        raise ValueError(
            f"Unsupported format: .{ext}  (supported: {', '.join(SUPPORTED_FORMATS)})"
        )

    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    if ext == "csv":
        df = pd.read_csv(file_path)
    elif ext == "json":
        df = pd.read_json(file_path)
    else:
        df = pd.read_parquet(file_path)

    df.columns = df.columns.str.strip().str.lower()
    return df


def get_metadata(df: pd.DataFrame) -> dict:
    """Return column names, dtypes, shape, and a small sample (max 3 rows)."""
    return {
        "columns": df.columns.tolist(),
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
        "shape": list(df.shape),
        "sample": df.head(3).to_dict(orient="records"),
    }


def _load_sample() -> pd.DataFrame:
    df = pd.DataFrame(SAMPLE_DATA)
    df["date"] = pd.to_datetime(df["date"])
    return df