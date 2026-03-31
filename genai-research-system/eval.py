"""Project-local evaluation runner for genai-research-system.

This module uses the shared evaluation layer while keeping project-specific
cases local to the project.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent
REPO_ROOT = PROJECT_ROOT.parent

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.metrics import aggregate_quality_metrics
from app.service import run_research_workflow
from shared.config import reset_byok_api_key, set_byok_api_key
from shared.eval import keyword_accuracy, latency_stats, run_evaluation, structural_match


def _contains_keywords(output: str, keywords: list[str], threshold: float = 0.5) -> bool:
    return keyword_accuracy(output, keywords) >= threshold


TEST_CASES: list[dict[str, Any]] = [
    {
        "name": "llm_software_engineering",
        "input": "impact of large language models on software engineering",
        "rule": lambda result: _contains_keywords(
            result.get("report", ""),
            ["language", "model", "software", "engineering"],
            threshold=0.5,
        ),
    },
    {
        "name": "renewable_energy_sections",
        "input": "renewable energy trends in 2025",
        "rule": lambda result: structural_match(
            result.get("report", ""),
            r"(introduction|overview|summary|conclusion)",
        ) == 1.0,
    },
    {
        "name": "transformer_citations",
        "input": "history of transformer architecture",
        "rule": lambda result: _contains_keywords(
            result.get("report", ""),
            ["transformer", "attention", "source"],
            threshold=2 / 3,
        )
        or structural_match(result.get("report", ""), r"(reference|http|\[\d+\])") == 1.0,
    },
    {
        "name": "cloud_security_key_points",
        "input": "top cloud security risks for enterprise teams",
        "rule": lambda result: _contains_keywords(
            result.get("report", ""),
            ["cloud", "security", "risk", "enterprise"],
            threshold=0.5,
        ),
    },
    {
        "name": "ai_healthcare_scenarios",
        "input": "future of AI in healthcare diagnostics",
        "rule": lambda result: bool(result.get("best_case")) and bool(result.get("worst_case")),
    },
    {
        "name": "remote_work_multiformat",
        "input": "future of remote work in global companies",
        "kwargs": {"formats": ("report", "blog", "linkedin", "twitter")},
        "rule": lambda result: bool(result.get("report"))
        and bool(result.get("blog"))
        and bool(result.get("linkedin_post"))
        and bool(result.get("twitter_thread")),
    },
]


def _run_research_query(
    query: str,
    *,
    tone: str = "formal",
    formats: tuple[str, ...] = ("report",),
) -> dict[str, Any]:
    """Run the flagship research workflow and return the structured response."""
    return run_research_workflow(query, tone=tone, formats=formats)


def run_project_eval() -> dict[str, Any]:
    """Run the project benchmark cases and print summary metrics."""
    dataset = [
        {
            "name": case["name"],
            "input": case["input"],
            "kwargs": case.get("kwargs", {}),
            "max_retries": case.get("max_retries", 0),
        }
        for case in TEST_CASES
    ]

    eval_metrics = run_evaluation(_run_research_query, dataset)

    passed_cases = 0
    failed_cases: list[dict[str, Any]] = []
    latencies = [case["latency_ms"] for case in eval_metrics["cases"]]
    quality_rows: list[dict[str, Any]] = []

    for case_def, case_result in zip(TEST_CASES, eval_metrics["cases"]):
        output_metrics = dict(case_result.get("output", {}).get("metrics", {}) or {})
        if output_metrics:
            quality_rows.append(output_metrics)

        if case_result["success"] and case_def["rule"](case_result["output"]):
            passed_cases += 1
            continue

        failed_cases.append(
            {
                "name": case_result["name"],
                "error": case_result["error"],
                "latency_ms": case_result["latency_ms"],
            }
        )

    latency = latency_stats(latencies)
    quality_summary = aggregate_quality_metrics(quality_rows)
    metrics = {
        "project": PROJECT_ROOT.name,
        "total": len(TEST_CASES),
        "accuracy": passed_cases / len(TEST_CASES) if TEST_CASES else 0.0,
        "failure_rate": len(failed_cases) / len(TEST_CASES) if TEST_CASES else 0.0,
        "latency_ms": latency,
        "quality": quality_summary,
        "failures": failed_cases,
        "shared_eval": eval_metrics,
    }

    print(f"Project: {metrics['project']}")
    print(f"Accuracy: {metrics['accuracy']:.2%}")
    print(f"Failure Rate: {metrics['failure_rate']:.2%}")
    print(
        "Latency: "
        f"avg={latency['mean']:.1f}ms "
        f"p95={latency['p95']:.1f}ms "
        f"min={latency['min']:.1f}ms "
        f"max={latency['max']:.1f}ms"
    )
    print(
        "Quality: "
        f"score={quality_summary['mean_quality_score']:.2f} "
        f"originality={quality_summary['mean_originality_score']:.2f} "
        f"format_coverage={quality_summary['mean_format_coverage']:.2%}"
    )
    print(f"Failures: {len(failed_cases)}")

    if failed_cases:
        for failure in failed_cases:
            reason = failure["error"] or "rule check failed"
            print(f"  - {failure['name']}: {reason}")

    return metrics


def run_project_eval_with_api_key(api_key: str) -> dict[str, Any]:
    """Run the project evaluation with an explicitly bound API key."""
    token = set_byok_api_key(api_key.strip())
    try:
        return run_project_eval()
    finally:
        reset_byok_api_key(token)
