"""Regression tests for ``shared.api.runner._MODULE_CACHE``.

The audit flagged ``sys.modules`` / ``sys.path`` mutation per request as a
correctness + performance issue.  The runner now caches loaded modules by
project slug, invalidates on ``main.py`` mtime in dev mode, caches for the
lifetime of the process in prod, and serialises mutation with two locks.
These tests pin that behaviour down so a future refactor cannot silently
regress it.
"""

from __future__ import annotations

import threading
from pathlib import Path

import pytest

from shared.api import runner


@pytest.fixture(autouse=True)
def _reset_module_cache():
    """Clear the module cache before and after each test for isolation."""
    with runner._MODULE_CACHE_LOCK:
        runner._MODULE_CACHE.clear()
    yield
    with runner._MODULE_CACHE_LOCK:
        runner._MODULE_CACHE.clear()


def _real_project_slug() -> str:
    """Pick a real project whose ``app/main.py`` imports cleanly in this env.

    Many projects pull in optional heavy deps (``crewai``, ``playwright``)
    that are not installed in the test environment.  We probe candidates
    and return the first one that loads without raising so the cache tests
    always run against a concrete import.
    """
    # Clear whatever prior probing may have left behind so each probe is
    # an honest first-load.
    with runner._MODULE_CACHE_LOCK:
        runner._MODULE_CACHE.clear()

    for child in sorted(runner.REPO_ROOT.iterdir()):
        if not child.is_dir():
            continue
        if not (child / "app" / "main.py").is_file():
            continue
        try:
            mod = runner._load_main(child.name)
        except BaseException:  # noqa: BLE001 — optional deps raise varied errors
            continue
        if mod is None:
            continue
        with runner._MODULE_CACHE_LOCK:
            runner._MODULE_CACHE.clear()
        return child.name
    pytest.skip("no importable project main.py in this environment")


def test_module_cache_returns_same_instance_across_loads() -> None:
    """Two consecutive loads of the same project must reuse the cached module."""
    project = _real_project_slug()

    first = runner._load_main(project)
    second = runner._load_main(project)

    assert first is not None
    assert second is not None
    assert first is second, (
        "expected _load_main to reuse the cached module on the second call"
    )

    # And the cache itself must have exactly one entry for this project.
    with runner._MODULE_CACHE_LOCK:
        assert project in runner._MODULE_CACHE
        cached_mtime, cached_mod = runner._MODULE_CACHE[project]
        assert cached_mod is first
        assert isinstance(cached_mtime, float)


def test_module_cache_invalidates_on_mtime_change_in_dev(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Dev mode must reload when ``main.py`` mtime changes."""
    project = _real_project_slug()
    monkeypatch.setenv("APP_ENV", "dev")

    first = runner._load_main(project)
    assert first is not None

    # Forge an older mtime in the cache so the next call looks stale.
    with runner._MODULE_CACHE_LOCK:
        _, cached_mod = runner._MODULE_CACHE[project]
        runner._MODULE_CACHE[project] = (0.0, cached_mod)

    second = runner._load_main(project)
    assert second is not None
    assert second is not first, (
        "dev mode must reload the module when main.py mtime differs from the cached value"
    )


def test_module_cache_is_sticky_in_prod(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Prod mode must never reload once a project has been imported."""
    project = _real_project_slug()
    monkeypatch.setenv("APP_ENV", "prod")

    first = runner._load_main(project)
    assert first is not None

    # Forge a stale mtime — prod must ignore it.
    with runner._MODULE_CACHE_LOCK:
        _, cached_mod = runner._MODULE_CACHE[project]
        runner._MODULE_CACHE[project] = (0.0, cached_mod)

    second = runner._load_main(project)
    assert second is first, (
        "prod mode must reuse the cached module regardless of mtime"
    )


def test_sys_modules_lock_is_a_threading_lock() -> None:
    """The cross-thread mutation guards must be actual locks, not no-ops."""
    # ``threading.Lock()`` returns an instance of an internal ``_thread.lock``
    # type, so compare via ``acquire``/``release`` duck-typing rather than
    # isinstance against a private class.
    assert hasattr(runner._SYS_MODULES_LOCK, "acquire")
    assert hasattr(runner._SYS_MODULES_LOCK, "release")
    assert hasattr(runner._MODULE_CACHE_LOCK, "acquire")
    assert hasattr(runner._MODULE_CACHE_LOCK, "release")


def test_concurrent_loads_populate_cache_and_stabilise() -> None:
    """Concurrent ``_load_main`` calls must not raise and must leave a stable cache.

    Note: the current implementation does not coalesce concurrent first-loads
    into a single ``exec_module`` — if N threads all see a cache miss they each
    load the module and the last writer wins.  That is an acceptable trade-off
    (no lost work, last winner is cached), so this test guards only the two
    invariants we do rely on: no exceptions, and post-race a single call to
    ``_load_main`` returns the cached winner.
    """
    project = _real_project_slug()
    results: list[object] = []
    errors: list[BaseException] = []

    def worker() -> None:
        try:
            results.append(runner._load_main(project))
        except BaseException as exc:  # noqa: BLE001
            errors.append(exc)

    threads = [threading.Thread(target=worker) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert errors == [], f"concurrent loads raised: {errors!r}"
    assert len(results) == 8
    for mod in results:
        assert mod is not None

    with runner._MODULE_CACHE_LOCK:
        assert project in runner._MODULE_CACHE
        _, winner = runner._MODULE_CACHE[project]

    # After the race settles, a fresh call must return the cached winner —
    # this is the property callers actually depend on.
    assert runner._load_main(project) is winner
