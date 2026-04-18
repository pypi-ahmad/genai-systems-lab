# syntax=docker/dockerfile:1.7

# ---- Builder stage: install Python deps into a relocatable prefix ----------
FROM python:3.13-slim AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /build

COPY requirements.txt .
RUN pip install --prefix=/install -r requirements.txt

# ---- Runtime stage: slim, non-root, with only what we need -----------------
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PORT=8000

# Install a tiny curl purely for the HEALTHCHECK; drop apt caches afterwards.
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --system --uid 10001 --home-dir /app --shell /usr/sbin/nologin app \
    && mkdir -p /app/.data \
    && chown -R app:app /app

WORKDIR /app

# Bring in the pre-built Python deps.
COPY --from=builder /install /usr/local

# NOTE: the old Dockerfile used `COPY crew-*/ ./`, `COPY genai-*/ ./`, and
# `COPY lg-*/ ./`, which flattened every project's contents into the root
# `/app` directory — last writer wins for every identically-named file
# (e.g. `app/__init__.py`), silently corrupting most of the 20 projects.
# We now copy each project into its own sub-directory, preserving structure.
COPY --chown=app:app shared/ ./shared/
COPY --chown=app:app pyproject.toml requirements.txt ./

COPY --chown=app:app crew-content-pipeline/    ./crew-content-pipeline/
COPY --chown=app:app crew-hiring-system/       ./crew-hiring-system/
COPY --chown=app:app crew-investment-analyst/  ./crew-investment-analyst/
COPY --chown=app:app crew-product-launch/      ./crew-product-launch/
COPY --chown=app:app crew-startup-simulator/   ./crew-startup-simulator/

COPY --chown=app:app genai-browser-agent/      ./genai-browser-agent/
COPY --chown=app:app genai-clinical-assistant/ ./genai-clinical-assistant/
COPY --chown=app:app genai-code-copilot/       ./genai-code-copilot/
COPY --chown=app:app genai-doc-intelligence/   ./genai-doc-intelligence/
COPY --chown=app:app genai-financial-analyst/  ./genai-financial-analyst/
COPY --chown=app:app genai-interviewer/        ./genai-interviewer/
COPY --chown=app:app genai-knowledge-os/       ./genai-knowledge-os/
COPY --chown=app:app genai-nl2sql-agent/       ./genai-nl2sql-agent/
COPY --chown=app:app genai-research-system/    ./genai-research-system/
COPY --chown=app:app genai-ui-builder/         ./genai-ui-builder/

COPY --chown=app:app lg-data-agent/            ./lg-data-agent/
COPY --chown=app:app lg-debugging-agent/       ./lg-debugging-agent/
COPY --chown=app:app lg-research-agent/        ./lg-research-agent/
COPY --chown=app:app lg-support-agent/         ./lg-support-agent/
COPY --chown=app:app lg-workflow-agent/        ./lg-workflow-agent/

# Drop privileges before runtime.  .env files are intentionally NOT copied in;
# inject runtime configuration via environment variables (docker-compose
# `environment:`, Kubernetes Secrets, Vercel env, etc.).
USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=20s --retries=3 \
    CMD curl -fsS http://127.0.0.1:${PORT}/health >/dev/null || exit 1

# ``--workers`` picks a sensible default for the container's CPU quota.  When
# running behind an orchestrator, let the orchestrator control concurrency
# (overriding CMD) rather than setting it via Python.
# ``--forwarded-allow-ips`` is required for ``--proxy-headers`` to be honoured
# for any client IP; without it, ``X-Forwarded-For`` is silently ignored for
# non-loopback peers and the app sees the reverse-proxy's IP everywhere
# (breaking rate-limiting / audit logs).  The deployment contract is that the
# container only ever receives traffic through a trusted reverse proxy.
CMD ["uvicorn", "shared.api.app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2", "--proxy-headers", "--forwarded-allow-ips", "*"]
