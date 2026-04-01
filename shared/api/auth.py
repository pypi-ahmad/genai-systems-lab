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
from typing import Any

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from .db import get_db_session
from .models import Run, User

JWT_ALGORITHM = "HS256"
AUTH_COOKIE_NAME = os.getenv("GENAI_SYSTEMS_LAB_AUTH_COOKIE_NAME", "genai_systems_lab_session")
_DEFAULT_JWT_TTL_SECONDS = 60 * 60 * 24 * 7
_EPHEMERAL_DEV_JWT_SECRET = secrets.token_urlsafe(48)
PBKDF2_ITERATIONS = 310_000

_auth_logger = logging.getLogger(__name__)

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
    """Create a signed JWT for the authenticated user."""
    header = {"alg": JWT_ALGORITHM, "typ": "JWT"}
    now = int(time.time())
    payload = {
        "sub": str(user.id),
        "email": user.email,
        "iat": now,
        "exp": now + JWT_TTL_SECONDS,
    }

    header_segment = _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_segment = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{header_segment}.{payload_segment}".encode("utf-8")
    signature = hmac.new(JWT_SECRET.encode("utf-8"), signing_input, hashlib.sha256).digest()
    return f"{header_segment}.{payload_segment}.{_b64url_encode(signature)}"


def decode_access_token(token: str) -> dict[str, Any]:
    """Validate and decode a signed JWT."""
    try:
        header_segment, payload_segment, signature_segment = token.split(".", 2)
    except ValueError as exc:
        raise AuthError("Malformed token.") from exc

    signing_input = f"{header_segment}.{payload_segment}".encode("utf-8")
    expected_signature = hmac.new(JWT_SECRET.encode("utf-8"), signing_input, hashlib.sha256).digest()
    actual_signature = _b64url_decode(signature_segment)

    if not hmac.compare_digest(expected_signature, actual_signature):
        raise AuthError("Invalid token signature.")

    payload = json.loads(_b64url_decode(payload_segment))
    if int(payload.get("exp", 0)) <= int(time.time()):
        raise AuthError("Token expired.")
    return payload


def authenticate_user(session: Session, email: str, password: str) -> User | None:
    """Return the matching user when credentials are valid."""
    normalized_email = email.strip().lower()
    normalized_password = password.strip()
    user = session.scalar(select(User).where(User.email == normalized_email))
    if user is None or not verify_password(normalized_password, user.password_hash):
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
    except json.JSONDecodeError:
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
    except json.JSONDecodeError:
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
    }


def get_bearer_token(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(auth_scheme),
) -> str:
    """Resolve a bearer token from Authorization header or query string."""
    if credentials is not None:
        return credentials.credentials

    cookie_token = request.cookies.get(AUTH_COOKIE_NAME)
    if cookie_token:
        return cookie_token

    query_token = request.query_params.get("token")
    if query_token:
        return query_token

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

    query_token = request.query_params.get("token")
    if query_token:
        return query_token

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