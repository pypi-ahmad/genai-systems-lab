from shared.llm.catalog import (
    build_provider_catalog,
    calculate_model_cost,
    default_model,
    estimate_model_cost,
    infer_provider,
    validate_model_effort,
)
from shared.llm.telemetry import (
    begin_llm_run,
    consume_llm_call_metadata,
    consume_llm_run_usage,
    record_llm_call_metadata,
    record_llm_run_call,
)


def test_call_metadata_merges_model_and_usage() -> None:
    record_llm_call_metadata({"model_used": "fallback"})
    record_llm_call_metadata({"usage_details": {"input": 2, "output": 3}})
    assert consume_llm_call_metadata() == {
        "model_used": "fallback",
        "usage_details": {"input": 2, "output": 3},
    }


def test_run_usage_aggregates_calls() -> None:
    begin_llm_run()
    record_llm_run_call({"model_used": "a", "input_tokens": 2, "output_tokens": 3, "estimated_cost_usd": 0.1})
    record_llm_run_call({"model_used": "b", "input_tokens": 5, "output_tokens": 7, "estimated_cost_usd": None})
    assert consume_llm_run_usage() == {
        "input_tokens": 7,
        "output_tokens": 10,
        "total_tokens": 17,
        "estimated_cost_usd": 0.1,
        "models_used": ["a", "b"],
        "cost_breakdown": [],
        "calls": [
            {"model_used": "a", "input_tokens": 2, "output_tokens": 3, "estimated_cost_usd": 0.1},
            {"model_used": "b", "input_tokens": 5, "output_tokens": 7, "estimated_cost_usd": None},
        ],
    }


def test_catalog_contains_only_approved_hosted_models(monkeypatch) -> None:
    monkeypatch.setattr("shared.llm.catalog.list_ollama_models", lambda: ([], "offline"))
    catalog = build_provider_catalog()
    hosted = {
        provider["id"]: [model["id"] for model in provider["models"]]
        for provider in catalog["providers"]
        if provider["id"] != "ollama"
    }
    assert default_model() == "gemini-3.7-flash"
    assert hosted == {
        "gemini": ["gemini-3.7-flash", "gemini-3.5-flash-lite"],
        "openai": ["gpt-5.6-luna", "gpt-5.6-terra"],
        "anthropic": ["claude-sonnet-5"],
        "xai": ["grok-4.6"],
    }
    assert infer_provider("grok-4.6") == "xai"


def test_model_effort_validation() -> None:
    assert validate_model_effort("gpt-5.6-luna", "MAX") == "max"
    assert validate_model_effort("gpt-5.6-luna", "default") is None
    assert validate_model_effort("grok-4.6", None) is None
    try:
        validate_model_effort("gemini-3.7-flash", "minimal")
    except ValueError as exc:
        assert "Unsupported effort" in str(exc)
    else:  # pragma: no cover - contract guard
        raise AssertionError("Invalid effort was accepted")


def test_luna_cost_uses_cached_input_rate() -> None:
    breakdown = calculate_model_cost(
        "gpt-5.6-luna",
        1_000_000,
        1_000_000,
        cached_input_tokens=250_000,
    )
    assert breakdown is not None
    assert breakdown["cached_input_tokens"] == 250_000
    assert breakdown["input_cost_usd"] == 0.155
    assert breakdown["output_cost_usd"] == 1.2
    assert breakdown["estimated_cost_usd"] == 1.355


def test_long_context_thresholds_apply_only_when_exceeded() -> None:
    terra_standard = calculate_model_cost("gpt-5.6-terra", 272_000, 1_000)
    terra_long = calculate_model_cost("gpt-5.6-terra", 272_001, 1_000)
    grok_standard = calculate_model_cost("grok-4.6", 200_000, 1_000)
    grok_long = calculate_model_cost("grok-4.6", 200_001, 1_000)
    assert terra_standard and terra_standard["pricing_tier"] == "standard"
    assert terra_long and terra_long["pricing_tier"] == "long_context"
    assert terra_long["output_rate_per_million_usd"] == 24.0
    assert grok_standard and grok_standard["pricing_tier"] == "standard"
    assert grok_long and grok_long["pricing_tier"] == "long_context"
    assert grok_long["input_rate_per_million_usd"] == 4.0


def test_cost_is_unknown_for_local_models() -> None:
    assert estimate_model_cost("local-model", 1_000, 1_000) is None


def test_run_usage_groups_matching_cost_rows() -> None:
    first = calculate_model_cost("gemini-3.7-flash", 1_000, 500)
    second = calculate_model_cost("gemini-3.7-flash", 2_000, 1_000)
    assert first and second
    begin_llm_run()
    for breakdown in (first, second):
        record_llm_run_call({
            "model_used": "gemini-3.7-flash",
            "input_tokens": breakdown["input_tokens"],
            "output_tokens": breakdown["output_tokens"],
            "estimated_cost_usd": breakdown["estimated_cost_usd"],
            "cost_breakdown": breakdown,
        })

    usage = consume_llm_run_usage()
    assert usage is not None
    assert usage["estimated_cost_usd"] == 0.007875
    assert usage["cost_breakdown"] == [{
        **first,
        "input_tokens": 3_000.0,
        "cached_input_tokens": 0.0,
        "output_tokens": 1_500.0,
        "input_cost_usd": 0.00225,
        "output_cost_usd": 0.005625,
        "estimated_cost_usd": 0.007875,
    }]
