# Contributing to GenAI Systems Lab

Thank you for your interest in GenAI Systems Lab! This is a community project and every contribution — bug report, feature idea, documentation improvement, or code change — is genuinely appreciated. There is no team behind this, just an open codebase that anyone can help improve.

> [!NOTE]
> **No donations needed.** This project is free and will stay free. There is no financial support, sponsorship, or bounty program — and none is wanted. The best way to contribute is with your time, ideas, and code.

---

## Table of Contents

- [Getting started](#getting-started)
- [Development setup](#development-setup)
- [Running tests](#running-tests)
- [Making changes](#making-changes)
- [Submitting a pull request](#submitting-a-pull-request)
- [Reporting bugs](#reporting-bugs)
- [Suggesting features](#suggesting-features)
- [Data responsibility](#data-responsibility)
- [Code of conduct](#code-of-conduct)

---

## Getting started

1. Fork the repository and clone your fork:
   ```bash
   git clone https://github.com/<your-username>/genai-systems-lab.git
   cd genai-systems-lab
   ```
2. Read [README.md](README.md) and [ARCHITECTURE.md](ARCHITECTURE.md) to understand the platform structure.
3. Check open issues for something you want to work on, or open a new one to discuss your idea first.

---

## Development setup

### Requirements

- Python 3.13 (pinned in `pyproject.toml`)
- [uv](https://docs.astral.sh/uv/) for dependency management
- Node.js 22+ for the portfolio frontend
- Docker Desktop (optional — only needed for full-stack `docker compose` runs)

### Backend

```bash
# Install all dependencies including dev tools
uv sync --all-extras

# Copy env template and fill in your values
cp .env.example .env
```

The backend starts on `http://localhost:8514` by default:

```bash
uv run uvicorn shared.api.app:app --host 0.0.0.0 --port 8514 --reload
```

### Frontend (portfolio)

```bash
cd portfolio
npm install
npm run dev   # starts on http://localhost:8513
```

### Full stack with Docker

```bash
docker compose up --build
```

This provisions PostgreSQL, Redis, the FastAPI backend, an RQ worker, and applies Alembic migrations before serving.

---

## Running tests

```bash
# Full test suite
uv run pytest

# Single file
uv run pytest tests/test_project_catalog.py -v

# Lint
uv run ruff check .

# Format check
uv run ruff format --check .

# Type check (if mypy is installed)
uv run mypy shared/
```

CI runs the full suite on every push. All tests must pass before a PR can be merged.

---

## Making changes

- **New AI project:** Add a directory in the repo root following the existing pattern (`app/main.py` exporting `run(input: str, api_key: str) -> dict`). No registration step required — the platform auto-discovers it at startup.
- **Bug fix:** Prefer fixing the root cause in the shared layer over patching individual callers.
- **Dependency change:** Update `pyproject.toml` and run `uv lock` to regenerate `uv.lock`. Commit both files.
- **Schema change:** Add an idempotent `ALTER TABLE` guard in `shared/db.py`, or adopt an Alembic migration if the change is non-trivial.

### Style

- Python: follow the existing code style; `ruff check .` and `ruff format .` enforce it.
- TypeScript/Next.js: follow the existing component conventions in `portfolio/`.
- Keep commits focused — one logical change per commit.
- Write a clear commit message that explains *why*, not just *what*.

---

## Submitting a pull request

1. Create a branch from `main`:
   ```bash
   git checkout -b feat/my-feature
   ```
2. Make your changes, add tests where appropriate, and confirm the test suite passes.
3. Push and open a pull request against `main`.
4. Fill in the PR template — describe what changed and why, and link to any related issues.
5. A maintainer will review and give feedback. Small, focused PRs are easiest to review and land fastest.

---

## Reporting bugs

Use the [Bug Report](.github/ISSUE_TEMPLATE/bug_report.md) template when opening an issue. The more detail you provide — version, provider, steps to reproduce, redacted logs — the faster the bug can be diagnosed.

> [!IMPORTANT]
> **Never include API keys, JWT secrets, or production credentials in issues, PRs, or comments.** Redact all sensitive values before posting.

Security vulnerabilities go to [SECURITY.md](SECURITY.md), not public issues.

---

## Suggesting features

Use the [Feature Request](.github/ISSUE_TEMPLATE/feature_request.md) template. Describe the problem you are trying to solve and why it would benefit others. Speculative ideas are welcome — you do not need a complete design to open a discussion.

---

## Data responsibility

GenAI Systems Lab runs entirely on your machine with your own API keys. **You are responsible for any data — prompts, documents, outputs — that you process through the platform.** The maintainer has no access to your data, your credentials, or your runs.

See [DISCLAIMER.md](DISCLAIMER.md) for the full statement.

---

## Code of conduct

All contributors are expected to follow [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md). Be respectful and constructive.
