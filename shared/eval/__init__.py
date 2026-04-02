"""Shared evaluation framework for LLM-powered projects."""

from .evaluator import run_evaluation
from .metrics import (
    keyword_accuracy,
    latency_stats,
    structural_match,
)
from .benchmarks import (
    BenchmarkSuite,
    BenchmarkCase,
    BENCHMARKS,
    get_dataset,
    list_projects,
)
from .stress import run_stress_test, StressRunner, StressResult

__all__ = [
    "run_evaluation",
    "BenchmarkSuite",
    "BenchmarkCase",
    "BENCHMARKS",
    "get_dataset",
    "list_projects",
    "run_stress_test",
    "StressRunner",
    "StressResult",
    "keyword_accuracy",
    "latency_stats",
    "structural_match",
]
