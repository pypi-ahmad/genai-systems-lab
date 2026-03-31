# AI Ops Retrospective - Q4 2025

We shipped three internal agent workflows into daily use: incident triage, customer support summarization, and experiment review. The biggest operational lesson was that retrieval quality mattered more than model upgrades for answer reliability. Runs backed by clean source documents and stable metadata had materially fewer hallucinations than runs using loosely curated notes.

Our incident triage agent reduced first-response time from 22 minutes to 8 minutes when the retrieved context included recent postmortems and service ownership notes. Failures clustered around stale runbooks, ambiguous service names, and duplicated documents with conflicting remediation steps.

The support summarization workflow performed best when prompts required explicit source grounding and short output schemas. Free-form summaries looked impressive but often hid uncertainty. Structured summaries with sections for issue, impact, attempted fixes, and recommended next step were easier for managers to review.

We should treat metadata as part of the product. Ownership, document freshness, incident severity, and system domain should be present on every note before ingestion. Better metadata would improve routing, retrieval filtering, and long-term memory quality.