from __future__ import annotations

from typing import Any

from shared.eval.metrics import keyword_accuracy


def collect_research_metrics(query: str, state: dict[str, Any]) -> dict[str, Any]:
    report = str(state.get("final_output", "") or "")
    plan = list(state.get("plan", []) or [])
    findings = dict(state.get("findings", {}) or {})
    critiques = dict(state.get("critiques", {}) or {})
    requested_formats = tuple(state.get("formats", ("report",)) or ("report",))
    if "all" in requested_formats:
        requested_formats = ("report", "blog", "linkedin", "twitter")

    generated_formats: list[str] = ["report"] if report else []
    if state.get("blog"):
        generated_formats.append("blog")
    if state.get("linkedin_post"):
        generated_formats.append("linkedin")
    if state.get("twitter_thread"):
        generated_formats.append("twitter")

    requested_non_report = [fmt for fmt in requested_formats if fmt != "report"]
    generated_non_report = [fmt for fmt in generated_formats if fmt != "report"]
    report_words = len(report.split())
    report_sections = sum(1 for line in report.splitlines() if line.strip().startswith("## "))

    scenario_coverage = 0.0
    if state.get("best_case"):
        scenario_coverage += 0.5
    if state.get("worst_case"):
        scenario_coverage += 0.5

    format_coverage = 1.0
    if requested_non_report:
        format_coverage = len(generated_non_report) / len(requested_non_report)

    keyword_coverage = keyword_accuracy(report, query)
    originality_score = float(state.get("originality_score", 0.0) or 0.0)
    completeness_signals = [
        1.0 if report else 0.0,
        1.0 if findings and len(findings) >= len(plan) else 0.0,
        1.0 if not critiques else 0.0,
    ]
    quality_score = (
        keyword_coverage + originality_score + format_coverage + scenario_coverage + sum(completeness_signals) / len(completeness_signals)
    ) / 5

    return {
        "latency_ms": round(float(state.get("total_duration_ms", 0.0) or 0.0), 2),
        "plan_tasks": len(plan),
        "completed_findings": len(findings),
        "open_critiques": len(critiques),
        "research_iterations": int(state.get("iteration", 0) or 0),
        "editor_revisions": int(state.get("editor_revisions", 0) or 0),
        "originality_rewrites": int(state.get("originality_rewrites", 0) or 0),
        "originality_score": round(originality_score, 3),
        "format_coverage": round(format_coverage, 3),
        "scenario_coverage": round(scenario_coverage, 3),
        "keyword_coverage": round(keyword_coverage, 3),
        "quality_score": round(quality_score, 3),
        "report_words": report_words,
        "report_chars": len(report),
        "report_sections": report_sections,
        "formats_requested": list(requested_formats),
        "formats_generated": generated_formats,
        "node_count": len(dict(state.get("node_timings", {}) or {})),
        "node_timings": dict(state.get("node_timings", {}) or {}),
        "success": bool(report),
    }


def aggregate_quality_metrics(metric_rows: list[dict[str, Any]]) -> dict[str, float]:
    if not metric_rows:
        return {
            "failure_rate": 0.0,
            "mean_quality_score": 0.0,
            "mean_originality_score": 0.0,
            "mean_format_coverage": 0.0,
            "mean_keyword_coverage": 0.0,
            "mean_report_words": 0.0,
        }

    total = len(metric_rows)
    failures = sum(1 for row in metric_rows if not row.get("success"))
    return {
        "failure_rate": failures / total,
        "mean_quality_score": sum(float(row.get("quality_score", 0.0)) for row in metric_rows) / total,
        "mean_originality_score": sum(float(row.get("originality_score", 0.0)) for row in metric_rows) / total,
        "mean_format_coverage": sum(float(row.get("format_coverage", 0.0)) for row in metric_rows) / total,
        "mean_keyword_coverage": sum(float(row.get("keyword_coverage", 0.0)) for row in metric_rows) / total,
        "mean_report_words": sum(float(row.get("report_words", 0.0)) for row in metric_rows) / total,
    }