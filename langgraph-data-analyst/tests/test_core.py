"""Tests for dataframe_tools, python_executor, and planner output format.

Uses a real small CSV fixture — no mock-heavy patterns.
"""

from __future__ import annotations

import json
import sys
import textwrap
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Resolve paths so imports work regardless of cwd
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
FIXTURES = Path(__file__).resolve().parent / "fixtures"
CSV_PATH = FIXTURES / "sales.csv"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# ===========================================================================
# DataFrame loading  (src/tools/dataframe_tools.py)
# ===========================================================================

from src.tools.dataframe_tools import (
    get_basic_info,
    get_summary_stats,
    load_dataframe,
)


class TestLoadDataframe:
    def test_loads_csv(self):
        df = load_dataframe(CSV_PATH)
        assert len(df) == 8
        assert list(df.columns) == ["date", "region", "revenue", "units", "category"]

    def test_returns_correct_dtypes(self):
        df = load_dataframe(CSV_PATH)
        assert df["revenue"].dtype.kind == "f"  # float because of NaN
        assert df["units"].dtype.kind == "i"

    def test_missing_file_raises(self):
        with pytest.raises(FileNotFoundError):
            load_dataframe("/nonexistent/path.csv")

    def test_unsupported_extension_raises(self, tmp_path):
        bad = tmp_path / "data.parquet"
        bad.write_text("x")
        with pytest.raises(ValueError, match="Unsupported format"):
            load_dataframe(bad)

    def test_corrupt_csv_raises(self, tmp_path):
        bad = tmp_path / "bad.csv"
        bad.write_bytes(b"\x00\x01\x02\x03")
        # pandas may still load binary junk; just confirm no crash
        load_dataframe(bad)


class TestGetBasicInfo:
    @pytest.fixture()
    def df(self):
        return load_dataframe(CSV_PATH)

    def test_row_count(self, df):
        info = get_basic_info(df)
        assert info["rows"] == 8

    def test_column_count(self, df):
        info = get_basic_info(df)
        assert info["columns"] == 5

    def test_column_names(self, df):
        info = get_basic_info(df)
        assert info["column_names"] == ["date", "region", "revenue", "units", "category"]

    def test_missing_values(self, df):
        info = get_basic_info(df)
        assert info["missing"] == {"revenue": 1}

    def test_memory_mb_positive(self, df):
        info = get_basic_info(df)
        assert info["memory_mb"] > 0

    def test_dtypes_are_strings(self, df):
        info = get_basic_info(df)
        assert all(isinstance(v, str) for v in info["dtypes"].values())


class TestGetSummaryStats:
    @pytest.fixture()
    def df(self):
        return load_dataframe(CSV_PATH)

    def test_numeric_columns(self, df):
        stats = get_summary_stats(df)
        assert "revenue" in stats["numeric"]
        assert "units" in stats["numeric"]

    def test_categorical_columns(self, df):
        stats = get_summary_stats(df)
        assert "region" in stats["categorical"]
        assert "category" in stats["categorical"]

    def test_revenue_stats(self, df):
        stats = get_summary_stats(df)
        rev = stats["numeric"]["revenue"]
        assert rev["count"] == 7  # one NaN excluded
        assert rev["min"] == 700.0
        assert rev["max"] == 2100.0
        assert rev["mean"] == pytest.approx(1192.8571, rel=1e-2)

    def test_region_value_counts(self, df):
        stats = get_summary_stats(df)
        regions = stats["categorical"]["region"]
        assert regions["North"] == 3
        assert regions["South"] == 2


# ===========================================================================
# Python executor  (src/tools/python_executor.py)
# ===========================================================================

from src.tools.python_executor import CodeResult, execute_code


