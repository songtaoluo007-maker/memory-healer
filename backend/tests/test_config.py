from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from backend.config import Settings
from backend.main import app


def make_settings(**overrides) -> Settings:
    return Settings(_env_file=None, **overrides)


def test_default_database_is_sqlite_and_container_host_is_public() -> None:
    settings = make_settings()

    assert settings.DATABASE_URL.startswith("sqlite:///")
    assert settings.BACKEND_HOST == "0.0.0.0"


def test_supplied_postgresql_url_is_preserved() -> None:
    url = "postgresql+psycopg://memory:secret@postgres:5432/memory"

    settings = make_settings(DATABASE_URL=url)

    assert settings.DATABASE_URL == url


def test_production_rejects_wildcard_cookie_origins() -> None:
    with pytest.raises(ValidationError, match="CORS_ORIGINS"):
        make_settings(ENVIRONMENT="production", CORS_ORIGINS="*")


def test_cookie_secure_defaults_follow_environment() -> None:
    assert make_settings(ENVIRONMENT="development").cookie_secure is False
    assert make_settings(ENVIRONMENT="production").cookie_secure is True
    assert make_settings(ENVIRONMENT="development", COOKIE_SECURE=True).cookie_secure is True


def test_health_response_contains_no_secret_or_capability_disclosure() -> None:
    response = TestClient(app).get("/api/health")

    assert response.status_code == 200
    assert set(response.json()) == {"status", "service", "version", "database"}
    serialized = response.text.lower()
    assert "deepseek" not in serialized
    assert "api_key" not in serialized
    assert "debug" not in serialized
