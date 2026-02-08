"""Regression tests for startup security validation in production profile."""

import os

import pytest

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./data/test-startup-validation.db"

from app.core.config import settings, validate_startup_security_settings


@pytest.fixture
def restore_security_settings():
    snapshot = {
        "APP_ENV": settings.APP_ENV,
        "APP_DEBUG": settings.APP_DEBUG,
        "API_KEY": settings.API_KEY,
        "SECRET_KEY": settings.SECRET_KEY,
    }
    yield
    for key, value in snapshot.items():
        setattr(settings, key, value)


def test_development_mode_allows_missing_api_key(restore_security_settings):
    settings.APP_ENV = "development"
    settings.API_KEY = None
    settings.SECRET_KEY = "change-me-in-production-please"  # noqa: S105
    settings.APP_DEBUG = True

    validate_startup_security_settings()


def test_production_requires_api_key(restore_security_settings):
    settings.APP_ENV = "production"
    settings.APP_DEBUG = False
    settings.API_KEY = None
    settings.SECRET_KEY = "this-is-a-long-and-secure-secret-key-value-123"  # noqa: S105

    with pytest.raises(ValueError, match="API_KEY"):
        validate_startup_security_settings()


def test_production_rejects_weak_secret_key(restore_security_settings):
    settings.APP_ENV = "production"
    settings.APP_DEBUG = False
    settings.API_KEY = "prod-api-key"
    settings.SECRET_KEY = "change-me-in-production-please"  # noqa: S105

    with pytest.raises(ValueError, match="SECRET_KEY"):
        validate_startup_security_settings()


def test_production_rejects_debug_mode(restore_security_settings):
    settings.APP_ENV = "production"
    settings.APP_DEBUG = True
    settings.API_KEY = "prod-api-key"
    settings.SECRET_KEY = "this-is-a-long-and-secure-secret-key-value-123"  # noqa: S105

    with pytest.raises(ValueError, match="APP_DEBUG"):
        validate_startup_security_settings()
