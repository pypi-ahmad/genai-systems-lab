"""Authentication helpers for the shared API."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import logging
import secrets
import time
from pathlib import Path
from typing import Any

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from .db import DATA_DIR, get_db_session
from .models import Run, User


def _load_or_create_persistent_dev_secret() -> str:
    """Return a stable dev secret shared across uvicorn workers.

    When no secret is configured and ``APP_ENV=dev``, multiple workers would
    otherwise each generate their own ephemeral secret, causing tokens issued
    by worker A to be rejected by worker B.  A file under the data directory
    provides a consistent secret for the duration of a developer's machine
    session while still being regenerated if deleted.
    """
    try:
        secret_path = Path(DATA_DIR) / ".dev_jwt_secret"
        if secret_path.is_file():
            value = secret_path.read_text(encoding="utf-8").strip()
            if len(value) >= 32:
                return value
        value = secrets.token_urlsafe(48)
        secret_path.write_text(value, encoding="utf-8")
        try:
            os.chmod(secret_path, 0o600)
        except OSError:
            pass
        return value
    except OSError:
        # Read-only filesystem (e.g. serverless) — fall back to a process-local
        # ephemeral secret.  This preserves the existing dev-mode semantics.
        return secrets.token_urlsafe(48)


# Module-level dev fallback.  Preserves the pre-audit name/contract for tests
# (``_EPHEMERAL_DEV_JWT_SECRET``) while actually persisting the value across
# workers and restarts when the filesystem allows it.
_EPHEMERAL_DEV_JWT_SECRET = _load_or_create_persistent_dev_secret()

JWT_ALGORITHM = "HS256"
AUTH_COOKIE_NAME = os.getenv("GENAI_SYSTEMS_LAB_AUTH_COOKIE_NAME", "genai_systems_lab_session")
_DEFAULT_JWT_TTL_SECONDS = 60 * 60 * 24 * 7
# OWASP 2023+ recommends at least 600_000 iterations of PBKDF2-HMAC-SHA256.
# Argon2id remains preferred; migration path documented in HI-11 of the audit.
PBKDF2_ITERATIONS = 600_000
# Small leeway so mild clock skew between services does not invalidate tokens.
_JWT_LEEWAY_SECONDS = 30

_auth_logger = logging.getLogger(__name__)


# ``_EPHEMERAL_DEV_JWT_SECRET`` is computed lazily below so it can reuse the
# persistent-file loader; the name is preserved for test contract compatibility.

auth_scheme = HTTPBearer(auto_error=False)
_VALID_MEMORY_TYPES = {"thought", "action", "observation"}


class AuthError(Exception):
    """Raised when authentication fails."""


def _load_jwt_ttl_seconds() -> int:
    raw_value = os.getenv("GENAI_SYSTEMS_LAB_JWT_TTL_SECONDS", str(_DEFAULT_JWT_TTL_SECONDS)).strip()
    try:
        ttl_seconds = int(raw_value)
    except ValueError:
        return _DEFAULT_JWT_TTL_SECONDS
    return max(300, ttl_seconds)


def _load_jwt_secret() -> str:
    configured_secret = os.getenv("GENAI_SYSTEMS_LAB_JWT_SECRET", "").strip()
    environment = os.getenv("APP_ENV", "dev").strip().lower()

    if configured_secret:
        if len(configured_secret) < 16:
            raise RuntimeError(
                "GENAI_SYSTEMS_LAB_JWT_SECRET is too short (minimum 16 characters)."
            )
        return configured_secret

    if environment == "prod":
        raise RuntimeError(
            "GENAI_SYSTEMS_LAB_JWT_SECRET must be set to a strong value when APP_ENV=prod."
        )

    _auth_logger.warning(
        "No GENAI_SYSTEMS_LAB_JWT_SECRET configured — using an ephemeral secret. "
        "Auth tokens will not survive process restarts. "
        "Set GENAI_SYSTEMS_LAB_JWT_SECRET in .env for persistent sessions."
    )
    return _EPHEMERAL_DEV_JWT_SECRET


def _allowed_jwt_algorithms() -> frozenset[str]:
    """Algorithms accepted during decode. Hardcoded to HS256 to block alg-confusion.

    Preserved for backwards compatibility; ``decode_access_token`` now passes
    the allowlist directly to :func:`jwt.decode`.
    """
    return frozenset({JWT_ALGORITHM})


JWT_SECRET = _load_jwt_secret()
JWT_TTL_SECONDS = _load_jwt_ttl_seconds()


def _b64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _b64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def hash_password(password: str) -> str:
    """Hash a password using PBKDF2-HMAC-SHA256."""
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return "pbkdf2_sha256${iterations}${salt}${digest}".format(
        iterations=PBKDF2_ITERATIONS,
        salt=_b64url_encode(salt),
        digest=_b64url_encode(digest),
    )


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against the stored PBKDF2 hash."""
    try:
        algorithm, iterations_raw, salt_raw, digest_raw = password_hash.split("$", 3)
    except ValueError:
        return False

    if algorithm != "pbkdf2_sha256":
        return False

    computed = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        _b64url_decode(salt_raw),
        int(iterations_raw),
    )
    return hmac.compare_digest(_b64url_encode(computed), digest_raw)


