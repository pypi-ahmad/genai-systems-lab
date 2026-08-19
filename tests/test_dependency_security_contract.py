"""Regression checks for the production dependency security boundary."""

from __future__ import annotations

from pathlib import Path

from packaging.version import Version

REPO_ROOT = Path(__file__).resolve().parent.parent

# Known-patched floors for direct dependencies that previously shipped with
# disclosed vulnerabilities. These are *minimum* versions, not pins: any
# resolved version at or above the floor keeps the vulnerable release out of
# the dependency tree, so routine upgrades (e.g. via Dependabot) must keep
# passing these checks rather than requiring an exact-match bump every time.
STARLETTE_PATCHED_FLOOR = Version("1.3.1")
PYJWT_PATCHED_FLOOR = Version("2.13.0")
PYTHON_DOTENV_PATCHED_FLOOR = Version("1.2.2")
LANGCHAIN_PATCHED_FLOOR = Version("1.3.14")
LANGCHAIN_CORE_PATCHED_FLOOR = Version("1.5.0")


def _active_requirements(path: Path) -> set[str]:
    return {
        line.strip().lower()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }


def _resolved_version(requirements: set[str], package: str) -> Version:
    """Return the pinned ``==`` version for ``package`` in ``requirements``.

    Raises ``AssertionError`` (via the final call) if the package is not
    pinned with ``==``, so a dependency that becomes unpinned or is removed
    fails loudly instead of silently skipping the security check.
    """
    prefix = f"{package.lower()}=="
    for line in requirements:
        if line.startswith(prefix):
            return Version(line[len(prefix) :])
    raise AssertionError(f"{package!r} is not pinned with '==' in requirements")


def test_production_requirements_use_patched_direct_dependencies() -> None:
    requirements = _active_requirements(REPO_ROOT / "requirements.txt")

    assert _resolved_version(requirements, "starlette") >= STARLETTE_PATCHED_FLOOR
    assert _resolved_version(requirements, "pyjwt") >= PYJWT_PATCHED_FLOOR
    assert (
        _resolved_version(requirements, "python-dotenv")
        >= PYTHON_DOTENV_PATCHED_FLOOR
    )
    assert not any(line.startswith("crewai") for line in requirements)


def test_standalone_api_uses_patched_starlette() -> None:
    requirements = _active_requirements(
        REPO_ROOT / "langgraph-data-analyst" / "requirements.txt"
    )

    assert _resolved_version(requirements, "starlette") >= STARLETTE_PATCHED_FLOOR
    assert _resolved_version(requirements, "langchain") >= LANGCHAIN_PATCHED_FLOOR
    assert (
        _resolved_version(requirements, "langchain-core")
        >= LANGCHAIN_CORE_PATCHED_FLOOR
    )


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
