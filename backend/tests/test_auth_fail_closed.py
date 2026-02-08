"""Regression tests for fail-closed auth behavior."""

import os

import pytest
from fastapi.testclient import TestClient

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./data/test-auth-fail-closed.db"

from app.api import agents, executions, integrations, skills
from app.core.config import settings
from app.core.security import verify_api_key
from app.main import app


@pytest.fixture
def restore_auth_settings():
    snapshot = {
        "APP_ENV": settings.APP_ENV,
        "APP_DEBUG": settings.APP_DEBUG,
        "API_KEY": settings.API_KEY,
        "SECRET_KEY": settings.SECRET_KEY,
        "SECRET_KEY_SALT": settings.SECRET_KEY_SALT,
    }
    yield
    for key, value in snapshot.items():
        setattr(settings, key, value)


def test_verify_api_key_allows_missing_key_in_development(restore_auth_settings):
    settings.APP_ENV = "development"
    settings.API_KEY = None

    assert verify_api_key(None) is True


def test_verify_api_key_rejects_missing_key_in_production(restore_auth_settings):
    settings.APP_ENV = "production"
    settings.API_KEY = None

    with pytest.raises(Exception) as exc:
        verify_api_key(None)

    assert getattr(exc.value, "status_code", None) == 401


def test_verify_api_key_rejects_blank_key_in_production(restore_auth_settings):
    settings.APP_ENV = "production"
    settings.API_KEY = "  "

    with pytest.raises(Exception) as exc:
        verify_api_key(None)

    assert getattr(exc.value, "status_code", None) == 401


def test_verify_api_key_rejects_invalid_key_in_production(restore_auth_settings):
    settings.APP_ENV = "production"
    settings.API_KEY = "expected-key"

    with pytest.raises(Exception) as exc:
        verify_api_key("wrong-key")

    assert getattr(exc.value, "status_code", None) == 401


def test_verify_api_key_accepts_valid_key_in_production(restore_auth_settings):
    settings.APP_ENV = "production"
    settings.API_KEY = "expected-key"

    assert verify_api_key("expected-key") is True


def test_protected_routers_keep_verify_api_key_dependency():
    for router in [agents.router, skills.router, integrations.router, executions.router]:
        dependency_targets = [
            getattr(dependency, "dependency", None) for dependency in router.dependencies
        ]
        assert verify_api_key in dependency_targets


def test_health_public_and_api_protected_in_production(restore_auth_settings):
    settings.APP_ENV = "production"
    settings.APP_DEBUG = False
    settings.API_KEY = "test-api-key"
    settings.SECRET_KEY = "this-is-a-long-and-secure-secret-key-value-123"  # noqa: S105
    settings.SECRET_KEY_SALT = b"production-salt-value-at-least-16-bytes"

    with TestClient(app) as client:
        health = client.get("/health")
        agents_response = client.get("/api/agents")

    assert health.status_code == 200
    assert agents_response.status_code == 401