def create_access_token(user: User) -> str:
    """Create a signed JWT for the authenticated user.

    Uses PyJWT with a hardcoded HS256 algorithm.  The payload shape
    (``sub``/``email``/``iat``/``nbf``/``exp``) is preserved so existing
    tokens in active sessions continue to decode correctly.
    """
    now = int(time.time())
    payload = {
        "sub": str(user.id),
        "email": user.email,
        "iat": now,
        "nbf": now,
        "exp": now + JWT_TTL_SECONDS,
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    # PyJWT <2.0 returned bytes; 2.x returns str, but normalise defensively.
    if isinstance(token, bytes):  # pragma: no cover — defensive, 2.x returns str
        token = token.decode("ascii")
    return token


def decode_access_token(token: str) -> dict[str, Any]:
    """Validate and decode a signed JWT.

    Delegates verification to PyJWT with an explicit ``algorithms`` allowlist
    (prevents ``alg: none`` / RS256-HS256 confusion), leeway for clock skew,
    and a ``require`` list so missing ``exp``/``nbf``/``iat`` claims are
    rejected rather than silently accepted.  All PyJWT-specific exceptions
    are mapped back to ``AuthError`` so callers see the same contract as the
    previous hand-rolled implementation.
    """
    if not isinstance(token, str):
        raise AuthError("Malformed token.")

    try:
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
            leeway=_JWT_LEEWAY_SECONDS,
            options={"require": ["exp", "nbf", "iat", "sub"]},
        )
    except jwt.ExpiredSignatureError as exc:
        raise AuthError("Token expired.") from exc
    except jwt.ImmatureSignatureError as exc:
        raise AuthError("Token not yet valid.") from exc
    except jwt.InvalidSignatureError as exc:
        raise AuthError("Invalid token signature.") from exc
    except jwt.InvalidAlgorithmError as exc:
        raise AuthError("Unsupported token algorithm.") from exc
    except jwt.MissingRequiredClaimError as exc:
        raise AuthError(f"Missing required claim: {exc.claim}.") from exc
    except jwt.DecodeError as exc:
        raise AuthError("Malformed token.") from exc
    except jwt.InvalidTokenError as exc:
        raise AuthError("Invalid token.") from exc

    if not isinstance(payload, dict):
        raise AuthError("Malformed token payload.")

    return payload


def authenticate_user(session: Session, email: str, password: str) -> User | None:
    """Return the matching user when credentials are valid.

    Email is normalised (lowercased + stripped) but passwords are used *exactly
    as provided* — silently stripping whitespace from passwords creates a
    silent auth failure mode for users who intentionally include it.
    """
    normalized_email = email.strip().lower()
    user = session.scalar(select(User).where(User.email == normalized_email))
    if user is None or not verify_password(password, user.password_hash):
        return None
    return user


def create_user(session: Session, email: str, password: str) -> User:
    """Persist a new user account."""
    user = User(email=email.strip().lower(), password_hash=hash_password(password))
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def _serialize_memory_entries(memory: list[dict[str, str]] | None) -> str:
    if not memory:
        return "[]"

    cleaned: list[dict[str, str]] = []
    for entry in memory:
        step = entry.get("step")
        content = entry.get("content")
        entry_type = entry.get("type")
        if not isinstance(step, str) or not isinstance(content, str) or not isinstance(entry_type, str):
            continue
        if entry_type not in _VALID_MEMORY_TYPES:
            continue
        cleaned.append({
            "step": step,
            "content": content,
            "type": entry_type,
        })

    return json.dumps(cleaned, separators=(",", ":"))


def _deserialize_memory_entries(raw: str | None) -> list[dict[str, str]]:
    if not raw:
        return []

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        # Treat corrupted rows as empty rather than crashing the request, but
        # log loudly so we notice data drift instead of silently returning [].
        _auth_logger.warning(
            "failed to decode memory entries json (len=%d): %s",
            len(raw),
            exc,
        )
        return []

    if not isinstance(payload, list):
        return []

    cleaned: list[dict[str, str]] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        step = item.get("step")
        content = item.get("content")
        entry_type = item.get("type")
        if not isinstance(step, str) or not isinstance(content, str) or not isinstance(entry_type, str):
            continue
        if entry_type not in _VALID_MEMORY_TYPES:
            continue
        cleaned.append({
            "step": step,
            "content": content,
            "type": entry_type,
        })

    return cleaned