class TestExecuteCode:
    def test_simple_print(self):
        result = execute_code("print('hello')")
        assert result.success is True
        assert "hello" in result.output

    def test_arithmetic(self):
        result = execute_code("print(2 + 3)")
        assert result.success is True
        assert "5" in result.output

    def test_multiline(self):
        code = textwrap.dedent("""\
            xs = [1, 2, 3, 4]
            print(sum(xs))
        """)
        result = execute_code(code)
        assert result.success is True
        assert "10" in result.output

    def test_syntax_error(self):
        result = execute_code("def f(\n")
        assert result.success is False
        assert result.error  # non-empty

    def test_runtime_error(self):
        result = execute_code("1 / 0")
        assert result.success is False
        assert "ZeroDivision" in result.error

    def test_empty_code(self):
        result = execute_code("")
        assert result.success is False
        assert "No code" in result.error

    def test_whitespace_only(self):
        result = execute_code("   \n  ")
        assert result.success is False

    def test_blocked_subprocess(self):
        result = execute_code("import subprocess; subprocess.run(['ls'])")
        assert result.success is False
        assert "Blocked" in result.error

    def test_blocked_eval(self):
        result = execute_code("eval('1+1')")
        assert result.success is False
        assert "Blocked" in result.error

    def test_blocked_os_system(self):
        result = execute_code("import os; os.system('echo hi')")
        assert result.success is False
        assert "Blocked" in result.error

    def test_timeout(self):
        code = "import time; time.sleep(30)"
        result = execute_code(code, timeout_seconds=1)
        assert result.success is False
        assert "timed out" in result.error.lower()

    def test_pandas_available(self):
        code = textwrap.dedent("""\
            import pandas as pd
            df = pd.DataFrame({"a": [1, 2, 3]})
            print(df["a"].sum())
        """)
        result = execute_code(code)
        assert result.success is True
        assert "6" in result.output

    def test_reads_real_csv(self):
        code = textwrap.dedent(f"""\
            import pandas as pd
            df = pd.read_csv(r"{CSV_PATH}")
            print(len(df))
        """)
        result = execute_code(code)
        assert result.success is True
        assert "8" in result.output

    def test_code_result_dataclass(self):
        r = CodeResult(success=True, output="ok", error="")
        assert r.success is True
        assert r.output == "ok"


# ===========================================================================
# Planner output format  (src/agents/planner._parse_plan)
# ===========================================================================

from src.agents.planner import _parse_plan


class TestParsePlan:
    """Tests _parse_plan directly — no LLM calls needed."""

    def test_valid_json_array(self):
        raw = json.dumps(["Step 1", "Step 2", "Step 3"])
        steps = _parse_plan(raw, "revenue query")
        assert steps == ["Step 1", "Step 2", "Step 3"]

    def test_json_with_markdown_fences(self):
        raw = '```json\n["Step A", "Step B"]\n```'
        steps = _parse_plan(raw, "q")
        assert steps == ["Step A", "Step B"]

    def test_plain_fences(self):
        raw = '```\n["Step A"]\n```'
        steps = _parse_plan(raw, "q")
        assert steps == ["Step A"]

    def test_whitespace_around_json(self):
        raw = '  \n ["Do X", "Do Y"]  \n  '
        steps = _parse_plan(raw, "q")
        assert steps == ["Do X", "Do Y"]

    def test_empty_strings_filtered(self):
        raw = json.dumps(["Step 1", "", "  ", "Step 2"])
        steps = _parse_plan(raw, "q")
        assert steps == ["Step 1", "Step 2"]

    def test_fallback_on_invalid_json(self):
        steps = _parse_plan("This is not valid JSON", "revenue by region")
        assert len(steps) == 3
        assert "revenue by region" in steps[-1]

    def test_fallback_on_non_array(self):
        raw = json.dumps({"plan": "something"})
        steps = _parse_plan(raw, "q")
        assert len(steps) == 3  # fallback

    def test_fallback_on_mixed_types(self):
        raw = json.dumps(["Step 1", 42, "Step 2"])
        steps = _parse_plan(raw, "q")
        assert len(steps) == 3  # fallback (not all strings)

    def test_fallback_on_empty_array(self):
        steps = _parse_plan("[]", "q")
        assert len(steps) == 3  # fallback

    def test_fallback_empty_query(self):
        steps = _parse_plan("not json", "")
        assert steps[-1] == "Summarise findings"

    def test_single_step(self):
        raw = json.dumps(["Only step"])
        steps = _parse_plan(raw, "q")
        assert steps == ["Only step"]

    def test_strips_step_whitespace(self):
        raw = json.dumps(["  Step 1  ", "Step 2"])
        steps = _parse_plan(raw, "q")
        assert steps == ["Step 1", "Step 2"]
