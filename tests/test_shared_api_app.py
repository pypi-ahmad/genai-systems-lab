from __future__ import annotations

import json
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import shared.api.app as lab_api
from shared.api.db import Base, get_db_session
from shared.api.runner import ProjectUnavailableError, RunResult


TEST_PROVIDER_CREDENTIAL = "local-test-credential"
TEST_ACCOUNT_PASSWORD = "example-password"


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    Base.metadata.create_all(bind=engine)

    def override_db_session() -> Generator[Session, None, None]:
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    def fake_run_project(project: str, user_input: str, *, api_key: str, step_emitter=None) -> RunResult:
        assert api_key == TEST_PROVIDER_CREDENTIAL
        if step_emitter is not None:
            step_emitter("planner", "running")
            step_emitter("planner", "done")
            step_emitter("validator", "running")
            step_emitter("validator", "done")

        display_input = user_input
        if "Current request:\n" in user_input:
            display_input = user_input.split("Current request:\n", 1)[1].strip()

        output = json.dumps(
            {
                "project": project,
                "input": display_input,
                "summary": f"Processed: {display_input}",
                "score": 0.91,
            }
        )
        return RunResult(
            project="genai-nl2sql-agent",
            output=output,
            exit_code=0,
            elapsed_ms=123.45,
        )

    def fake_build_run_explanation(**_: object) -> dict[str, object]:
        return {
            "steps_taken": [
                {
                    "step": "Planner",
                    "what_happened": "The request was analyzed.",
                    "why_it_mattered": "It shaped the output path.",
                }
            ],
            "key_decisions": [
                {
                    "decision": "Use deterministic stub output",
                    "reason": "This keeps the API contract testable.",
                }
            ],
            "final_reasoning": "The saved run artifacts support a successful completion.",
            "final_outcome": "The API returned a structured result.",
        }

    monkeypatch.setattr(lab_api, "run_project", fake_run_project)
    monkeypatch.setattr(lab_api, "build_run_explanation", fake_build_run_explanation)
    monkeypatch.setattr(lab_api, "metrics_store", lab_api._MetricsStore())

    app = lab_api.create_app()
    app.dependency_overrides[get_db_session] = override_db_session

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def _signup_and_headers(client: TestClient, *, include_api_key: bool = True) -> dict[str, str]:
    response = client.post(
        "/auth/signup",
        json={"email": "audit@example.com", "password": TEST_ACCOUNT_PASSWORD},
    )
    assert response.status_code == 201
    token = response.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}
    if include_api_key:
        headers["X-API-Key"] = TEST_PROVIDER_CREDENTIAL
    return headers


def _extract_done_event(stream_body: str) -> dict[str, object]:
    marker = "event: done\ndata: "
    start = stream_body.index(marker) + len(marker)
    end = stream_body.index("\n\n", start)
    return json.loads(stream_body[start:end])


def test_run_requires_x_api_key(client: TestClient) -> None:
    headers = _signup_and_headers(client, include_api_key=False)

    response = client.post("/nl2sql-agent/run", headers=headers, json={"input": "select * from users"})

    assert response.status_code == 400
    assert response.json()["detail"] == "Missing x-api-key header."


def test_root_is_public_and_returns_service_metadata(client: TestClient) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "service": "genai-systems-lab-api",
        "status": "ok",
        "health": "/health",
        "catalog": "/llm/catalog",
    }


