from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.table import Table

from shared.api.eval_runner import run_project_evaluation
from shared.eval import list_projects


@dataclass
class ProjectDashboardRow:
    project: str
    accuracy: float
    failure_rate: float
    latency_mean_ms: float
    latency_p95_ms: float
    total_cases: int
    failed_cases: int
    status: str
    error: str | None = None


def _default_report_path() -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return Path("shared") / "eval" / "reports" / f"benchmark-report-{timestamp}.json"


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def evaluate_project(project: str) -> ProjectDashboardRow:
    try:
        report = run_project_evaluation(project)
        metrics = report.get("metrics", {})
        latency = metrics.get("latency_ms", {})
        total_cases = int(metrics.get("total", 0))
        failed_cases = int(metrics.get("failed", 0))
        accuracy = _safe_float(metrics.get("accuracy"))

        return ProjectDashboardRow(
            project=report.get("project", project),
            accuracy=accuracy,
            failure_rate=(failed_cases / total_cases) if total_cases else 1.0,
            latency_mean_ms=_safe_float(latency.get("mean", latency.get("avg", 0.0))),
            latency_p95_ms=_safe_float(latency.get("p95", latency.get("max", 0.0))),
            total_cases=total_cases,
            failed_cases=failed_cases,
            status="ok",
        )
    except Exception as exc:
        return ProjectDashboardRow(
            project=project,
            accuracy=0.0,
            failure_rate=1.0,
            latency_mean_ms=0.0,
            latency_p95_ms=0.0,
            total_cases=0,
            failed_cases=0,
            status="error",
            error=str(exc),
        )


def build_report(projects: list[str]) -> dict[str, Any]:
    rows = [evaluate_project(project) for project in projects]

    completed_rows = [row for row in rows if row.status == "ok"]
    total_cases = sum(row.total_cases for row in completed_rows)
    failed_cases = sum(row.failed_cases for row in completed_rows)

    overall = {
        "projects_total": len(rows),
        "projects_succeeded": sum(row.status == "ok" for row in rows),
        "projects_failed": sum(row.status != "ok" for row in rows),
        "cases_total": total_cases,
        "cases_failed": failed_cases,
        "accuracy": (
            sum(row.accuracy * row.total_cases for row in completed_rows) / total_cases
            if total_cases
            else 0.0
        ),
        "failure_rate": (failed_cases / total_cases) if total_cases else 0.0,
        "latency_mean_ms": (
            sum(row.latency_mean_ms for row in completed_rows) / len(completed_rows)
            if completed_rows
            else 0.0
        ),
        "latency_p95_ms": max((row.latency_p95_ms for row in completed_rows), default=0.0),
    }

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "projects": [asdict(row) for row in rows],
        "overall": overall,
    }


def print_console_table(report: dict[str, Any], *, console: Console | None = None) -> None:
    console = console or Console()
    table = Table(title="Benchmark Dashboard")
    table.add_column("Project", style="cyan")
    table.add_column("Accuracy", justify="right")
    table.add_column("Latency (ms)", justify="right")
    table.add_column("Failure Rate", justify="right")
    table.add_column("Status", justify="center")

    for row in report["projects"]:
        status = row["status"] if row["status"] == "ok" else f"error: {row['error']}"
        table.add_row(
            row["project"],
            f"{row['accuracy']:.1%}",
            f"{row['latency_mean_ms']:.1f}",
            f"{row['failure_rate']:.1%}",
            status,
        )

    console.print(table)

    overall = report["overall"]
    console.print(
        "Overall: "
        f"accuracy={overall['accuracy']:.1%} "
        f"latency_mean_ms={overall['latency_mean_ms']:.1f} "
        f"failure_rate={overall['failure_rate']:.1%}"
    )


def save_json_report(report: dict[str, Any], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return output_path


def save_matplotlib_chart(report: dict[str, Any], output_path: Path) -> Path | None:
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        return None

    rows = report["projects"]
    projects = [row["project"] for row in rows]
    accuracies = [row["accuracy"] * 100 for row in rows]
    failure_rates = [row["failure_rate"] * 100 for row in rows]
    latencies = [row["latency_mean_ms"] for row in rows]

    figure, axes = plt.subplots(3, 1, figsize=(14, 12), constrained_layout=True)

    axes[0].bar(projects, accuracies, color="#2E86AB")
    axes[0].set_title("Accuracy by Project")
    axes[0].set_ylabel("Accuracy (%)")

    axes[1].bar(projects, latencies, color="#F18F01")
    axes[1].set_title("Mean Latency by Project")
    axes[1].set_ylabel("Latency (ms)")

    axes[2].bar(projects, failure_rates, color="#C73E1D")
    axes[2].set_title("Failure Rate by Project")
    axes[2].set_ylabel("Failure Rate (%)")

    for axis in axes:
        axis.tick_params(axis="x", rotation=45)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output_path, dpi=150)
    plt.close(figure)
    return output_path


def generate_dashboard_artifacts(
    *,
    projects: list[str] | None = None,
    output_path: Path | None = None,
    plot_path: Path | None = None,
) -> dict[str, Any]:
    """Build the shared benchmark report and optionally persist report artifacts."""
    selected_projects = sorted(projects) if projects else list_projects()
    report = build_report(selected_projects)
    print_console_table(report)

    if output_path is not None:
        saved_report = save_json_report(report, output_path)
        print(f"Saved JSON report to {saved_report}")

    if plot_path is not None:
        saved_plot = save_matplotlib_chart(report, plot_path)
        if saved_plot is None:
            print("matplotlib is not installed; skipping chart generation")
        else:
            print(f"Saved chart to {saved_plot}")

    return report