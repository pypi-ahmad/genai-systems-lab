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

    lab_api.app.dependency_overrides[get_db_session] = override_db_session

    with TestClient(lab_api.app) as test_client:
        yield test_client

    lab_api.app.dependency_overrides.clear()


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


def test_leaderboard_is_public_without_api_key(client: TestClient) -> None:
    response = client.get("/leaderboard")

    assert response.status_code == 200
    assert isinstance(response.json(), list)