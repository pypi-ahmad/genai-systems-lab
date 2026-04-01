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
from shared.api.runner import RunResult


TEST_API_KEY = "smoke-test-key-1234567890"


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
        assert api_key == TEST_API_KEY
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
        json={"email": "audit@example.com", "password": "password123"},
    )
    assert response.status_code == 201
    token = response.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}
    if include_api_key:
        headers["X-API-Key"] = TEST_API_KEY
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
    assert '"token": ' in body
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


def test_guest_run_allows_execution_without_history(client: TestClient) -> None:
    headers = {"X-API-Key": TEST_API_KEY}

    response = client.post("/nl2sql-agent/run", headers=headers, json={"input": "guest mode"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["session_id"] is None
    assert payload["session_memory"] == []
    assert payload["used_session_context"] is False

    history = client.get("/history", headers=headers)
    assert history.status_code == 401


def test_guest_stream_allows_execution_without_session_state(client: TestClient) -> None:
    headers = {"X-API-Key": TEST_API_KEY}

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
        json={"email": "cookie@example.com", "password": "password123"},
    )
    assert signup.status_code == 201
    assert "genai_systems_lab_session=" in signup.headers.get("set-cookie", "")

    me = client.get("/auth/me")
    assert me.status_code == 200
    assert me.json()["email"] == "cookie@example.com"

    run = client.post(
        "/nl2sql-agent/run",
        headers={"X-API-Key": TEST_API_KEY},
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
        headers={"X-API-Key": TEST_API_KEY},
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