# Support

Welcome! Here is how to get help with GenAI Systems Lab.

> [!NOTE]
> **No paid support or donations.** This project is free and community-maintained. There is no financial support model, no sponsorship program, and no paid-support tier. If you want to give back, the best way is to open a bug report, suggest an improvement, or contribute a fix.

---

## Before asking for help

1. Check [README.md](README.md) — the setup, configuration, and usage are documented there in full.
2. Check [portfolio/USAGE.md](portfolio/USAGE.md) for the step-by-step frontend guide.
3. Check [ARCHITECTURE.md](ARCHITECTURE.md) for platform internals.
4. Search [open and closed issues](https://github.com/pypi-ahmad/genai-systems-lab/issues?q=is%3Aissue) — someone may have already asked the same question.

---

## How to get help

| Question type | Where to go |
|---|---|
| Bug or unexpected behavior | [Open a bug report](https://github.com/pypi-ahmad/genai-systems-lab/issues/new?template=bug_report.md) |
| Feature suggestion or idea | [Open a feature request](https://github.com/pypi-ahmad/genai-systems-lab/issues/new?template=feature_request.md) |
| Question about the codebase | [Open a GitHub issue](https://github.com/pypi-ahmad/genai-systems-lab/issues/new) with the `question` label |
| Security vulnerability | See [SECURITY.md](SECURITY.md) — **do not post publicly** |
| Contribution question | See [CONTRIBUTING.md](CONTRIBUTING.md) |

---

## Self-hosted — your machine, your keys

GenAI Systems Lab runs **entirely on your own machine**. There is no hosted service, no cloud backend, and no account system on this project's side. Every LLM call uses your own API keys provided via request headers.

This means:

- **API costs are yours.** Every call to Gemini, OpenAI, Anthropic, xAI, or Agnes AI deducts from your account quota at each provider's list rate.
- **Your data is yours.** The maintainer has no access to your prompts, outputs, session history, or credentials. See [DISCLAIMER.md](DISCLAIMER.md).
- **Provider issues go to the provider.** Quota errors, billing questions, rate limits, model deprecations, and API outages are outside the scope of this project. Contact the relevant provider directly.

---

## What this project will not debug

| Out of scope | Reason |
|---|---|
| Provider API errors (quota, billing, 429s) | Third-party services — contact the provider |
| API key validity or account access | Your credentials — check your provider dashboard |
| Docker or WSL setup on your machine | System-specific — consult Docker or Microsoft docs |
| Compliance with data regulations | Your responsibility — see [DISCLAIMER.md](DISCLAIMER.md) |
| Custom deployments or forks | Community help only — no dedicated support |

---

## Documentation index

| Document | What it covers |
|---|---|
| [README.md](README.md) | Full platform overview, setup, API reference, env vars |
| [portfolio/USAGE.md](portfolio/USAGE.md) | Frontend step-by-step usage guide |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Platform design, module layout, design philosophy |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Dev setup, test commands, PR rules |
| [SECURITY.md](SECURITY.md) | Security model, BYOK handling, vulnerability reporting |
| [DISCLAIMER.md](DISCLAIMER.md) | Data responsibility, no-warranty, no-financial-support |
| [CHANGELOG.md](CHANGELOG.md) | Release history |
