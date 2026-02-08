"""Regression tests for secret redaction and masking behavior."""

import os
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./data/test-secret-redaction.db"

from app.core.config import settings
from app.core.database import get_db
from app.core.security import REDACTED_VALUE, redact_sensitive_data
from app.main import app


@pytest.fixture
def restore_settings():
    snapshot = {
        "APP_ENV": settings.APP_ENV,
        "APP_DEBUG": settings.APP_DEBUG,
        "API_KEY": settings.API_KEY,
        "SECRET_KEY": settings.SECRET_KEY,
    }
    yield
    for key, value in snapshot.items():
        setattr(settings, key, value)


def test_redact_sensitive_data_handles_nested_payloads():
    payload = {
        "api_key": "sk-live-super-secret",
        "nested": {
            "token": "abc123",
            "safe": "ok",
        },
        "items": [{"password": "hello"}, {"label": "plain"}],
        "message": "authorization: Bearer my-token-value",
    }

    redacted = redact_sensitive_data(payload)

    assert redacted["api_key"] == REDACTED_VALUE
    assert redacted["nested"]["token"] == REDACTED_VALUE
    assert redacted["nested"]["safe"] == "ok"
    assert redacted["items"][0]["password"] == REDACTED_VALUE
    assert redacted["items"][1]["label"] == "plain"
    assert "my-token-value" not in redacted["message"]


@pytest.mark.asyncio
async def test_agent_executor_emit_log_redacts_secret_values():
    from app.runtime.agent_executor import AgentExecutor

    captured = []

    async def callback(entry):
        captured.append(entry)

    executor = AgentExecutor(SimpleNamespace())
    executor.add_log_callback(callback)
    await executor._emit_log("exec-1", "info", "token=supersecret-value")

    assert len(captured) == 1
    assert captured[0]["message"] == f"token={REDACTED_VALUE}"


def test_run_agent_route_redacts_response_and_strips_api_keys(monkeypatch, restore_settings):
    settings.APP_ENV = "development"
    settings.API_KEY = None

    class FakeDBResult:
        def scalar_one_or_none(self):
            return SimpleNamespace(id="agent-1", name="Redaction Agent")

    class FakeDBSession:
        async def execute(self, _query):
            return FakeDBResult()

    captured = {}

    class FakeAgentExecutor:
        def __init__(self, db):
            self.db = db

        def add_log_callback(self, _callback):
            pass

        async def execute(self, agent_id, input_data=None, trigger="manual", api_keys=None):
            captured["agent_id"] = agent_id
            captured["input_data"] = input_data
            captured["api_keys"] = api_keys
            return SimpleNamespace(
                id="exec-1",
                status="success",
                output_data={"token": "top-secret-token", "result": "ok"},
            )

    async def fake_get_db():
        yield FakeDBSession()

    monkeypatch.setattr("app.runtime.agent_executor.AgentExecutor", FakeAgentExecutor)
    app.dependency_overrides[get_db] = fake_get_db

    with TestClient(app) as client:
        response = client.post(
            "/api/agents/agent-1/run",
            json={
                "message": "hello",
                "api_keys": {"openai": "sk-from-request"},
                "token": "user-visible",
            },
        )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert captured["api_keys"] == {"openai": "sk-from-request"}
    assert "api_keys" not in (captured["input_data"] or {})
    assert response.json()["output"]["token"] == REDACTED_VALUE
