from shared.config import reset_request_provider, set_request_provider
from shared.llm import dispatch
from shared.llm.telemetry import begin_llm_run, consume_llm_run_usage, record_llm_call_metadata
from shared.llm.token_events import bind_token_emitter, reset_token_emitter


def test_final_text_stream_forwards_native_chunks_and_records_usage(monkeypatch) -> None:
    chunks: list[str] = []

    def fake_stream(prompt: str, model: str, emit) -> str:
        assert (prompt, model) == ("prompt", "gemini-3.7-flash")
        emit("hello ")
        emit("world")
        record_llm_call_metadata({"model_used": model, "usage_details": {"input": 4, "output": 2}})
        return "hello world"

    monkeypatch.setattr(dispatch.gemini_provider, "stream_text", fake_stream)
    provider_token = set_request_provider("gemini")
    emitter_token = bind_token_emitter(chunks.append)
    begin_llm_run()
    try:
        assert dispatch.generate_text_streaming("prompt", "gemini-3.7-flash") == "hello world"
        assert chunks == ["hello ", "world"]
        usage = consume_llm_run_usage()
        assert usage is not None and usage["total_tokens"] == 6
    finally:
        reset_token_emitter(emitter_token)
        reset_request_provider(provider_token)
