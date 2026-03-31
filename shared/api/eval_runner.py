"""Project evaluation runner backed by shared benchmark datasets."""

from __future__ import annotations

import time
from typing import Any

from shared.eval.benchmarks import BENCHMARKS, get_dataset
from shared.eval.metrics import latency_stats
from shared.config import get_effective_api_key
from shared.logging import get_logger, log_context

from .runner import resolve_project_name, run_project


LOGGER = get_logger(__name__)


def run_project_evaluation(project: str) -> dict[str, Any]:
    """Run the shared benchmark dataset for a project and return aggregate metrics."""
    resolved_project = resolve_project_name(project)

    LOGGER.info("evaluation started", extra={"project_name": resolved_project})

    try:
        dataset = get_dataset(resolved_project)
    except KeyError as exc:
        raise ValueError(f"Project '{project}' does not have a registered benchmark dataset") from exc

    case_results: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    latencies_ms: list[float] = []
    passed = 0

    with log_context(project_name=resolved_project):
        for index, case in enumerate(dataset):
            case_name = case.get("name", f"case_{index}")
            case_input = str(case.get("input", ""))
            rule = case.get("rule")
            start = time.perf_counter()

            try:
                result = run_project(resolved_project, case_input, api_key=get_effective_api_key())
                output = result.output
                exit_code = result.exit_code
                latency_ms = result.elapsed_ms
                error = None
            except Exception as exc:
                output = ""
                exit_code = 1
                latency_ms = round((time.perf_counter() - start) * 1000, 2)
                error = str(exc)

            rule_passed = bool(rule(output)) if callable(rule) and error is None else False
            success = exit_code == 0 and error is None and rule_passed

            case_result = {
                "name": case_name,
                "input": case_input,
                "success": success,
                "exit_code": exit_code,
                "latency_ms": latency_ms,
                "error": error,
                "output": output,
            }
            case_results.append(case_result)
            latencies_ms.append(latency_ms)

            if success:
                passed += 1
            else:
                failures.append(case_result)
                LOGGER.warning(
                    "evaluation case failed",
                    extra={
                        "project_name": resolved_project,
                        "latency_ms": f"{latency_ms:.2f}",
                        "error": error or f"rule_failed:{case_name}",
                    },
                )

    total = len(case_results)
    failed = total - passed

    report = {
        "requested_project": project,
        "project": resolved_project,
        "metrics": {
            "total": total,
            "passed": passed,
            "failed": failed,
            "accuracy": (passed / total) if total else 0.0,
            "latency_ms": latency_stats(latencies_ms),
        },
        "failures": failures,
        "cases": case_results,
    }

    LOGGER.info(
        "evaluation finished",
        extra={
            "project_name": resolved_project,
            "latency_ms": f"{report['metrics']['latency_ms']['mean']:.2f}",
            "error": "-" if failed == 0 else f"failed_cases={failed}",
        },
    )
    return report


def build_leaderboard() -> list[dict[str, float | str]]:
    """Run all registered benchmark suites and rank projects by accuracy/latency."""
    entries: list[dict[str, float | str]] = []

    for project_name in sorted(BENCHMARKS):
        report = run_project_evaluation(project_name)
        accuracy = float(report["metrics"]["accuracy"])
        latency = float(report["metrics"]["latency_ms"]["mean"])
        score = accuracy / latency if latency > 0 else 0.0
        entries.append(
            {
                "project": str(report["project"]),
                "accuracy": round(accuracy, 4),
                "latency": round(latency, 2),
                "score": round(score, 6),
            }
        )

    return sorted(entries, key=lambda entry: float(entry["score"]), reverse=True)