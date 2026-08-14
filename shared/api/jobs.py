"""Redis/RQ-backed project jobs with encrypted, expiring BYOK credentials."""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime

from cryptography.fernet import Fernet, InvalidToken
from redis import Redis
from rq import Queue
from rq.command import send_stop_job_command
from rq.job import Job as RQJob
from rq.serializers import JSONSerializer

from shared.config import (
    reset_byok_api_key,
    reset_request_effort,
    reset_request_model,
    reset_request_provider,
    set_byok_api_key,
    set_request_effort,
    set_request_model,
    set_request_provider,
)

from .db import SessionLocal
from .models import Job
from .runner import run_project

KEY_TTL_SECONDS = 3600


def redis_connection() -> Redis:
    url = os.getenv("GENAI_SYSTEMS_LAB_REDIS_URL") or os.getenv("REDIS_URL")
    if not url:
        raise RuntimeError("Redis is not configured.")
    return Redis.from_url(url)


def _fernet() -> Fernet:
    key = os.getenv("GENAI_SYSTEMS_LAB_BYOK_ENCRYPTION_KEY", "").encode()
    if not key:
        raise RuntimeError("GENAI_SYSTEMS_LAB_BYOK_ENCRYPTION_KEY is required for queued BYOK runs.")
    return Fernet(key)


def store_api_key(job_id: str, api_key: str) -> None:
    redis_connection().setex(f"job-key:{job_id}", KEY_TTL_SECONDS, _fernet().encrypt(api_key.encode()))


def consume_api_key(job_id: str) -> str:
    connection = redis_connection()
    encrypted = connection.getdel(f"job-key:{job_id}")
    if not encrypted:
        raise RuntimeError("The queued API key expired or was already consumed.")
    try:
        return _fernet().decrypt(encrypted).decode()
    except InvalidToken as exc:
        raise RuntimeError("The queued API key could not be decrypted.") from exc


def enqueue_job(
    job_id: str,
    *,
    project: str,
    model: str,
    provider: str,
    effort: str | None,
    api_key: str,
) -> None:
    store_api_key(job_id, api_key)
    Queue("projects", connection=redis_connection(), serializer=JSONSerializer).enqueue(
        execute_job, job_id, project, model, provider, effort, job_id=job_id, job_timeout="30m"
    )


def execute_job(job_id: str, project: str, model: str, provider: str, effort: str | None) -> None:
    with SessionLocal() as session:
        job = session.get(Job, job_id)
        if job is None or job.status == "cancelled":
            return
        job.status, job.started_at = "running", datetime.now(UTC)
        session.commit()
        key = consume_api_key(job_id)
        key_token = set_byok_api_key(key)
        model_token = set_request_model(model)
        provider_token = set_request_provider(provider)
        effort_token = set_request_effort(effort)
        try:
            result = run_project(project, job.input_text, api_key=key)
            session.refresh(job)
            if job.status != "cancelled":
                job.status = "succeeded"
                job.output_text = result.output
                job.usage_text = json.dumps(result.usage) if result.usage else None
        except Exception as exc:
            job.status = "failed"
            job.error_text = str(exc)[:1000]
            raise
        finally:
            job.finished_at = datetime.now(UTC)
            session.commit()
            reset_request_effort(effort_token)
            reset_request_provider(provider_token)
            reset_request_model(model_token)
            reset_byok_api_key(key_token)


def cancel_job(job_id: str) -> None:
    connection = redis_connection()
    rq_job = RQJob.fetch(job_id, connection=connection, serializer=JSONSerializer)
    if rq_job.get_status(refresh=True) == "started":
        send_stop_job_command(connection, job_id)
    else:
        rq_job.cancel()
    connection.delete(f"job-key:{job_id}")
