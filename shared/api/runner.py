"""Project runner — dynamically loads and executes any project pipeline."""

from __future__ import annotations

import importlib.util
import json
import inspect
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from shared.logging import get_logger, reset_log_context, set_log_context
from .step_events import StepEmitter, bind_step_emitter, reset_step_emitter

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
LOGGER = get_logger(__name__)

PROJECT_ALIASES = {
    "ai-interviewer": "genai-interviewer",
    "browser-agent": "genai-browser-agent",
    "clinical-decision-support": "genai-clinical-assistant",
    "codebase-copilot": "genai-code-copilot",
    "content-pipeline": "crew-content-pipeline",
    "data-analysis-agent": "lg-data-agent",
    "debugging-agent": "lg-debugging-agent",
    "document-intelligence": "genai-doc-intelligence",
    "financial-analyst-agent": "genai-financial-analyst",
    "generative-ui-builder": "genai-ui-builder",
    "hiring-crew": "crew-hiring-system",
    "investment-crew": "crew-investment-analyst",
    "knowledge-os": "genai-knowledge-os",
    "multi-agent-research": "genai-research-system",
    "nl2sql-agent": "genai-nl2sql-agent",
    "product-launch-crew": "crew-product-launch",
    "research-graph": "lg-research-agent",
    "startup-simulator": "crew-startup-simulator",
    "support-agent": "lg-support-agent",
    "workflow-agent": "lg-workflow-agent",
}

PREFIXES = ("crew-", "genai-", "lg-")


@dataclass
class RunResult:
    project: str
    output: str
    exit_code: int
    elapsed_ms: float


def _clear_project_imports() -> None:
    """Clear cached project-local package imports between project loads.

    Many projects use absolute imports like ``from app.foo import bar``.
    Without clearing the cached ``app`` package, importing one project's
    entrypoint can leak into the next project load.
    """
    module_names = [name for name in sys.modules if name == "app" or name.startswith("app.")]
    for module_name in module_names:
        sys.modules.pop(module_name, None)


def _load_main(project: str):
    """Import ``<project>/app/main.py`` and return the module, or *None*."""
    main_path = REPO_ROOT / project / "app" / "main.py"
    if not main_path.is_file():
        return None

    project_dir = str(REPO_ROOT / project)
    repo_root = str(REPO_ROOT)

    if project_dir not in sys.path:
        sys.path.insert(0, project_dir)
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)

    _clear_project_imports()

    spec = importlib.util.spec_from_file_location(f"{project}.app.main", str(main_path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def list_available() -> list[str]:
    """Return names of all runnable projects."""
    return sorted(
        d.name
        for d in REPO_ROOT.iterdir()
        if d.is_dir() and (d / "app" / "main.py").is_file()
    )


def resolve_project_name(project: str) -> str:
    """Resolve canonical and legacy project names to a runnable project folder."""
    available = set(list_available())
    if project in available:
        return project

    alias = PROJECT_ALIASES.get(project)
    if alias in available:
        return alias

    for prefix in PREFIXES:
        candidate = f"{prefix}{project}"
        if candidate in available:
            return candidate

    raise ValueError(f"Project '{project}' not found or has no app/main.py")


def run_project(project: str, user_input: str, *, api_key: str, step_emitter: StepEmitter | None = None) -> RunResult:
    """Run a project's standardized ``run(input, api_key)`` entry-point.

    Raises ``ValueError`` if the project is not found or has no callable ``run``.
    """
    resolved_project = resolve_project_name(project)
    tokens = set_log_context(project_name=resolved_project)
    emitter_token = bind_step_emitter(step_emitter)

    LOGGER.info("project run started", extra={"project_name": resolved_project})

    try:
        mod = _load_main(resolved_project)
        if mod is None:
            raise ValueError(f"Project '{project}' not found or has no app/main.py")

        run_fn = getattr(mod, "run", None)
        if run_fn is None:
            raise ValueError(f"{resolved_project}/app/main.py has no run() function")

        start = time.perf_counter()
        run_signature = inspect.signature(run_fn)
        kwargs = {"api_key": api_key}
        if "step_emitter" in run_signature.parameters:
            kwargs["step_emitter"] = step_emitter
        result_dict = run_fn(user_input, **kwargs)
        elapsed_ms = (time.perf_counter() - start) * 1000

        if not isinstance(result_dict, dict):
            result_dict = {"output": result_dict}

        output = json.dumps(result_dict, default=str)

        LOGGER.info(
            "project run finished",
            extra={
                "project_name": resolved_project,
                "latency_ms": f"{elapsed_ms:.2f}",
                "error": "-",
            },
        )

        return RunResult(
            project=resolved_project,
            output=output,
            exit_code=0,
            elapsed_ms=round(elapsed_ms, 2),
        )
    except Exception as exc:
        LOGGER.exception(
            "project run failed",
            extra={"project_name": resolved_project, "error": str(exc)},
        )
        raise
    finally:
        reset_step_emitter(emitter_token)
        reset_log_context(tokens)
