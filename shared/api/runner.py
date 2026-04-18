"""Project runner — dynamically loads and executes any project pipeline."""

from __future__ import annotations

import importlib.util
import json
import inspect
import os
import sys
import threading
import queue
import time
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from shared.logging import get_logger, reset_log_context, set_log_context
from shared.observability.langfuse import score_trace, trace_context, flush as langfuse_flush
from shared.project_catalog import load_project_catalog, project_api_name
from .step_events import StepEmitter, bind_step_emitter, reset_step_emitter

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
LOGGER = get_logger(__name__)

# Module-load cache — see ``_load_main`` below.  ``dev`` mode uses the
# on-disk mtime to hot-reload modified project code; ``prod`` caches
# unconditionally for the lifetime of the process.
_MODULE_CACHE: dict[str, tuple[float, object]] = {}
_MODULE_CACHE_LOCK = threading.RLock()
# ``sys.modules`` / ``sys.path`` mutation must be serialised across threads.
_SYS_MODULES_LOCK = threading.Lock()


def _is_dev_mode() -> bool:
    return os.getenv("APP_ENV", "dev").strip().lower() != "prod"

LEGACY_PROJECT_API_NAMES = {
    "ai-interviewer": "interviewer",
    "clinical-decision-support": "clinical-assistant",
    "codebase-copilot": "code-copilot",
    "data-analysis-agent": "data-agent",
    "document-intelligence": "doc-intelligence",
    "financial-analyst-agent": "financial-analyst",
    "generative-ui-builder": "ui-builder",
    "product-launch-crew": "product-launch",
    "research-graph": "research-agent",
}


@lru_cache(maxsize=1)
def _project_aliases() -> dict[str, str]:
    """Derive API-name → folder-slug mapping from the catalog plus legacy route aliases."""
    aliases = {
        project_api_name(entry.apiEndpoint): entry.slug
        for entry in load_project_catalog()
    }
    aliases.update(
        {
            legacy_name: aliases[current_name]
            for legacy_name, current_name in LEGACY_PROJECT_API_NAMES.items()
        }
    )
    return aliases

PREFIXES = ("crew-", "genai-", "lg-")

OPTIONAL_DEPLOYMENT_DEPENDENCIES: dict[str, str] = {
    "crewai": "CrewAI-backed projects are unavailable in this deployment because the optional CrewAI runtime is not installed.",
    "playwright": "Browser automation projects are unavailable in this deployment because the optional Playwright runtime is not installed.",
}


class ProjectUnavailableError(RuntimeError):
    """Raised when a project cannot run in the current deployment footprint."""


def _optional_dependency_error(exc: ModuleNotFoundError) -> ProjectUnavailableError | None:
    missing = (exc.name or "").split(".", 1)[0]
    if missing not in OPTIONAL_DEPLOYMENT_DEPENDENCIES:
        return None
    message = OPTIONAL_DEPLOYMENT_DEPENDENCIES[missing]
    return ProjectUnavailableError(message)


@dataclass
class RunResult:
    project: str
    output: str
    exit_code: int
    elapsed_ms: float
    trace_id: str | None = None


def _clear_project_imports() -> None:
    """Clear cached project-local package imports between project loads.

    Many projects use absolute imports like ``from app.foo import bar``.
    Without clearing the cached ``app`` package, importing one project's
    entrypoint can leak into the next project load.  Always called under
    ``_SYS_MODULES_LOCK`` so that concurrent requests for different projects
    cannot trample each other's module tables.
    """
    module_names = [name for name in sys.modules if name == "app" or name.startswith("app.")]
    for module_name in module_names:
        sys.modules.pop(module_name, None)


