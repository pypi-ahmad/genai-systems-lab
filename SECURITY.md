# Security Policy

## Supported Versions

Security fixes are applied to the default branch and recent actively maintained updates.

## Reporting a Vulnerability

Please report potential vulnerabilities through GitHub Issues in this repository.

When reporting, include:

- A clear description of the issue
- Impact assessment
- Reproduction steps or proof of concept
- Suggested remediation, if available

Avoid posting exploit details that could put users at risk. Maintainers may request
additional details privately through GitHub as needed.

## Response Process

Maintainers will triage reports, assess severity, and communicate remediation status
through issue updates and release/change notes when fixes are available.

## BYOK handling

Synchronous keys are request-scoped and never persisted. Queued-job keys are Fernet-encrypted using `GENAI_SYSTEMS_LAB_BYOK_ENCRYPTION_KEY`, expire from Redis after one hour, and are deleted when consumed or cancelled. Agnes keys follow the same BYOK flow; `AGNES_API_KEY` is not a runtime fallback and must never be exposed to the frontend. Never commit this key, provider keys, JWT secrets, or production database credentials.

Gitleaks v3 scans repository content in CI and loads `.github/gitleaks.toml` through its supported `GITLEAKS_CONFIG` environment variable. Its only generated-graph exception is Graphify's exact `cache/stat-index.json` path, which contains repository file-content hashes rather than credentials; other graph artifacts remain subject to the default secret rules.

Python dependency audits are blocking and cover both the shared platform and the standalone data analyst. The production image installs only the shared runtime and removes build-only pip/setuptools tooling; optional CrewAI and browser runtimes must be installed explicitly for their corresponding local projects. CI does not suppress Python or container advisories.

Every queued-job route requires authentication. Job creation records the authenticated owner, and status/cancellation queries match both the random job UUID and that owner. Cross-user lookups return the same `404` as missing jobs. Provider credentials are required only when creating work, not when reading or cancelling owned jobs.

## Generated-code execution

`lg-debugging-agent` executes generated Python and is therefore a trusted-local experiment, not a sandbox. The shared runner, API, evaluation, streaming, and queued-job surfaces exclude it by default. It can only be enabled when `APP_ENV` is not `prod` and `GENAI_SYSTEMS_LAB_ENABLE_UNSAFE_AGENTS=true`; never enable it for untrusted users.

## Model-generated SQL

NL2SQL output is untrusted. Before execution, DuckDB parses it into an AST that is checked with a deny-by-default policy: one `SELECT`, only the `customers` and `orders` demo tables, and only approved expressions and functions. The executor repeats validation at the sink, caps returned rows, disables external file/network access, and disables extension auto-install and autoload.
