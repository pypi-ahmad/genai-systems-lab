"""Application entry point for the clinical decision support pipeline."""

from __future__ import annotations

from app.extractor import extract_patient_info
from app.retriever import retrieve_conditions
from app.reasoner import analyze_conditions
from app.risk_evaluator import assign_confidence
from app.formatter import format_output
from shared.api.step_events import emit_step
from shared.config import set_byok_api_key, reset_byok_api_key


def _merge_reasoning_and_confidence(
    analyses: list[dict], scored: list[dict]
) -> list[dict]:
    """Combine reasoning from the LLM with confidence from the deterministic scorer."""
    scored_map = {entry.get("name", ""): entry for entry in scored}
    merged = []
    for analysis in analyses:
        condition_name = analysis.get("condition", "")
        score_entry = scored_map.get(condition_name, {})
        merged.append({
            **analysis,
            "confidence": score_entry.get("confidence", 0.0),
            "label": score_entry.get("label", "Low"),
        })
    return merged


def run(input: str, api_key: str) -> dict:
    """Run the clinical decision support pipeline and return structured output."""
    token = set_byok_api_key(api_key)
    try:
        emit_step("extractor", "running")
        patient_info = extract_patient_info(input)
        emit_step("extractor", "done")

        emit_step("retriever", "running")
        conditions = retrieve_conditions(patient_info.get("symptoms", []))
        emit_step("retriever", "done")
        if not conditions:
            return {"report": "No matching conditions found for the provided symptoms.", "conditions": []}

        emit_step("reasoner", "running")
        analyses = analyze_conditions(patient_info, conditions)
        scored = assign_confidence(conditions)
        emit_step("reasoner", "done")

        emit_step("formatter", "running")
        merged = _merge_reasoning_and_confidence(analyses, scored)
        report = format_output(input, merged)
        emit_step("formatter", "done")
        return {"report": report, "conditions": merged}
    finally:
        reset_byok_api_key(token)
