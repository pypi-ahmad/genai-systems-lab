from __future__ import annotations

import math

from google.genai import types

from app.knowledge_base import get_all_conditions
from shared.llm.gemini import _get_client

MAX_RESULTS = 5
MIN_RESULTS = 3
SIMILARITY_THRESHOLD = 0.40
EMBEDDING_MODEL = "gemini-embedding-2-preview"


def _embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a list of texts in a single API call."""
    response = _get_client().models.embed_content(
        model=EMBEDDING_MODEL,
        contents=texts,
        config=types.EmbedContentConfig(task_type="SEMANTIC_SIMILARITY"),
    )
    return [list(e.values) for e in response.embeddings]


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


def _build_embedding_index(
    patient_symptoms: list[str], conditions: list[dict]
) -> tuple[list[list[float]], dict[str, list[list[float]]]]:
    """Embed patient symptoms and all condition symptoms in one batch API call."""
    all_texts: list[str] = list(patient_symptoms)
    condition_ranges: list[tuple[str, int, int]] = []
    for condition in conditions:
        start = len(all_texts)
        all_texts.extend(condition["symptoms"])
        condition_ranges.append((condition["name"], start, len(all_texts)))

    embeddings = _embed_texts(all_texts)

    patient_embeddings = embeddings[: len(patient_symptoms)]
    condition_embeddings: dict[str, list[list[float]]] = {}
    for name, start, end in condition_ranges:
        condition_embeddings[name] = embeddings[start:end]

    return patient_embeddings, condition_embeddings


def _semantic_score(
    patient_embeddings: list[list[float]],
    condition_symptom_embeddings: list[list[float]],
) -> float:
    """Score a condition by averaging the best similarity each patient symptom achieves."""
    if not patient_embeddings or not condition_symptom_embeddings:
        return 0.0

    best_per_patient: list[float] = []
    for p_emb in patient_embeddings:
        best = max(_cosine_similarity(p_emb, c_emb) for c_emb in condition_symptom_embeddings)
        best_per_patient.append(best)

    return sum(best_per_patient) / len(best_per_patient)


def retrieve_conditions(symptoms: list[str]) -> list[dict]:
    """Return top matching conditions using embedding-based semantic similarity.

    Each patient symptom is compared against every condition symptom via cosine
    similarity.  The condition score is the average of the best per-symptom
    similarity values.  Returns the top 3–5 conditions above a minimum
    similarity threshold.
    """
    if not symptoms:
        return []

    conditions = get_all_conditions()
    patient_embeddings, condition_embeddings = _build_embedding_index(symptoms, conditions)

    scored: list[tuple[float, int, dict]] = []
    for condition in conditions:
        cond_embs = condition_embeddings[condition["name"]]
        score = _semantic_score(patient_embeddings, cond_embs)

        # Count symptoms that individually exceed the threshold (used downstream)
        match_count = 0
        for p_emb in patient_embeddings:
            if max(_cosine_similarity(p_emb, c_emb) for c_emb in cond_embs) >= SIMILARITY_THRESHOLD:
                match_count += 1

        if score >= SIMILARITY_THRESHOLD:
            scored.append((score, match_count, condition))

    # Sort by semantic score descending, then alphabetically for stability
    scored.sort(key=lambda item: (-item[0], item[2]["name"]))

    count = max(MIN_RESULTS, min(MAX_RESULTS, len(scored)))
    top = scored[:count]

    return [
        {**condition, "match_score": match_count, "semantic_score": round(score, 4)}
        for score, match_count, condition in top
    ]