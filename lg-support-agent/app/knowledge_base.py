from __future__ import annotations

import math

from shared.llm.gemini import generate_text
from app.state import RESPONSE_MODEL

EMBEDDING_MODEL = "gemini-embedding-2-preview"

# ---------------------------------------------------------------------------
# Raw articles keyed by intent category
# ---------------------------------------------------------------------------

ARTICLES: dict[str, list[str]] = {
    "billing": [
        "Issue: Double charge on subscription. Solution: Verify the transaction in the billing portal. If confirmed, submit a refund request through Settings > Billing > Dispute. Refunds process within 5-7 business days.",
        "Issue: Unable to update payment method. Solution: Go to Settings > Billing > Payment Methods. Remove the old card and add the new one. If the new card is declined, confirm the billing address matches your bank records.",
        "Issue: Unexpected price increase. Solution: Check your plan tier under Settings > Subscription. Price changes are communicated 30 days in advance via email. Review your notification preferences if you did not receive the notice.",
        "Issue: Invoice not received. Solution: Invoices are sent to the account email on file. Check spam/junk folders. Download past invoices from Settings > Billing > Invoice History.",
        "Issue: Promo code not applied. Solution: Promo codes must be entered before checkout confirmation. Contact support with the code and order ID to apply retroactively within 48 hours of purchase.",
    ],
    "technical": [
        "Issue: Application crashes on startup. Solution: Clear the app cache in Settings > Storage > Clear Cache. If the issue persists, uninstall and reinstall the latest version from the official download page.",
        "Issue: Login fails with 'invalid credentials' error. Solution: Reset your password via the login page. Ensure caps lock is off and the correct email is used. If using SSO, confirm your identity provider session is active.",
        "Issue: Slow performance or high latency. Solution: Check your internet connection speed. Disable browser extensions that may interfere. Try switching to a wired connection or a different network.",
        "Issue: File upload fails with size error. Solution: The maximum upload size is 50 MB per file. Compress large files or split them before uploading. Supported formats: PDF, PNG, JPG, CSV, XLSX.",
        "Issue: API rate limit exceeded. Solution: The default rate limit is 100 requests per minute. Implement exponential backoff in your client. Upgrade to a higher-tier plan for increased limits.",
    ],
    "account": [
        "Issue: Cannot reset password. Solution: Use the 'Forgot Password' link on the login page. If the reset email does not arrive within 5 minutes, check spam or try an alternate email associated with the account.",
        "Issue: Account locked after failed login attempts. Solution: Accounts lock after 5 consecutive failed attempts. Wait 30 minutes for automatic unlock, or contact support with your account email for immediate unlock.",
        "Issue: Unable to change account email. Solution: Go to Settings > Profile > Email. Enter the new email and verify it via the confirmation link. The old email remains active until the new one is confirmed.",
        "Issue: Two-factor authentication lost. Solution: Use one of your backup recovery codes to log in. If backup codes are unavailable, contact support with government-issued ID for identity verification and 2FA reset.",
        "Issue: Account deletion request. Solution: Go to Settings > Account > Delete Account. Data is retained for 30 days before permanent deletion. Download your data export before confirming deletion.",
    ],
    "general": [
        "Issue: How to contact support. Solution: Use the in-app chat widget, email support@example.com, or call 1-800-SUPPORT during business hours (9 AM - 6 PM EST, Mon-Fri).",
        "Issue: Feature request submission. Solution: Submit feature requests through the feedback portal at feedback.example.com. Upvote existing requests to increase priority. The product team reviews submissions monthly.",
        "Issue: Service status and outage information. Solution: Check the real-time service status page at status.example.com. Subscribe to status updates via email or SMS for incident notifications.",
        "Issue: Data privacy and GDPR compliance. Solution: Review our privacy policy at example.com/privacy. Submit a data access or deletion request through Settings > Privacy > Data Requests. Requests are processed within 30 days.",
        "Issue: Supported platforms and system requirements. Solution: The application supports Windows 10+, macOS 12+, iOS 16+, and Android 12+. Minimum browser versions: Chrome 90+, Firefox 90+, Safari 15+, Edge 90+.",
    ],
}

# ---------------------------------------------------------------------------
# Embedding helpers
# ---------------------------------------------------------------------------

_test_embed_fn = None  # Injected for testing only


def _get_embed_fn():
    """Return the embedding function.

    Creates a fresh Gemini client per call from the per-request API key.
    """
    if _test_embed_fn is not None:
        return _test_embed_fn

    from google.genai import types as _types
    from shared.llm.gemini import _get_client

    def _embed(texts: list[str]) -> list[list[float]]:
        response = _get_client().models.embed_content(
            model=EMBEDDING_MODEL,
            contents=texts,
            config=_types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT"),
        )
        return [list(e.values) for e in response.embeddings]

    return _embed


def set_embed_fn(fn) -> None:
    """Override the embedding function (useful for testing)."""
    global _test_embed_fn  # noqa: PLW0603
    _test_embed_fn = fn


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


# ---------------------------------------------------------------------------
# Document store — built lazily on first search
# ---------------------------------------------------------------------------

_index: list[dict] | None = None  # [{text, intent, embedding}, ...]


def _build_index() -> list[dict]:
    embed = _get_embed_fn()
    all_texts: list[str] = []
    all_intents: list[str] = []
    for intent, docs in ARTICLES.items():
        for doc in docs:
            all_texts.append(doc)
            all_intents.append(intent)
    embeddings = embed(all_texts)
    return [
        {"text": text, "intent": intent, "embedding": emb}
        for text, intent, emb in zip(all_texts, all_intents, embeddings)
    ]


def _get_index() -> list[dict]:
    global _index  # noqa: PLW0603
    if _index is None:
        _index = _build_index()
    return _index


def reset_index() -> None:
    """Force a rebuild of the index on the next search (useful after set_embed_fn)."""
    global _index  # noqa: PLW0603
    _index = None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def search(
    query: str,
    intent: str = "",
    top_k: int = 5,
    threshold: float = 0.0,
) -> list[str]:
    """Return the top-k articles most similar to *query*.

    If *intent* matches a known category, only articles in that category are
    considered.  Falls back to all articles when intent is empty, unknown, or
    yields no results above *threshold*.
    """
    if not query.strip():
        return []

    embed = _get_embed_fn()
    query_embedding = embed([query])[0]
    index = _get_index()

    # Score every article
    scored: list[tuple[float, str]] = []
    for entry in index:
        score = _cosine_similarity(query_embedding, entry["embedding"])
        scored.append((score, entry["text"], entry["intent"]))

    # Filter by intent if valid
    if intent and intent in ARTICLES:
        intent_results = [
            (s, t) for s, t, i in scored if i == intent and s >= threshold
        ]
        intent_results.sort(key=lambda x: x[0], reverse=True)
        if intent_results:
            return [text for _, text in intent_results[:top_k]]

    # Fallback: search across all articles
    all_results = [(s, t) for s, t, _ in scored if s >= threshold]
    all_results.sort(key=lambda x: x[0], reverse=True)
    return [text for _, text in all_results[:top_k]]