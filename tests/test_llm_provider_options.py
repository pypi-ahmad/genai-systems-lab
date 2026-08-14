import json
from contextlib import contextmanager

from shared.config import (
    reset_byok_api_key,
    reset_request_effort,
    set_byok_api_key,
    set_request_effort,
)
from shared.llm import dispatch, gemini_provider, providers


def _bind_request(effort: str | None = None):
    key_token = set_byok_api_key("provider-test-credential")
    effort_token = set_request_effort(effort)
    return key_token, effort_token


def _reset_request(tokens) -> None:
    key_token, effort_token = tokens
    reset_request_effort(effort_token)
    reset_byok_api_key(key_token)


def test_openai_effort_is_sent_in_responses_payload(monkeypatch) -> None:
    captured = {}

    def fake_request_json(**kwargs):
        captured.update(kwargs)
        return {"output_text": "ok", "usage": {"input_tokens": 2, "output_tokens": 1}}

    monkeypatch.setattr(providers, "_request_json", fake_request_json)
    tokens = _bind_request("max")
    try:
        assert providers.openai_generate_text(
            "prompt", "gpt-5.6-luna", temperature=0.7
        ) == "ok"
    finally:
        _reset_request(tokens)

    assert captured["url"] == providers.OPENAI_RESPONSES_URL
    assert captured["payload"]["reasoning"] == {"effort": "max"}
    assert "temperature" not in captured["payload"]


def test_xai_text_structured_and_vision_use_xai_responses(monkeypatch) -> None:
    requests: list[dict] = []

    def fake_request_json(**kwargs):
        requests.append(kwargs)
        output = '{"answer":"ok"}' if "text" in kwargs["payload"] else "ok"
        return {"output_text": output, "usage": {"input_tokens": 2, "output_tokens": 1}}

    monkeypatch.setattr(providers, "_request_json", fake_request_json)
    tokens = _bind_request()
    try:
        assert providers.xai_generate_text("prompt", "grok-4.6") == "ok"
        assert providers.xai_generate_structured(
            "prompt", "grok-4.6", {"type": "object", "properties": {"answer": {"type": "string"}}}
        ) == {"answer": "ok"}
        assert providers.xai_generate_text_from_image("prompt", b"image", "grok-4.6") == "ok"
    finally:
        _reset_request(tokens)

    assert len(requests) == 3
    assert all(request["url"] == providers.XAI_RESPONSES_URL for request in requests)
    assert requests[1]["payload"]["text"]["format"]["type"] == "json_schema"
    assert requests[2]["payload"]["input"][0]["content"][1]["type"] == "input_image"


def test_xai_stream_uses_responses_events(monkeypatch) -> None:
    events = [
        {"type": "response.output_text.delta", "delta": "hello "},
        {"type": "response.output_text.delta", "delta": "world"},
        {
            "type": "response.completed",
            "response": {"usage": {"input_tokens": 3, "output_tokens": 2}},
        },
    ]
    captured = {}

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def iter_lines(self):
            return [f"data: {json.dumps(event)}" for event in events]

    class FakeClient:
        @contextmanager
        def stream(self, method, url, **kwargs):
            captured.update({"method": method, "url": url, **kwargs})
            yield FakeResponse()

    monkeypatch.setattr(providers, "_http_client", lambda: FakeClient())
    chunks: list[str] = []
    tokens = _bind_request()
    try:
        assert providers.xai_stream_text("prompt", "grok-4.6", chunks.append) == "hello world"
    finally:
        _reset_request(tokens)

    assert chunks == ["hello ", "world"]
    assert captured["url"] == providers.XAI_RESPONSES_URL


def test_anthropic_effort_merges_with_structured_output_config(monkeypatch) -> None:
    captured = {}

    def fake_request_json(**kwargs):
        captured.update(kwargs)
        return {"content": [{"type": "text", "text": '{"answer":"ok"}'}], "usage": {}}

    monkeypatch.setattr(providers, "_request_json", fake_request_json)
    tokens = _bind_request("xhigh")
    try:
        result = providers.anthropic_generate_structured(
            "prompt", "claude-sonnet-5", {"type": "object", "properties": {"answer": {"type": "string"}}}
        )
    finally:
        _reset_request(tokens)

    assert result == {"answer": "ok"}
    assert captured["payload"]["output_config"]["effort"] == "xhigh"
    assert captured["payload"]["output_config"]["format"]["type"] == "json_schema"


def test_gemini_effort_is_added_to_generation_config(monkeypatch) -> None:
    captured = {}

    class FakeResponse:
        text = "ok"
        usage_metadata = None

    def fake_request_content(**kwargs):
        captured.update(kwargs)
        return FakeResponse()

    monkeypatch.setattr(gemini_provider, "_request_content", fake_request_content)
    tokens = _bind_request("high")
    try:
        assert gemini_provider.generate_text("prompt", "gemini-3.7-flash") == "ok"
    finally:
        _reset_request(tokens)

    assert captured["config"].thinking_config.thinking_level.value == "HIGH"


def test_compat_client_routes_gemini_text_through_measured_dispatch(monkeypatch) -> None:
    captured = {}

    def fake_generate_text(**kwargs):
        captured.update(kwargs)
        return "measured"

    monkeypatch.setattr(dispatch.gemini_provider, "generate_text", fake_generate_text)
    tokens = _bind_request("low")
    try:
        response = dispatch.get_client_adapter().models.generate_content(
            model="gemini-3.7-flash",
            contents="prompt",
        )
    finally:
        _reset_request(tokens)

    assert response.text == "measured"
    assert captured == {"prompt": "prompt", "model": "gemini-3.7-flash"}
