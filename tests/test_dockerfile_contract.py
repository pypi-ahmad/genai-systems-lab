"""Regression tests for Dockerfile secret-handling and project-copy correctness.

The audit flagged two concerns:
  1. ``.env`` files being baked into the image.
  2. Project directories being flattened by glob ``COPY crew-*/ ./`` lines.

Both are fixed — ``.dockerignore`` excludes ``.env`` and ``.env.*``, and the
Dockerfile copies each project into its own sub-directory.  These tests pin
that state so a future refactor cannot silently regress either invariant.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCKERFILE = REPO_ROOT / "Dockerfile"
DOCKERIGNORE = REPO_ROOT / ".dockerignore"


@pytest.fixture(scope="module")
def dockerfile_text() -> str:
    return DOCKERFILE.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def dockerignore_text() -> str:
    return DOCKERIGNORE.read_text(encoding="utf-8")


def _active_lines(text: str) -> list[str]:
    """Strip comments and blank lines — we only care about live directives."""
    out: list[str] = []
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if line:
            out.append(line)
    return out


# --- .dockerignore invariants ---------------------------------------------


def test_dockerignore_excludes_env_files(dockerignore_text: str) -> None:
    lines = set(_active_lines(dockerignore_text))
    assert ".env" in lines, ".dockerignore must exclude plain .env"
    assert ".env.*" in lines, ".dockerignore must exclude .env.* (per-env files)"


def test_dockerignore_excludes_sqlite_and_data_dir(dockerignore_text: str) -> None:
    lines = set(_active_lines(dockerignore_text))
    # Prevent local dev DBs from being shipped into images.
    assert ".data/" in lines
    assert "*.sqlite" in lines
    assert "*.sqlite3" in lines
    assert "*.db" in lines


def test_dockerignore_excludes_git_and_venvs(dockerignore_text: str) -> None:
    lines = set(_active_lines(dockerignore_text))
    assert ".git/" in lines
    assert ".venv/" in lines
    assert "venv/" in lines


# --- Dockerfile invariants -------------------------------------------------


def test_dockerfile_does_not_copy_env_files(dockerfile_text: str) -> None:
    for raw in dockerfile_text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line.upper().startswith("COPY"):
            continue
        # Reject any COPY that mentions a .env source (case-insensitive).
        # ``.env.example`` would also be caught here; today the Dockerfile
        # does not copy it, and if someone ever wants to they must do so
        # explicitly with a narrowly-targeted COPY and update this test.
        assert ".env" not in line.lower(), (
            f"Dockerfile must not COPY .env files: {line!r}"
        )


def test_dockerfile_does_not_flatten_projects_via_globs(dockerfile_text: str) -> None:
    """Historical bug: ``COPY crew-*/ ./`` merges every project's files into /app.

    The fix is one ``COPY <slug>/ ./<slug>/`` per project so structure is
    preserved.  This test rejects any COPY that targets ``./`` as a directory
    and sources from a wildcard project glob.
    """
    offending = re.compile(
        r"^\s*COPY\s+(?:--\S+\s+)*"  # optional flags (e.g. --chown)
        r"(?:crew-\*|genai-\*|lg-\*)[^\s]*\s+\./\s*$",
        re.IGNORECASE,
    )
    for raw in dockerfile_text.splitlines():
        line = raw.split("#", 1)[0]
        assert not offending.match(line), (
            f"Dockerfile uses a flattening wildcard COPY: {line!r}"
        )


def test_dockerfile_copies_each_project_into_its_own_subdir(dockerfile_text: str) -> None:
    """Every runnable project must land under ``/app/<slug>/``, not ``/app``."""
    project_slugs = sorted(
        child.name
        for child in REPO_ROOT.iterdir()
        if child.is_dir()
        and child.name.startswith(("crew-", "genai-", "lg-"))
        and (child / "app" / "main.py").is_file()
    )
    # Sanity: we must find at least a handful of projects, otherwise the
    # test is silently vacuous.
    assert len(project_slugs) >= 10, f"only found {len(project_slugs)} projects"

    # Build a per-slug regex: ``COPY [--flags] <slug>/ ./<slug>/``
    for slug in project_slugs:
        pattern = re.compile(
            rf"^\s*COPY\s+(?:--\S+\s+)*{re.escape(slug)}/\s+\./{re.escape(slug)}/\s*$",
            re.IGNORECASE,
        )
        assert any(pattern.match(raw) for raw in dockerfile_text.splitlines()), (
            f"Dockerfile is missing a preserving COPY for project {slug!r}"
        )


def test_dockerfile_runs_as_non_root(dockerfile_text: str) -> None:
    # Final ``USER`` directive must be the non-root app user.  This is a
    # longstanding invariant the secret-handling fix relies on (keys never
    # written to a root-owned filesystem layer).
    user_lines = [
        line.split("#", 1)[0].strip()
        for line in dockerfile_text.splitlines()
        if line.strip().upper().startswith("USER ")
    ]
    assert user_lines, "Dockerfile must declare a USER directive"
    assert user_lines[-1].split()[1] == "app", (
        f"final USER must be 'app', got {user_lines[-1]!r}"
    )