def test_run_response_contract_and_history_payload(client: TestClient) -> None:
    headers = _signup_and_headers(client)

    response = client.post("/nl2sql-agent/run", headers=headers, json={"input": "select * from users"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert isinstance(payload["output"], str)
    assert isinstance(payload["confidence"], float)
    assert isinstance(payload["latency"], float)
    assert isinstance(payload["session_id"], int)
    assert isinstance(payload["session_memory"], list)
    assert isinstance(payload["used_session_context"], bool)
    assert payload["memory"]
    assert payload["timeline"]
    assert {entry["type"] for entry in payload["memory"]}.issubset({"thought", "action", "observation"})
    assert all({"timestamp", "step", "event", "data"}.issubset(entry) for entry in payload["timeline"])

    history = client.get("/history", headers=headers)
    assert history.status_code == 200
    history_payload = history.json()
    assert history_payload["count"] == 1
    assert history_payload["runs"][0]["project"] == "genai-nl2sql-agent"
    assert history_payload["runs"][0]["success"] is True


def test_stream_validates_input_and_emits_contract(client: TestClient) -> None:
    headers = _signup_and_headers(client)

    invalid = client.get("/stream/nl2sql-agent", headers=headers, params={"input": "   "})
    assert invalid.status_code == 422
    assert invalid.json()["detail"] == "The 'input' field must not be empty."

    with client.stream("GET", "/stream/nl2sql-agent", headers=headers, params={"input": "stream request"}) as response:
        assert response.status_code == 200
        body = "".join(response.iter_text())

    assert "event: step" in body
    assert '"step": "planner"' in body
    assert "event: output" in body
    assert "event: done" in body

    done_payload = _extract_done_event(body)
    assert done_payload["success"] is True
    assert isinstance(done_payload["output"], str)
    assert isinstance(done_payload["confidence"], float)
    assert isinstance(done_payload["latency"], float)
    assert isinstance(done_payload["session_id"], int)
    assert isinstance(done_payload["session_memory"], list)
    assert isinstance(done_payload["used_session_context"], bool)
    assert done_payload["memory"]
    assert done_payload["timeline"]


def test_stream_emits_single_honest_output_frame_not_fake_token_chunks(
    client: TestClient,
) -> None:
    """The SSE stream must not pretend to stream tokens.

    Earlier revisions sliced the already-complete ``result.output`` into
    80-character pieces and emitted each as ``{"token": "..."}`` to mimic
    token-level streaming.  The honest behaviour is to emit the full output
    exactly once, in a single ``event: output`` frame, because the project
    has fully finished generating by the time the frame is sent.
    """
    headers = _signup_and_headers(client)

    with client.stream(
        "GET",
        "/stream/nl2sql-agent",
        headers=headers,
        params={"input": "honest stream"},
    ) as response:
        assert response.status_code == 200
        body = "".join(response.iter_text())

    # No legacy fake-token frames must be emitted.
    assert '"token":' not in body, (
        "stream must not emit fake token chunks — the output is already "
        "complete before any token frame would fire"
    )

    # Exactly one ``event: output`` frame carrying the full output.
    output_frames = [
        frame for frame in body.split("\n\n") if frame.startswith("event: output")
    ]
    assert len(output_frames) == 1, f"expected 1 output frame, got {len(output_frames)}"

    marker = "event: output\ndata: "
    start = body.index(marker) + len(marker)
    end = body.index("\n\n", start)
    output_payload = json.loads(body[start:end])

    assert set(output_payload.keys()) == {"output"}
    assert isinstance(output_payload["output"], str)
    assert output_payload["output"] != ""

    # The output frame must match the final done-frame output exactly —
    # proving the "stream" frame and the "done" frame agree and no slicing
    # has happened between them.
    done_payload = _extract_done_event(body)
    assert output_payload["output"] == done_payload["output"]


def test_guest_run_allows_execution_without_history(client: TestClient) -> None:
    headers = {"X-API-Key": TEST_PROVIDER_CREDENTIAL}

    response = client.post("/nl2sql-agent/run", headers=headers, json={"input": "guest mode"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["session_id"] is None
    assert payload["session_memory"] == []
    assert payload["used_session_context"] is False

    history = client.get("/history", headers=headers)
    assert history.status_code == 401


def test_run_returns_503_when_project_dependency_is_unavailable(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    headers = _signup_and_headers(client)

    def unavailable_run_project(project: str, user_input: str, *, api_key: str, step_emitter=None) -> RunResult:
        raise ProjectUnavailableError(
            "CrewAI-backed projects are unavailable in this deployment because the optional CrewAI runtime is not installed."
        )

    monkeypatch.setattr(lab_api, "run_project", unavailable_run_project)

    response = client.post("/nl2sql-agent/run", headers=headers, json={"input": "select * from users"})

    assert response.status_code == 503
    assert "optional CrewAI runtime is not installed" in response.json()["detail"]


def test_guest_stream_allows_execution_without_session_state(client: TestClient) -> None:
    headers = {"X-API-Key": TEST_PROVIDER_CREDENTIAL}

    with client.stream("GET", "/stream/nl2sql-agent", headers=headers, params={"input": "guest stream"}) as response:
        assert response.status_code == 200
        body = "".join(response.iter_text())

    done_payload = _extract_done_event(body)
    assert done_payload["success"] is True
    assert done_payload["session_id"] is None
    assert done_payload["session_memory"] == []
    assert done_payload["used_session_context"] is False


def test_auth_cookie_supports_browser_session_without_authorization_header(client: TestClient) -> None:
    signup = client.post(
        "/auth/signup",
        json={"email": "cookie@example.com", "password": TEST_ACCOUNT_PASSWORD},
    )
    assert signup.status_code == 201
    assert "genai_systems_lab_session=" in signup.headers.get("set-cookie", "")

    me = client.get("/auth/me")
    assert me.status_code == 200
    assert me.json()["email"] == "cookie@example.com"

    run = client.post(
        "/nl2sql-agent/run",
        headers={"X-API-Key": TEST_PROVIDER_CREDENTIAL},
        json={"input": "cookie-backed auth"},
    )
    assert run.status_code == 200

    history = client.get("/history")
    assert history.status_code == 200
    assert history.json()["count"] == 1

    logout = client.post("/auth/logout")
    assert logout.status_code == 200

    history_after_logout = client.get("/history")
    assert history_after_logout.status_code == 401


def test_session_memory_is_deduped_capped_and_marks_context_usage(client: TestClient) -> None:
    headers = _signup_and_headers(client)

    first = client.post("/nl2sql-agent/run", headers=headers, json={"input": "repeat request"})
    assert first.status_code == 200
    session_id = first.json()["session_id"]

    second = client.post(
        "/nl2sql-agent/run",
        headers=headers,
        json={"input": "repeat request", "session_id": session_id},
    )
    assert second.status_code == 200
    assert second.json()["used_session_context"] is True

    session_state = client.get(f"/session/{session_id}", headers=headers)
    assert session_state.status_code == 200
    assert session_state.json()["entry_count"] == 1

    for index in range(14):
        response = client.post(
            "/nl2sql-agent/run",
            headers=headers,
            json={"input": f"request {index}", "session_id": session_id},
        )
        assert response.status_code == 200

    updated_session = client.get(f"/session/{session_id}", headers=headers)
    assert updated_session.status_code == 200
    payload = updated_session.json()
    assert payload["entry_count"] == 12
    assert len(payload["memory"]) <= 5


def test_explain_requires_byok_and_share_links_round_trip(client: TestClient) -> None:
    headers = _signup_and_headers(client)
    run_response = client.post("/nl2sql-agent/run", headers=headers, json={"input": "share this run"})
    assert run_response.status_code == 200

    history = client.get("/history", headers=headers)
    run_id = history.json()["runs"][0]["id"]

    explain_missing_key = client.post(f"/explain/{run_id}", headers={"Authorization": headers["Authorization"]}, json={})
    assert explain_missing_key.status_code == 400
    assert explain_missing_key.json()["detail"] == "Missing x-api-key header."

    explain = client.post(f"/explain/{run_id}", headers=headers, json={})
    assert explain.status_code == 200
    assert explain.json()["final_outcome"] == "The API returned a structured result."

    shared = client.post(f"/run/{run_id}/share", headers={"Authorization": headers["Authorization"]}, json={})
    assert shared.status_code == 200
    share_token = shared.json()["share_token"]

    shared_run = client.get(f"/shared/{share_token}")
    assert shared_run.status_code == 200
    shared_payload = shared_run.json()
    assert shared_payload["id"] == run_id
    assert shared_payload["project"] == "genai-nl2sql-agent"
    assert shared_payload["memory"]
    assert shared_payload["timeline"]


def test_metrics_use_canonical_project_names(client: TestClient) -> None:
    headers = _signup_and_headers(client)

    response = client.post("/nl2sql-agent/run", headers=headers, json={"input": "metrics"})
    assert response.status_code == 200

    metrics = client.get("/metrics")
    assert metrics.status_code == 200
    names = {project["name"] for project in metrics.json()["projects"]}
    assert "genai-nl2sql-agent" in names
    assert "nl2sql-agent" not in names


def test_metrics_persist_across_app_restart_for_guest_runs(client: TestClient) -> None:
    response = client.post(
        "/nl2sql-agent/run",
        headers={"X-API-Key": TEST_PROVIDER_CREDENTIAL},
        json={"input": "persist guest metrics"},
    )
    assert response.status_code == 200

    first_metrics = client.get("/metrics")
    assert first_metrics.status_code == 200
    assert first_metrics.json()["total_requests"] == 1

    lab_api.metrics_store = lab_api._MetricsStore()
    restarted_app = lab_api.create_app()
    restarted_app.dependency_overrides[get_db_session] = client.app.dependency_overrides[get_db_session]

    with TestClient(restarted_app) as restarted_client:
        restarted_metrics = restarted_client.get("/metrics")
        assert restarted_metrics.status_code == 200
        restarted_payload = restarted_metrics.json()
        assert restarted_payload["total_requests"] == 1
        assert restarted_payload["projects"][0]["name"] == "genai-nl2sql-agent"

        time_series = restarted_client.get(
            "/metrics/time",
            params={"project": "nl2sql-agent", "range": "day"},
        )
        assert time_series.status_code == 200
        points = time_series.json()
        assert len(points) == 1
        assert points[0]["success"] is True
        assert points[0]["confidence"] > 0


def test_app_startup_bootstraps_otel_when_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    called: dict[str, object] = {}

    def fake_setup_otel(**kwargs: object) -> bool:
        called["setup"] = kwargs
        return True

    def fake_shutdown_otel() -> None:
        called["shutdown"] = True

    monkeypatch.setenv("OTEL_ENABLED", "true")
    monkeypatch.setattr(lab_api, "init_db", lambda: None)
    monkeypatch.setattr(lab_api, "setup_otel", fake_setup_otel)
    monkeypatch.setattr(lab_api, "shutdown_otel", fake_shutdown_otel)

    app = lab_api.create_app()
    with TestClient(app) as test_client:
        response = test_client.get("/health")
        assert response.status_code == 200

    assert "setup" in called
    assert called.get("shutdown") is True


def test_cors_allows_local_frontend_origin_only(client: TestClient) -> None:
    allowed = client.options(
        "/auth/login",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert allowed.status_code == 200
    assert allowed.headers.get("access-control-allow-origin") == "http://localhost:3000"

    blocked = client.options(
        "/auth/login",
        headers={
            "Origin": "https://evil.example",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert blocked.headers.get("access-control-allow-origin") is None


# ---------- Removed-surface guardrails ----------


def _route_paths(client: TestClient) -> set[str]:
    return {
        path
        for route in client.app.routes
        if isinstance((path := getattr(route, "path", None)), str)
    }


def test_leaderboard_route_is_gone(client: TestClient) -> None:
    """Leaderboard feature was removed entirely — no dedicated route should exist."""
    assert "/leaderboard" not in _route_paths(client)


def test_no_streamlit_routes(client: TestClient) -> None:
    """Streamlit UI surface was removed — no route prefix should exist."""
    route_paths = _route_paths(client)
    assert all(not path.startswith("/streamlit") for path in route_paths)
    assert all(not path.startswith("/_stcore") for path in route_paths)


# ---------- Auth config contract ----------


def test_auth_config_exposes_signup_flag(client: TestClient) -> None:
    """The /auth/config endpoint must exist and return a public_signup boolean."""
    response = client.get("/auth/config")
    assert response.status_code == 200
    payload = response.json()
    assert "public_signup" in payload
    assert isinstance(payload["public_signup"], bool)


# ---------- Input validation preserves raw prompt text ----------


def test_input_validation_does_not_html_escape_prompt_body(client: TestClient) -> None:
    """Regression guard: InputValidationMiddleware must not mutate string fields.

    A previous iteration of the middleware ``html.escape``-d every string in
    the JSON body, which turned ``O'Brien`` into ``O&#x27;Brien``, corrupted
    SQL/HTML prompts for projects like ``genai-nl2sql-agent``, and poisoned
    persisted run history.  The fake ``run_project`` in this module echoes
    the received ``input`` into both the response ``output`` and the row
    saved to the runs table, so we can assert exact byte-for-byte round-trip.
    """
    headers = _signup_and_headers(client)

    prompt = (
        "O'Brien said \"hello\" & wrote SELECT * FROM users WHERE name='<admin>' "
        "-- a comment;\nnew line\ttab ok"
    )

    response = client.post(
        "/nl2sql-agent/run",
        headers=headers,
        json={"input": prompt},
    )
    assert response.status_code == 200, response.text

    output_payload = json.loads(response.json()["output"])
    # The prompt must reach the project handler untouched.
    assert output_payload["input"] == prompt
    # Smoke-check common entity fingerprints that the old escaper produced.
    for poison in ("&#x27;", "&quot;", "&lt;", "&amp;"):
        assert poison not in output_payload["input"]
        assert poison not in output_payload["summary"]

    # And must be persisted verbatim to run history.
    history = client.get("/history", headers=headers).json()
    assert history["count"] == 1
    persisted_output = json.loads(history["runs"][0]["output"])
    assert persisted_output["input"] == prompt


@pytest.mark.parametrize(
    "prompt",
    [
        # SQL-injection-looking prompt: the old blocklist matched the literal
        # substrings ``UNION SELECT``, ``; DROP ``, and ``-- `` and returned
        # 422, which broke genai-nl2sql-agent entirely.
        "Write a query using UNION SELECT to combine results; DROP the temp table -- done",
        # Inline-JS event handlers: the old blocklist rejected ``onerror=``,
        # ``onclick=``, etc., which broke genai-code-copilot / genai-ui-builder
        # prompts that discussed XSS defensively.
        "Explain why <img src=x onerror=alert(1)> and <a onclick=\"fn()\"> are unsafe in HTML.",
        # <script> tags: same root cause.  The old blocklist treated any
        # mention of ``<script`` as an attack signature.
        "Review this snippet: <script>doThing()</script> and suggest a safer pattern.",
    ],
    ids=["sql_keywords", "inline_event_handlers", "script_tag"],
)
def test_no_regex_blocklist_rejects_legitimate_prompts(client: TestClient, prompt: str) -> None:
    """Regression guard: no WAF-style regex may reject legitimate LLM prompts.

    Historically a ``_SUSPICIOUS_PATTERN`` regex scanned the request body for
    SQL keywords, inline-JS event handlers, and ``<script>`` tags and returned
    422.  That silently broke the three most important projects on the
    platform (nl2sql, code-copilot, debugging-agent).  This test sends prompts
    that trip every historical signature and asserts 200 + verbatim
    round-trip.
    """
    headers = _signup_and_headers(client)

    response = client.post(
        "/nl2sql-agent/run",
        headers=headers,
        json={"input": prompt},
    )
    assert response.status_code == 200, response.text
    output_payload = json.loads(response.json()["output"])
    assert output_payload["input"] == prompt


# ---------- Query-string token is rejected ----------


def test_history_rejects_query_string_token(client: TestClient) -> None:
    """Regression guard: ``?token=...`` must never authenticate a request.

    Query-string tokens leak into server access logs, reverse-proxy logs,
    browser history, and ``Referer`` headers sent to third-party hosts.
    ``get_bearer_token`` / ``get_optional_bearer_token`` only look at the
    ``Authorization`` header and the HttpOnly session cookie; any code that
    re-introduces a query-string fallback is a security regression.
    """
    # Obtain a valid token the legitimate way.
    response = client.post(
        "/auth/signup",
        json={"email": "qs-reject@example.com", "password": TEST_ACCOUNT_PASSWORD},
    )
    assert response.status_code == 201
    valid_token = response.json()["token"]

    # Clear the session cookie that signup set — otherwise the TestClient
    # would silently re-authenticate every subsequent request via the cookie
    # jar, masking whether the query-string fallback is actually being used.
    client.cookies.clear()

    # Pass it only via query string — no Authorization header, no cookie.
    response_qs = client.get(
        "/history",
        params={"token": valid_token, "access_token": valid_token},
    )
    assert response_qs.status_code == 401
    assert response_qs.json()["detail"] == "Authentication required."


def test_stream_rejects_query_string_token(client: TestClient) -> None:
    """Same guard for the SSE streaming route.

    ``/stream/{project}`` allows guest access, so the assertion is not about
    the HTTP status code but about whether the query-string token was used
    to bind the run to the token's owner.  We verify that no ``Authorization``
    header on the request produces the guest-session contract
    (``session_id is None``, empty ``session_memory``) even when a valid
    token is sitting in the query string.
    """
    response = client.post(
        "/auth/signup",
        json={"email": "qs-reject-stream@example.com", "password": TEST_ACCOUNT_PASSWORD},
    )
    assert response.status_code == 201
    valid_token = response.json()["token"]

    # Drop the cookie so the TestClient cannot silently authenticate via it.
    client.cookies.clear()

    response_stream = client.get(
        "/stream/nl2sql-agent",
        params={"input": "select 1", "token": valid_token},
        headers={"X-API-Key": TEST_PROVIDER_CREDENTIAL},
    )
    assert response_stream.status_code == 200
    body = response_stream.text
    done = _extract_done_event(body)
    # Guest contract: no persisted session id, no accumulated memory.  If the
    # query-string token were honoured we'd see the token-owner's session id
    # + their memory echoed back here.
    assert done["session_id"] is None
    assert done["session_memory"] == []


def test_batch_run_offloads_project_execution_to_thread(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Regression guard: the ``/{project}/run`` async route must not call
    ``run_project`` directly — it must offload via ``asyncio.to_thread`` so a
    slow project cannot freeze the worker event loop.

    We verify this by intercepting ``asyncio.to_thread`` in the ``shared.api.app``
    module namespace and recording whether ``run_project`` was scheduled
    through it during a batch ``POST /{project}/run`` request.
    """
    import asyncio

    observed: list[str] = []
    real_to_thread = asyncio.to_thread

    async def recording_to_thread(func, /, *args, **kwargs):
        observed.append(getattr(func, "__name__", repr(func)))
        return await real_to_thread(func, *args, **kwargs)

    monkeypatch.setattr(lab_api.asyncio, "to_thread", recording_to_thread)

    headers = _signup_and_headers(client)
    response = client.post(
        "/nl2sql-agent/run",
        headers=headers,
        json={"input": "select 1"},
    )
    assert response.status_code == 200, response.text
    # The shared fixture monkey-patches ``run_project`` → ``fake_run_project``
    # in the module namespace before the app is built, so the offloaded
    # callable's ``__name__`` reflects the stub.  Either name is acceptable;
    # what we assert is that *some* offload happened for this request.
    assert any(
        name in {"run_project", "fake_run_project"} for name in observed
    ), (
        "POST /{project}/run must route run_project through asyncio.to_thread "
        f"to stay non-blocking; observed offloads: {observed!r}"
    )