def _serialize_timeline_entries(timeline: list[dict[str, Any]] | None) -> str:
    if not timeline:
        return "[]"

    cleaned: list[dict[str, Any]] = []
    for entry in timeline:
        timestamp = entry.get("timestamp")
        step = entry.get("step")
        event = entry.get("event")
        data = entry.get("data")
        if not isinstance(timestamp, (int, float)):
            continue
        if not isinstance(step, str) or not isinstance(event, str) or not isinstance(data, str):
            continue
        cleaned.append({
            "timestamp": round(float(timestamp), 4),
            "step": step,
            "event": event,
            "data": data,
        })

    return json.dumps(cleaned, separators=(",", ":"))


def _deserialize_timeline_entries(raw: str | None) -> list[dict[str, Any]]:
    if not raw:
        return []

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        _auth_logger.warning(
            "failed to decode timeline entries json (len=%d): %s",
            len(raw),
            exc,
        )
        return []

    if not isinstance(payload, list):
        return []

    cleaned: list[dict[str, Any]] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        timestamp = item.get("timestamp")
        step = item.get("step")
        event = item.get("event")
        data = item.get("data")
        if not isinstance(timestamp, (int, float)):
            continue
        if not isinstance(step, str) or not isinstance(event, str) or not isinstance(data, str):
            continue
        cleaned.append({
            "timestamp": round(float(timestamp), 4),
            "step": step,
            "event": event,
            "data": data,
        })

    return cleaned


def save_run(
    session: Session,
    *,
    user_id: int,
    session_id: int | None,
    project: str,
    input_text: str,
    output_text: str,
    memory: list[dict[str, str]] | None,
    timeline: list[dict[str, Any]] | None,
    latency_ms: float,
    confidence_score: float,
    success: bool,
    prompt_tokens: int | None = None,
    completion_tokens: int | None = None,
    total_tokens: int | None = None,
    cost_usd: float | None = None,
    model_used: str | None = None,
) -> Run:
    """Persist a project execution for a user."""
    run = Run(
        user_id=user_id,
        session_id=session_id,
        project=project,
        input_text=input_text,
        output_text=output_text,
        memory_text=_serialize_memory_entries(memory),
        timeline_text=_serialize_timeline_entries(timeline),
        latency_ms=latency_ms,
        confidence_score=confidence_score,
        success=success,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        cost_usd=cost_usd,
        model_used=model_used,
    )
    session.add(run)
    session.commit()
    session.refresh(run)
    return run


def serialize_run(run: Run) -> dict[str, Any]:
    """Convert a persisted run into an API payload."""
    return {
        "id": run.id,
        "user_id": run.user_id,
        "session_id": run.session_id,
        "project": run.project,
        "input": run.input_text,
        "output": run.output_text,
        "memory": _deserialize_memory_entries(run.memory_text),
        "timeline": _deserialize_timeline_entries(run.timeline_text),
        "latency": round(run.latency_ms, 2),
        "confidence": round(run.confidence_score, 2),
        "success": run.success,
        "timestamp": run.timestamp.isoformat() if run.timestamp else None,
        "share_token": run.share_token,
        "is_public": run.is_public,
        "expires_at": run.expires_at.isoformat() if run.expires_at else None,
        "prompt_tokens": run.prompt_tokens,
        "completion_tokens": run.completion_tokens,
        "total_tokens": run.total_tokens,
        "cost_usd": run.cost_usd,
        "model_used": run.model_used,
    }


def get_bearer_token(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(auth_scheme),
) -> str:
    """Resolve a bearer token from Authorization header or HttpOnly cookie.

    The ``?token=`` query-string fallback was removed in the 2026-04 audit:
    tokens in URLs leak into server access logs, reverse-proxy logs, browser
    history, and ``Referer`` headers sent to third-party hosts.  Clients
    streaming via ``/stream/{project}`` use ``fetch`` with a ``ReadableStream``
    body, which supports the ``Authorization`` header natively.
    """
    if credentials is not None:
        return credentials.credentials

    cookie_token = request.cookies.get(AUTH_COOKIE_NAME)
    if cookie_token:
        return cookie_token

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required.",
    )


def get_optional_bearer_token(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(auth_scheme),
) -> str | None:
    """Resolve a bearer token when present, otherwise return ``None``."""
    if credentials is not None:
        return credentials.credentials

    cookie_token = request.cookies.get(AUTH_COOKIE_NAME)
    if cookie_token:
        return cookie_token

    return None


def get_current_user(
    token: str = Depends(get_bearer_token),
    session: Session = Depends(get_db_session),
) -> User:
    """Return the currently authenticated user from a JWT."""
    try:
        payload = decode_access_token(token)
        user_id = int(payload.get("sub", "0"))
    except (AuthError, TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
        ) from exc

    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user was not found.",
        )

    return user


def get_optional_current_user(
    token: str | None = Depends(get_optional_bearer_token),
    session: Session = Depends(get_db_session),
) -> User | None:
    """Return the authenticated user when a token is provided, else ``None``."""
    if token is None:
        return None

    try:
        payload = decode_access_token(token)
        user_id = int(payload.get("sub", "0"))
    except (AuthError, TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
        ) from exc

    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user was not found.",
        )

    return user