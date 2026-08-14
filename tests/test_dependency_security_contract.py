"""Regression checks for the production dependency security boundary."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _active_requirements(path: Path) -> set[str]:
    return {
        line.strip().lower()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }


def test_production_requirements_use_patched_direct_dependencies() -> None:
    requirements = _active_requirements(REPO_ROOT / "requirements.txt")

    assert "starlette==1.3.1" in requirements
    assert "pyjwt==2.13.0" in requirements
    assert "python-dotenv==1.2.2" in requirements
    assert not any(line.startswith("crewai") for line in requirements)


def test_standalone_api_uses_patched_starlette() -> None:
    requirements = _active_requirements(
        REPO_ROOT / "langgraph-data-analyst" / "requirements.txt"
    )

    assert "starlette==1.3.1" in requirements
    assert "langchain==1.3.14" in requirements
    assert "langchain-core==1.5.0" in requirements


def test_security_scans_do_not_suppress_dependency_advisories() -> None:
    workflow = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(
        encoding="utf-8"
    )

    assert "--ignore-vuln" not in workflow


def test_secret_scan_loads_the_repository_configuration() -> None:
    workflow = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(
        encoding="utf-8"
    )

    assert "GITLEAKS_CONFIG: .github/gitleaks.toml" in workflow
    assert "config-path:" not in workflow


def test_runtime_image_removes_build_only_package_managers() -> None:
    dockerfile = (REPO_ROOT / "Dockerfile").read_text(encoding="utf-8")

    assert "pip uninstall --yes pip setuptools" in dockerfile
