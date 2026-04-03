from __future__ import annotations

import importlib.util
import json
import os
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Generator


_REPO_ROOT = Path(__file__).resolve().parents[3]
_PROVIDER_DIR = Path(__file__).resolve().parent

for candidate in (str(_PROVIDER_DIR), str(_REPO_ROOT)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from shared.config import (  # noqa: E402
    reset_byok_api_key,
    reset_request_model,
    reset_request_provider,
    set_byok_api_key,
    set_request_model,
    set_request_provider,
)
from shared.llm.catalog import infer_provider  # noqa: E402


def repository_root() -> Path:
    return _REPO_ROOT


def resolve_path(path_value: str | os.PathLike[str] | None) -> Path:
    if not path_value:
        return _REPO_ROOT

    candidate = Path(path_value)
    if not candidate.is_absolute():
        candidate = _REPO_ROOT / candidate
    return candidate.resolve()


def repo_relative_path(path_value: str | os.PathLike[str]) -> str:
    try:
        return str(Path(path_value).resolve().relative_to(_REPO_ROOT)).replace("\\", "/")
    except Exception:
        return str(path_value).replace("\\", "/")


def _clear_project_imports() -> None:
    module_names = [name for name in sys.modules if name == "app" or name.startswith("app.")]
    for module_name in module_names:
        sys.modules.pop(module_name, None)


def load_project_module(project: str):
    main_path = _REPO_ROOT / project / "app" / "main.py"
    if not main_path.is_file():
        raise FileNotFoundError(f"Missing entrypoint for project '{project}'.")

    project_dir = str(_REPO_ROOT / project)
    if project_dir not in sys.path:
        sys.path.insert(0, project_dir)

    _clear_project_imports()

    spec = importlib.util.spec_from_file_location(
        f"promptfoo_{project.replace('-', '_')}.app.main",
        str(main_path),
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load main module for project '{project}'.")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def normalize_provider(provider: Any, model: Any = None) -> str | None:
    provider_text = str(provider or "").strip().lower()
    if provider_text:
        return "gemini" if provider_text == "google" else provider_text

    model_text = str(model or "").strip()
    if not model_text:
        return None
    return infer_provider(model_text)


def resolve_api_key(config: dict[str, Any]) -> str:
    explicit = str(config.get("api_key") or "").strip()
    if explicit:
        return explicit

    provider = normalize_provider(config.get("provider"), config.get("model"))
    if provider == "ollama":
        return ""

    env_name_map = {
        "gemini": "GOOGLE_API_KEY",
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
    }
    if provider in env_name_map:
        return os.getenv(env_name_map[provider], "").strip()

    for env_name in ("GOOGLE_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"):
        value = os.getenv(env_name, "").strip()
        if value:
            return value
    return ""


@contextmanager
def request_overrides(config: dict[str, Any]) -> Generator[dict[str, str | None], None, None]:
    api_key = resolve_api_key(config)
    provider = normalize_provider(config.get("provider"), config.get("model"))
    model = str(config.get("model") or "").strip() or None

    api_key_token = set_byok_api_key(api_key or None)
    provider_token = set_request_provider(provider)
    model_token = set_request_model(model)
    try:
        yield {
            "api_key": api_key,
            "provider": provider,
            "model": model,
        }
    finally:
        reset_request_model(model_token)
        reset_request_provider(provider_token)
        reset_byok_api_key(api_key_token)


def parse_output_payload(raw_output: str) -> Any:
    try:
        return json.loads(raw_output)
    except Exception:
        return raw_output


def extract_primary_text(payload: Any) -> str:
    if isinstance(payload, str):
        return payload

    if isinstance(payload, list):
        parts = [extract_primary_text(item) for item in payload]
        return "\n\n".join(part for part in parts if part.strip())

    if not isinstance(payload, dict):
        return json.dumps(payload, indent=2, default=str)

    for key in ("answer", "summary", "report", "analysis", "output", "sql", "text"):
        value = payload.get(key)
        if value is None:
            continue
        candidate = extract_primary_text(value)
        if candidate.strip():
            return candidate

    results = payload.get("results")
    if isinstance(results, dict):
        joined = "\n\n".join(str(value).strip() for value in results.values() if str(value).strip())
        if joined:
            return joined

    return json.dumps(payload, indent=2, default=str)