def _load_main(project: str):
    """Import ``<project>/app/main.py`` and return the module, or *None*.

    Results are cached keyed on project name.  In dev mode the cache is
    invalidated when ``main.py``'s mtime changes so edits take effect without
    restarting the API.  In prod mode the first load wins — heavy frameworks
    like CrewAI and LangGraph add 1–3 s of cold-import overhead which the old
    code paid on every request.

    ``sys.modules`` mutation is serialised to avoid two concurrent project
    loads clobbering each other's ``app.*`` module references.
    """
    main_path = REPO_ROOT / project / "app" / "main.py"
    if not main_path.is_file():
        return None

    mtime = main_path.stat().st_mtime
    with _MODULE_CACHE_LOCK:
        cached = _MODULE_CACHE.get(project)
        if cached is not None:
            cached_mtime, cached_module = cached
            if not _is_dev_mode() or cached_mtime == mtime:
                # Ensure sys.path still contains the project dir in case a
                # subsequent project load cleared it — cheap enough to redo.
                with _SYS_MODULES_LOCK:
                    project_dir = str(REPO_ROOT / project)
                    repo_root = str(REPO_ROOT)
                    if project_dir not in sys.path:
                        sys.path.insert(0, project_dir)
                    if repo_root not in sys.path:
                        sys.path.insert(0, repo_root)
                return cached_module

    project_dir = str(REPO_ROOT / project)
    repo_root = str(REPO_ROOT)

    with _SYS_MODULES_LOCK:
        if project_dir not in sys.path:
            sys.path.insert(0, project_dir)
        if repo_root not in sys.path:
            sys.path.insert(0, repo_root)
        _clear_project_imports()

        spec = importlib.util.spec_from_file_location(f"{project}.app.main", str(main_path))
        if spec is None or spec.loader is None:  # pragma: no cover — defensive
            return None
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

    with _MODULE_CACHE_LOCK:
        _MODULE_CACHE[project] = (mtime, mod)
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

    trace = None
    trace_id: str | None = None

    LOGGER.info("project run started", extra={"project_name": resolved_project})

    try:
        with trace_context(
            name=f"project-run:{resolved_project}",
            input={"project": resolved_project, "user_input": user_input[:500]},
            metadata={"project": resolved_project},
            tags=[resolved_project],
        ) as active_trace:
            trace = active_trace
            trace_id = getattr(active_trace, "trace_id", None)

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

            if trace is not None:
                try:
                    trace.update(
                        output=result_dict,
                        metadata={"latency_ms": round(elapsed_ms, 2), "success": True},
                    )
                    score_trace(trace=trace, name="success", value=1.0)
                    score_trace(trace=trace, name="latency_ms", value=round(elapsed_ms, 2))
                except Exception:
                    pass

            return RunResult(
                project=resolved_project,
                output=output,
                exit_code=0,
                elapsed_ms=round(elapsed_ms, 2),
                trace_id=trace_id,
            )
    except ModuleNotFoundError as exc:
        unavailable_error = _optional_dependency_error(exc)
        if unavailable_error is None:
            LOGGER.exception(
                "project run failed",
                extra={"project_name": resolved_project, "error": str(exc)},
            )
            if trace is not None:
                score_trace(trace=trace, name="success", value=0.0)
            raise
        LOGGER.warning(
            "project unavailable in deployment",
            extra={"project_name": resolved_project, "error": str(unavailable_error)},
        )
        if trace is not None:
            score_trace(trace=trace, name="success", value=0.0)
        raise unavailable_error from exc
    except Exception as exc:
        LOGGER.exception(
            "project run failed",
            extra={"project_name": resolved_project, "error": str(exc)},
        )
        if trace is not None:
            score_trace(trace=trace, name="success", value=0.0)
        raise
    finally:
        # ``langfuse_flush()`` synchronously drains the event queue over the
        # network.  Running it in the request-serving thread added 100 ms–
        # several seconds per request when Langfuse was enabled.  Offload it
        # to a daemon thread so the HTTP response can be sent immediately.
        _fire_and_forget_langfuse_flush()
        reset_step_emitter(emitter_token)
        reset_log_context(tokens)


def _fire_and_forget_langfuse_flush() -> None:
    """Enqueue a Langfuse flush on the shared background worker.

    A single long-lived daemon thread consumes flush requests from a bounded
    queue.  The previous implementation spawned one ``threading.Thread`` per
    request, which created unbounded thread churn under concurrency (each
    thread costs ~2 MB of stack + GIL contention during flush).  Flush
    failures must never surface as a request error — they are pure telemetry
    loss and are swallowed at the worker level.
    """

    try:
        _LANGFUSE_FLUSH_QUEUE.put_nowait(None)
    except queue.Full:
        # A flush is already pending; coalesce this one into it.
        pass


def _langfuse_flush_worker() -> None:
    while True:
        _LANGFUSE_FLUSH_QUEUE.get()
        try:
            langfuse_flush()
        except Exception:  # pragma: no cover — telemetry must not break runs.
            LOGGER.debug("langfuse flush failed in background worker", exc_info=True)


_LANGFUSE_FLUSH_QUEUE: "queue.Queue[None]" = queue.Queue(maxsize=1)
_LANGFUSE_FLUSH_WORKER = threading.Thread(
    target=_langfuse_flush_worker,
    name="langfuse-flush-worker",
    daemon=True,
)
_LANGFUSE_FLUSH_WORKER.start()
