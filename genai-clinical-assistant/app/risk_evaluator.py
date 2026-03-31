from __future__ import annotations

HIGH_THRESHOLD = 0.6
MEDIUM_THRESHOLD = 0.3


def _compute_confidence(match_score: int, total_symptoms: int) -> float:
    """Compute confidence as the ratio of matched symptoms to total symptoms."""
    if total_symptoms <= 0:
        return 0.0
    return round(min(match_score / total_symptoms, 1.0), 2)


def _label_from_confidence(confidence: float) -> str:
    if confidence >= HIGH_THRESHOLD:
        return "High"
    if confidence >= MEDIUM_THRESHOLD:
        return "Medium"
    return "Low"


def assign_confidence(results: list[dict]) -> list[dict]:
    """Add confidence score (0–1) and label (Low/Medium/High) to each condition.

    Expects each dict to contain:
      - match_score (int): number of patient symptoms that matched
      - symptoms (list): the condition's full symptom list
    """
    enriched = []
    for entry in results:
        match_score = entry.get("match_score", 0)
        total_symptoms = len(entry.get("symptoms", []))
        confidence = _compute_confidence(match_score, total_symptoms)
        enriched.append({
            **entry,
            "confidence": confidence,
            "label": _label_from_confidence(confidence),
        })
    return enriched