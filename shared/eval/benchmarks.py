"""Benchmark datasets and runner for all 20 projects.

Each project has a list of benchmark cases with rule-based expectations.
Cases are designed for ``shared.eval.evaluator.run_evaluation``: pass a
project's ``task_fn`` and its dataset to ``run_evaluation`` for automated
scoring.

Usage::

    from shared.eval.benchmarks import get_dataset, BENCHMARKS, BenchmarkSuite
    cases = get_dataset("genai-nl2sql-agent")
    # Each case: {"name", "input", "rule", "max_retries", ...}

The ``BenchmarkSuite`` / ``BenchmarkCase`` classes are also available for
latency-focused benchmarking of any callable.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from typing import Any, Callable

from .metrics import latency_stats


# ---------------------------------------------------------------------------
# Benchmark runner (latency-focused)
# ---------------------------------------------------------------------------

@dataclass
class BenchmarkCase:
    """A single benchmark definition."""

    name: str
    fn: Callable[..., Any]
    args: tuple[Any, ...] = ()
    kwargs: dict[str, Any] = field(default_factory=dict)
    iterations: int = 5


@dataclass
class BenchmarkResult:
    """Aggregated result for one benchmark case."""

    name: str
    iterations: int
    latencies_ms: list[float]
    stats: dict[str, float]
    last_output: Any = None


class BenchmarkSuite:
    """Collect and run benchmark cases, returning latency statistics.

    Usage::

        suite = BenchmarkSuite("llm-calls")
        suite.add(BenchmarkCase("generate", fn=generate_text,
                                args=("prompt",), kwargs={"model": "gemini-3-flash-preview"}))
        results = suite.run()
    """

    def __init__(self, name: str) -> None:
        self.name = name
        self._cases: list[BenchmarkCase] = []

    def add(self, case: BenchmarkCase) -> None:
        self._cases.append(case)

    def run(self) -> list[BenchmarkResult]:
        results: list[BenchmarkResult] = []
        for case in self._cases:
            latencies: list[float] = []
            last_output = None
            for _ in range(case.iterations):
                start = time.perf_counter()
                last_output = case.fn(*case.args, **case.kwargs)
                latencies.append((time.perf_counter() - start) * 1000)

            results.append(
                BenchmarkResult(
                    name=case.name,
                    iterations=case.iterations,
                    latencies_ms=latencies,
                    stats=latency_stats(latencies),
                    last_output=last_output,
                )
            )
        return results

    def summary(self, results: list[BenchmarkResult] | None = None) -> dict[str, Any]:
        if results is None:
            results = self.run()
        return {
            "suite": self.name,
            "cases": [
                {"name": r.name, "iterations": r.iterations, **r.stats}
                for r in results
            ],
        }


# ---------------------------------------------------------------------------
# Rule helpers — reusable predicates for rule-based expectations
# ---------------------------------------------------------------------------

def _contains_any(output: str, *terms: str) -> bool:
    """True if *output* contains at least one of *terms* (case-insensitive)."""
    lower = output.lower()
    return any(t.lower() in lower for t in terms)


def _contains_all(output: str, *terms: str) -> bool:
    """True if *output* contains every one of *terms* (case-insensitive)."""
    lower = output.lower()
    return all(t.lower() in lower for t in terms)


def _matches(output: str, pattern: str) -> bool:
    """True if *output* matches a regex *pattern* (case-insensitive)."""
    return bool(re.search(pattern, output, re.IGNORECASE))


def _min_length(output: str, n: int) -> bool:
    """True if *output* is at least *n* characters long."""
    return len(output) >= n


def _is_valid_json(output: str) -> bool:
    """True if *output* is parseable JSON."""
    import json
    try:
        json.loads(output)
        return True
    except (json.JSONDecodeError, TypeError):
        return False


def _no_error(output: Any) -> bool:
    """True unless output looks like an error message."""
    if output is None:
        return False
    s = str(output).lower()
    return "error" not in s and "traceback" not in s


# ---------------------------------------------------------------------------
# Per-project benchmark datasets
# ---------------------------------------------------------------------------

_NL2SQL = [
    {
        "name": "group_by_query",
        "input": "top customers by total spend",
        "rule": lambda out: _contains_any(str(out), "GROUP BY", "group by"),
    },
    {
        "name": "count_query",
        "input": "how many orders were placed last month",
        "rule": lambda out: _contains_any(str(out), "COUNT", "count("),
    },
    {
        "name": "join_query",
        "input": "list products with their category names",
        "rule": lambda out: _contains_any(str(out), "JOIN", "join"),
    },
    {
        "name": "where_filter",
        "input": "orders over 1000 dollars",
        "rule": lambda out: _matches(str(out), r"WHERE.*>|WHERE.*>=|where.*>"),
    },
    {
        "name": "aggregate_avg",
        "input": "average order value",
        "rule": lambda out: _contains_any(str(out), "AVG", "avg("),
    },
]

_RESEARCH_SYSTEM = [
    {
        "name": "key_points",
        "input": "impact of large language models on software engineering",
        "rule": lambda out: _min_length(str(out), 200) and _contains_any(str(out), "LLM", "language model", "software"),
    },
    {
        "name": "structured_sections",
        "input": "renewable energy trends in 2025",
        "rule": lambda out: _matches(str(out), r"(introduction|overview|conclusion|summary)", ),
    },
    {
        "name": "citations_present",
        "input": "history of transformer architecture",
        "rule": lambda out: _matches(str(out), r"(source|reference|\[\d+\]|http)"),
    },
]

_CODE_COPILOT = [
    {
        "name": "mentions_function",
        "input": "what does the main function do?",
        "rule": lambda out: _contains_any(str(out), "main", "def ", "function"),
    },
    {
        "name": "mentions_class",
        "input": "list all classes in this codebase",
        "rule": lambda out: _contains_any(str(out), "class"),
    },
    {
        "name": "explains_import",
        "input": "what libraries are used?",
        "rule": lambda out: _contains_any(str(out), "import", "library", "package", "module"),
    },
]

_CLINICAL_ASSISTANT = [
    {
        "name": "condition_with_confidence",
        "input": "45-year-old male with chest pain, shortness of breath, and fatigue",
        "rule": lambda out: _matches(str(out), r"(confidence|score|percent|\d+\.\d+)") and _min_length(str(out), 100),
    },
    {
        "name": "multiple_conditions",
        "input": "30-year-old female with persistent cough, weight loss, and night sweats",
        "rule": lambda out: _matches(str(out), r"(condition|diagnosis|differential)"),
    },
    {
        "name": "report_format",
        "input": "elderly patient with confusion, fever, and painful urination",
        "rule": lambda out: _min_length(str(out), 150),
    },
]

_BROWSER_AGENT = [
    {
        "name": "plan_steps",
        "input": "go to google.com and search for 'latest AI tools'",
        "rule": lambda out: _contains_any(str(out), "navigate", "click", "search", "type", "step"),
    },
    {
        "name": "goal_echo",
        "input": "open github.com and click on Explore",
        "rule": lambda out: _contains_any(str(out), "github", "explore"),
    },
]

_KNOWLEDGE_OS = [
    {
        "name": "query_with_sources",
        "input": "query what is retrieval augmented generation?",
        "rule": lambda out: _contains_any(str(out), "retrieval", "RAG", "generation"),
    },
    {
        "name": "insight_generation",
        "input": "query key themes across all documents",
        "rule": lambda out: _min_length(str(out), 80),
    },
]

_INTERVIEWER = [
    {
        "name": "generates_question",
        "input": "Python",
        "rule": lambda out: _matches(str(out), r"\?"),
    },
    {
        "name": "difficulty_present",
        "input": "system design",
        "rule": lambda out: _contains_any(str(out), "easy", "medium", "hard", "difficulty", "question"),
    },
    {
        "name": "feedback_present",
        "input": "data structures",
        "rule": lambda out: _contains_any(str(out), "feedback", "score", "evaluation", "correct"),
    },
]

_UI_BUILDER = [
    {
        "name": "jsx_output",
        "input": "a login form with email and password fields",
        "rule": lambda out: _contains_any(str(out), "<", "return", "jsx", "react", "component"),
    },
    {
        "name": "contains_inputs",
        "input": "a dashboard with a sidebar and chart",
        "rule": lambda out: _contains_any(str(out), "sidebar", "chart", "dashboard"),
    },
]

_DOC_INTELLIGENCE = [
    {
        "name": "citation_in_answer",
        "input": "query what are the main findings?",
        "rule": lambda out: _contains_any(str(out), "source", "citation", "document", "finding"),
    },
    {
        "name": "extraction_structured",
        "input": "extract key information from the report",
        "rule": lambda out: _no_error(out) and _min_length(str(out), 50),
    },
]

_FINANCIAL_ANALYST = [
    {
        "name": "kpi_present",
        "input": "analyze revenue trends",
        "rule": lambda out: _contains_any(str(out), "revenue", "growth", "trend", "KPI", "metric"),
    },
    {
        "name": "forecast_output",
        "input": "forecast next 3 periods",
        "rule": lambda out: _contains_any(str(out), "forecast", "predict", "period", "project"),
    },
    {
        "name": "report_length",
        "input": "generate a financial summary",
        "rule": lambda out: _min_length(str(out), 100),
    },
]

_DATA_AGENT = [
    {
        "name": "plan_generated",
        "input": "total revenue by region",
        "rule": lambda out: _contains_any(str(out), "revenue", "region", "group", "plan"),
    },
    {
        "name": "numeric_result",
        "input": "average order value per customer",
        "rule": lambda out: _matches(str(out), r"\d+"),
    },
    {
        "name": "chart_mention",
        "input": "plot monthly sales trend",
        "rule": lambda out: _contains_any(str(out), "chart", "plot", "figure", "image", "png"),
    },
]

_DEBUGGING_AGENT = [
    {
        "name": "fix_type_error",
        "input": "def add(a, b): return a + b\nadd('1', 2)",
        "rule": lambda out: _contains_any(str(out), "fix", "int", "str", "type", "convert"),
    },
    {
        "name": "diff_output",
        "input": "x = [1,2,3]\nprint(x[5])",
        "rule": lambda out: _contains_any(str(out), "index", "range", "diff", "fix", "bound"),
    },
    {
        "name": "no_runtime_error",
        "input": "def greet(name):\n    return 'Hello ' + name\ngreet(None)",
        "rule": lambda out: _no_error(out),
    },
]

_RESEARCH_AGENT_LG = [
    {
        "name": "produces_output",
        "input": "benefits of microservices architecture",
        "rule": lambda out: _min_length(str(out), 50),
    },
    {
        "name": "topic_relevant",
        "input": "quantum computing applications",
        "rule": lambda out: _contains_any(str(out), "quantum", "computing", "qubit"),
    },
]

_SUPPORT_AGENT = [
    {
        "name": "intent_classified",
        "input": "I was charged twice for my subscription",
        "rule": lambda out: _contains_any(str(out), "billing", "charge", "refund", "payment", "intent"),
    },
    {
        "name": "escalation_detected",
        "input": "I want to speak to a manager right now",
        "rule": lambda out: _contains_any(str(out), "escalat", "manager", "agent", "transfer"),
    },
    {
        "name": "helpful_response",
        "input": "how do I reset my password?",
        "rule": lambda out: _contains_any(str(out), "password", "reset", "account", "link"),
    },
]

_WORKFLOW_AGENT = [
    {
        "name": "task_decomposed",
        "input": "organize a team offsite event for 20 people",
        "rule": lambda out: _contains_any(str(out), "step", "plan", "task", "venue", "budget"),
    },
    {
        "name": "execution_tracked",
        "input": "analyze sales data and generate a report",
        "rule": lambda out: _contains_any(str(out), "result", "report", "analys", "complete"),
    },
]

_CONTENT_PIPELINE = [
    {
        "name": "article_generated",
        "input": "the future of remote work",
        "rule": lambda out: _min_length(str(out), 300),
    },
    {
        "name": "seo_keywords",
        "input": "best practices for cloud security",
        "rule": lambda out: _contains_any(str(out), "cloud", "security", "keyword", "SEO", "meta"),
    },
    {
        "name": "structured_flow",
        "input": "introduction to generative AI",
        "rule": lambda out: _matches(str(out), r"(research|draft|edit|seo|final)"),
    },
]

_HIRING_SYSTEM = [
    {
        "name": "decision_present",
        "input": "5 years Python, distributed systems, AWS",
        "rule": lambda out: _contains_any(str(out), "hire", "reject", "decision", "recommend"),
    },
    {
        "name": "score_present",
        "input": "10 years ML engineer, published papers, TensorFlow",
        "rule": lambda out: _matches(str(out), r"(score|confidence|\d\.\d)"),
    },
    {
        "name": "bias_audit",
        "input": "junior developer, bootcamp graduate, JavaScript",
        "rule": lambda out: _contains_any(str(out), "bias", "audit", "fair", "risk"),
    },
]

_INVESTMENT_ANALYST = [
    {
        "name": "recommendation",
        "input": "evaluate Tesla as an investment",
        "rule": lambda out: _contains_any(str(out), "buy", "sell", "hold", "recommend", "invest", "risk"),
    },
    {
        "name": "risk_mentioned",
        "input": "analyze Apple stock",
        "rule": lambda out: _contains_any(str(out), "risk", "volatil", "downside", "competition"),
    },
    {
        "name": "financial_data",
        "input": "assess NVIDIA growth potential",
        "rule": lambda out: _contains_any(str(out), "revenue", "growth", "market", "valuation"),
    },
]

_PRODUCT_LAUNCH = [
    {
        "name": "strategy_output",
        "input": "launch a new AI-powered note-taking app",
        "rule": lambda out: _contains_any(str(out), "strategy", "market", "launch", "audience", "persona"),
    },
    {
        "name": "positioning",
        "input": "premium fitness tracking wearable",
        "rule": lambda out: _contains_any(str(out), "position", "differentiator", "compet", "value"),
    },
]

_STARTUP_SIMULATOR = [
    {
        "name": "plan_generated",
        "input": "AI-powered healthcare diagnostics startup",
        "rule": lambda out: _min_length(str(out), 200) and _contains_any(str(out), "plan", "product", "market"),
    },
    {
        "name": "roles_present",
        "input": "edtech platform for personalized learning",
        "rule": lambda out: _contains_any(str(out), "CEO", "CTO", "engineer", "product", "founder"),
    },
    {
        "name": "execution_roadmap",
        "input": "sustainable packaging marketplace",
        "rule": lambda out: _contains_any(str(out), "roadmap", "milestone", "phase", "timeline", "quarter"),
    },
]


# ---------------------------------------------------------------------------
# Registry — maps project folder name to its benchmark dataset
# ---------------------------------------------------------------------------

BENCHMARKS: dict[str, list[dict[str, Any]]] = {
    "genai-nl2sql-agent": _NL2SQL,
    "genai-research-system": _RESEARCH_SYSTEM,
    "genai-code-copilot": _CODE_COPILOT,
    "genai-clinical-assistant": _CLINICAL_ASSISTANT,
    "genai-browser-agent": _BROWSER_AGENT,
    "genai-knowledge-os": _KNOWLEDGE_OS,
    "genai-interviewer": _INTERVIEWER,
    "genai-ui-builder": _UI_BUILDER,
    "genai-doc-intelligence": _DOC_INTELLIGENCE,
    "genai-financial-analyst": _FINANCIAL_ANALYST,
    "lg-data-agent": _DATA_AGENT,
    "lg-debugging-agent": _DEBUGGING_AGENT,
    "lg-research-agent": _RESEARCH_AGENT_LG,
    "lg-support-agent": _SUPPORT_AGENT,
    "lg-workflow-agent": _WORKFLOW_AGENT,
    "crew-content-pipeline": _CONTENT_PIPELINE,
    "crew-hiring-system": _HIRING_SYSTEM,
    "crew-investment-analyst": _INVESTMENT_ANALYST,
    "crew-product-launch": _PRODUCT_LAUNCH,
    "crew-startup-simulator": _STARTUP_SIMULATOR,
}


def get_dataset(project: str) -> list[dict[str, Any]]:
    """Return the benchmark dataset for a project by folder name.

    Raises ``KeyError`` if the project is not registered.
    """
    return BENCHMARKS[project]


def list_projects() -> list[str]:
    """Return sorted list of projects that have benchmark datasets."""
    return sorted(BENCHMARKS)
