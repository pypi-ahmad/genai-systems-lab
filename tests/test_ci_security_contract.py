"""Regression tests for the CI security / dependency contract.

The audit flagged missing security scanning and dependency hygiene.  The
pipeline now runs ``pip-audit``, ``bandit``, ``gitleaks`` (with a repo-local
config), ``npm audit``, and Trivy against the built Docker image, and
Dependabot tracks pip, npm, docker, and github-actions ecosystems.  These
tests pin that surface so a future workflow edit cannot silently drop a gate.
"""

from __future__ import annotations

from pathlib import Path

import pytest

try:
    import yaml  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover — PyYAML is a runtime dep, but be defensive
    yaml = None  # type: ignore[assignment]

REPO_ROOT = Path(__file__).resolve().parent.parent
CI_YAML = REPO_ROOT / ".github" / "workflows" / "ci.yml"
DEPENDABOT_YAML = REPO_ROOT / ".github" / "dependabot.yml"
GITLEAKS_CONFIG = REPO_ROOT / ".github" / "gitleaks.toml"


@pytest.fixture(scope="module")
def ci_text() -> str:
    return CI_YAML.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def dependabot_cfg() -> dict:
    if yaml is None:
        pytest.skip("PyYAML not available")
    return yaml.safe_load(DEPENDABOT_YAML.read_text(encoding="utf-8"))


# --- CI security gates -----------------------------------------------------


def test_ci_has_pip_audit_strict(ci_text: str) -> None:
    assert "pip-audit" in ci_text
    assert "--strict" in ci_text, "pip-audit must run in --strict mode to fail on CVEs"


def test_ci_has_bandit_static_analysis(ci_text: str) -> None:
    assert "bandit" in ci_text.lower()


def test_ci_has_gitleaks_secret_scanner(ci_text: str) -> None:
    assert "gitleaks/gitleaks-action" in ci_text


def test_ci_has_npm_audit_for_portfolio(ci_text: str) -> None:
    assert "npm audit" in ci_text


def test_ci_has_trivy_image_scan(ci_text: str) -> None:
    assert "aquasecurity/trivy-action" in ci_text
    # Critical/High must fail the build.
    assert "CRITICAL" in ci_text
    assert "HIGH" in ci_text


def test_ci_blocks_on_pip_audit_findings(ci_text: str) -> None:
    """``pip-audit`` must not be annotated with ``continue-on-error: true``."""
    lines = ci_text.splitlines()
    for idx, line in enumerate(lines):
        if "pip-audit" not in line or "run:" not in line:
            continue
        # Scan forward only within this step — stop at the next ``- name:``.
        step_lines: list[str] = []
        for follow in lines[idx + 1 :]:
            if follow.lstrip().startswith("- name:"):
                break
            step_lines.append(follow)
        tail = "\n".join(step_lines)
        assert "continue-on-error: true" not in tail, (
            "pip-audit must be a blocking gate"
        )


def test_ci_blocks_on_trivy_findings(ci_text: str) -> None:
    """Trivy image scan must have ``exit-code: \"1\"`` so CVEs fail the job."""
    # A light structural check: find the Trivy block and assert exit-code: "1"
    # is set somewhere within it.
    idx = ci_text.find("aquasecurity/trivy-action")
    assert idx != -1
    tail = ci_text[idx : idx + 400]
    assert 'exit-code: "1"' in tail, "Trivy must fail the build on findings"


# --- Gitleaks config -------------------------------------------------------


def test_gitleaks_config_file_exists_where_ci_expects_it() -> None:
    assert GITLEAKS_CONFIG.is_file(), (
        ".github/gitleaks.toml must exist — ci.yml references it via "
        "``config-path: .github/gitleaks.toml``"
    )


def test_gitleaks_config_extends_default_ruleset() -> None:
    text = GITLEAKS_CONFIG.read_text(encoding="utf-8")
    # ``useDefault = true`` pulls in the upstream ~100-rule baseline;
    # without it a bare custom config would weaken the scanner.
    assert "useDefault = true" in text


# --- Dependabot coverage ---------------------------------------------------


def test_dependabot_covers_all_first_class_ecosystems(dependabot_cfg: dict) -> None:
    ecosystems = {
        entry["package-ecosystem"]
        for entry in dependabot_cfg.get("updates", [])
    }
    assert "pip" in ecosystems, "Python deps must be tracked"
    assert "npm" in ecosystems, "portfolio (Next.js) deps must be tracked"
    assert "docker" in ecosystems, "Dockerfile base image must be tracked"
    assert "github-actions" in ecosystems, "workflow action refs must be tracked"


def test_dependabot_covers_standalone_analyst(dependabot_cfg: dict) -> None:
    """``langgraph-data-analyst/`` has its own requirements.txt — Dependabot
    must pick it up separately from the root pip entry."""
    pip_dirs = {
        entry.get("directory")
        for entry in dependabot_cfg.get("updates", [])
        if entry.get("package-ecosystem") == "pip"
    }
    assert "/langgraph-data-analyst" in pip_dirs


def test_dependabot_weekly_cadence_is_sane(dependabot_cfg: dict) -> None:
    for entry in dependabot_cfg.get("updates", []):
        schedule = entry.get("schedule", {})
        # ``interval`` must be set and conservative (weekly/daily/monthly).
        assert schedule.get("interval") in {"daily", "weekly", "monthly"}
