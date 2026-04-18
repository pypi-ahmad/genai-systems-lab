"""Focused tests for the PyJWT-based ``create_access_token`` / ``decode_access_token``.

Covers the contract we care about after swapping the hand-rolled HS256
encoder for PyJWT: valid tokens round-trip, expired tokens are rejected,
malformed input raises ``AuthError``, and tampering with any segment
(signature, payload, header algorithm) is detected.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

import jwt
import pytest

from shared.api.auth import (
    AuthError,
    JWT_ALGORITHM,
    JWT_SECRET,
    _JWT_LEEWAY_SECONDS,
    create_access_token,
    decode_access_token,
)


@dataclass
class _StubUser:
    id: int
    email: str


@pytest.fixture()
def user() -> _StubUser:
    return _StubUser(id=42, email="alice@example.com")


def test_valid_token_round_trips_claims(user: _StubUser) -> None:
    token = create_access_token(user)
    payload = decode_access_token(token)

    assert payload["sub"] == "42"
    assert payload["email"] == "alice@example.com"
    assert "iat" in payload and "nbf" in payload and "exp" in payload
    assert payload["exp"] > payload["iat"]


def test_expired_token_is_rejected(user: _StubUser, monkeypatch: pytest.MonkeyPatch) -> None:
    # Force an ``exp`` well outside the leeway window so the test is not flaky.
    now = int(time.time())
    payload = {
        "sub": str(user.id),
        "email": user.email,
        "iat": now - 3600,
        "nbf": now - 3600,
        "exp": now - (_JWT_LEEWAY_SECONDS + 60),
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    with pytest.raises(AuthError, match="expired"):
        decode_access_token(token)


def test_malformed_token_is_rejected() -> None:
    for bad in ("", "not-a-jwt", "only.two", "a.b.c.d", "!!!..!!!"):
        with pytest.raises(AuthError):
            decode_access_token(bad)


def test_non_string_token_is_rejected() -> None:
    with pytest.raises(AuthError, match="Malformed"):
        decode_access_token(None)  # type: ignore[arg-type]


def test_tampered_payload_fails_signature_check(user: _StubUser) -> None:
    token = create_access_token(user)
    header, payload_segment, signature = token.split(".")
    # Re-sign nothing — just flip a character in the payload segment.  The
    # original signature no longer matches.
    flipped_char = "A" if payload_segment[0] != "A" else "B"
    tampered = f"{header}.{flipped_char}{payload_segment[1:]}.{signature}"

    with pytest.raises(AuthError, match="signature|Malformed"):
        decode_access_token(tampered)


def test_tampered_signature_is_rejected(user: _StubUser) -> None:
    token = create_access_token(user)
    header, payload_segment, signature = token.split(".")
    # Swap the first char of the signature (keeping it base64url-decodable).
    flipped = "A" if signature[0] != "A" else "B"
    tampered = f"{header}.{payload_segment}.{flipped}{signature[1:]}"

    with pytest.raises(AuthError, match="signature"):
        decode_access_token(tampered)


def test_alg_none_is_rejected(user: _StubUser) -> None:
    """Defence against the classic JWT ``alg: none`` downgrade attack."""
    payload = {
        "sub": str(user.id),
        "email": user.email,
        "iat": int(time.time()),
        "nbf": int(time.time()),
        "exp": int(time.time()) + 60,
    }
    # PyJWT refuses to encode ``alg=none`` without an explicit opt-in, so
    # build the token manually.
    import base64
    import json

    def _b64(data: bytes) -> str:
        return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")

    header_b64 = _b64(json.dumps({"alg": "none", "typ": "JWT"}).encode("utf-8"))
    payload_b64 = _b64(json.dumps(payload).encode("utf-8"))
    token = f"{header_b64}.{payload_b64}."

    with pytest.raises(AuthError):
        decode_access_token(token)


def test_missing_required_claim_is_rejected() -> None:
    """Tokens that skip ``exp``/``nbf``/``iat``/``sub`` must not validate."""
    now = int(time.time())
    # Omit ``sub`` entirely.
    payload = {"email": "x@y.z", "iat": now, "nbf": now, "exp": now + 60}
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    with pytest.raises(AuthError, match="Missing required claim"):
        decode_access_token(token)


def test_wrong_secret_is_rejected(user: _StubUser) -> None:
    payload = {
        "sub": str(user.id),
        "email": user.email,
        "iat": int(time.time()),
        "nbf": int(time.time()),
        "exp": int(time.time()) + 60,
    }
    token = jwt.encode(payload, JWT_SECRET + "-different", algorithm=JWT_ALGORITHM)

    with pytest.raises(AuthError, match="signature"):
        decode_access_token(token)
