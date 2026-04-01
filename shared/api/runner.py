"""Project runner — dynamically loads and executes any project pipeline."""

from __future__ import annotations

import importlib.util
import json
import inspect
import sys
import time
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from shared.logging import get_logger, reset_log_context, set_log_context
from shared.project_catalog import load_project_catalog, project_api_name
from .step_events import StepEmitter, bind_step_emitter, reset_step_emitter

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
LOGGER = get_logger(__name__)


@lru_cache(maxsize=1)
def _project_aliases() -> dict[str, str]:
    """Derive API-name → folder-slug mapping from the canonical project catalog."""
    return {
        project_api_name(entry.apiEndpoint): entry.slug
        for entry in load_project_catalog()
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

    alias = _project_aliases().get(project)
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
