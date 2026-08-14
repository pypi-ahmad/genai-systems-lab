# Changelog

## Unreleased

- Added Agnes AI `agnes-2.5-flash` through the OpenAI-compatible Chat Completions API, including streaming, structured JSON, image understanding, BYOK key handling, and zero-cost usage estimates.
- Changed the local Next.js frontend port to `8513` and the host-facing FastAPI port to `8514`; Docker continues to use port `8000` inside the API container.

All notable changes to this project will be documented in this file.

This project follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and aims to follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

### Changed

### Fixed

## [1.1.1] - 2026-08-14

### Security

- Upgraded Starlette, PyJWT, python-dotenv, and the standalone LangChain stack to patched releases and removed dependency-advisory suppressions from CI.
- Removed the optional CrewAI dependency tree and build-only pip/setuptools tooling from the production image.
- Extended blocking Python dependency audits to the standalone data analyst environment.

### Fixed

- Included the shared project catalog in the Docker image so the API can start successfully.
- Wired the Gitleaks GitHub Action to its repository configuration through the supported environment variable, so Graphify content hashes are not misclassified as credentials.

## [1.1.0] - 2026-08-14

- Restricted the hosted model catalog to Gemini 3.7 Flash / 3.5 Flash Lite, GPT-5.6 Luna / Terra, Claude Sonnet 5, and Grok 4.6 while retaining dynamic Ollama discovery.
- Added model-specific reasoning-effort controls across the Playground, project demos, comparison workspace, synchronous requests, streams, and queued jobs.
- Added xAI BYOK dispatch for text, streaming, structured, and vision requests.
- Added UI pricing cards and per-call token-cost breakdowns with Luna cached-input and Terra/Grok long-context rates.
- Added `launch.cmd` for one-click Windows prerequisite setup, Docker services, frontend startup, health checks, and browser launch.
- Added a validated, interactive system architecture diagram with repository-pinned source evidence.
- Simplified shared runner import setup and best-effort telemetry control flow without changing execution behavior.
- Moved Langfuse trace flushing off the project execution path to remove synchronous telemetry latency.
- Disabled shared runner/API access to the generated-Python debugging agent by default, with an explicit development-only opt-in.
- Replaced NL2SQL text-pattern checks with DuckDB AST allowlisting, sink revalidation, bounded results, and disabled external access.
- Required authentication and owner-scoped lookup for queued job creation, status, and cancellation.
- Added PostgreSQL/Alembic production persistence and Redis/RQ worker services.
- Added durable job create/status/cancel APIs with encrypted, expiring BYOK handoff.
- Added token aggregation, verified cost estimates, actual-model attribution, and usage fields.
- Normalized Gemini, OpenAI, and Anthropic provider token field names into one run-level usage contract.
- Updated Next.js to 16.3.1 and removed high-severity production dependency findings.
- Added frontend loading/error/not-found boundaries and generated robots/sitemap metadata.
- Added queue/database environment templates and included Alembic assets in the production image.
- Expanded CI from two hand-picked project suites to automatic all-project test discovery.
- Added a live side-by-side model comparison workspace with latency, usage, and cost reporting.
- Added provider-native final-writer streaming for both research flagships across Gemini, OpenAI, Anthropic, xAI, Agnes AI, and Ollama; CrewAI remains explicitly step-only.

## [2026-06-13]

### Added

- OSS companion documentation initialized (license, contributing, security, conduct, changelog).
