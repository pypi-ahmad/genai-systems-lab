"""Tests for auth secret hardening — minimum length, prod enforcement, ephemeral fallback."""

from __future__ import annotations

import pytest


def test_short_jwt_secret_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GENAI_SYSTEMS_LAB_JWT_SECRET", "tooshort")  # 8 chars

    from shared.api.auth import _load_jwt_secret

    with pytest.raises(RuntimeError, match="too short"):
        _load_jwt_secret()


def test_minimum_length_jwt_secret_is_accepted(monkeypatch: pytest.MonkeyPatch) -> None:
    secret = "a" * 16
    monkeypatch.setenv("GENAI_SYSTEMS_LAB_JWT_SECRET", secret)

    from shared.api.auth import _load_jwt_secret

    assert _load_jwt_secret() == secret


def test_missing_secret_in_prod_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GENAI_SYSTEMS_LAB_JWT_SECRET", raising=False)
    monkeypatch.setenv("APP_ENV", "prod")

    from shared.api.auth import _load_jwt_secret

    with pytest.raises(RuntimeError, match="must be set to a strong value"):
        _load_jwt_secret()


def test_missing_secret_in_dev_returns_ephemeral(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GENAI_SYSTEMS_LAB_JWT_SECRET", raising=False)
    monkeypatch.setenv("APP_ENV", "dev")

    from shared.api.auth import _load_jwt_secret, _EPHEMERAL_DEV_JWT_SECRET

    result = _load_jwt_secret()
    assert result == _EPHEMERAL_DEV_JWT_SECRET
    assert len(result) >= 32  # secrets.token_urlsafe(48) produces ~64 chars


def test_missing_secret_in_dev_logs_ephemeral_warning(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    monkeypatch.delenv("GENAI_SYSTEMS_LAB_JWT_SECRET", raising=False)
    monkeypatch.setenv("APP_ENV", "dev")

    from shared.api.auth import _load_jwt_secret

    with caplog.at_level("WARNING"):
        _load_jwt_secret()

    assert "using an ephemeral secret" in caplog.text
    assert "Auth tokens will not survive process restarts" in caplog.text


def test_whitespace_only_secret_treated_as_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GENAI_SYSTEMS_LAB_JWT_SECRET", "   ")
    monkeypatch.setenv("APP_ENV", "dev")

    from shared.api.auth import _load_jwt_secret, _EPHEMERAL_DEV_JWT_SECRET

    assert _load_jwt_secret() == _EPHEMERAL_DEV_JWT_SECRET
