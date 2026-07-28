from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import create_engine, inspect

from backend import database
from backend.config import ROOT_DIR, Settings
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


def test_application_startup_never_creates_unmigrated_tables(tmp_path, monkeypatch) -> None:
    empty_engine = create_engine(f"sqlite:///{tmp_path / 'empty.db'}")
    monkeypatch.setattr(database, "engine", empty_engine)

    database.init_db()

    assert inspect(empty_engine).get_table_names() == []


def test_voice_settings_have_safe_disabled_defaults() -> None:
    settings = make_settings()

    assert settings.VOICE_PUBLIC_DIR == ROOT_DIR / "data" / "voice_public"
    assert settings.VOICE_SEED_DIR == ROOT_DIR / "data" / "voice_seeds"
    assert settings.VOICE_PRIMARY_ENABLED is False
    assert settings.VOICE_GENERATION_MAX_CONCURRENCY == 1
    assert settings.VOICE_CACHE_MAX_FILES == 500
    assert settings.VOICE_CACHE_MAX_BYTES == 2_147_483_648
    assert settings.COSYVOICE_BASE_URL == "http://127.0.0.1:50000"
    assert settings.COSYVOICE_BRIDGE_TOKEN == ""
    assert settings.COSYVOICE_CONNECT_TIMEOUT_SECONDS == 0.5
    assert settings.COSYVOICE_TOTAL_TIMEOUT_SECONDS == 2.5
    assert settings.COSYVOICE_FAILURE_THRESHOLD == 3
    assert settings.COSYVOICE_COOLDOWN_SECONDS == 30
    assert settings.COSYVOICE_MODEL_REVISION == "Fun-CosyVoice3-0.5B-2512"


def test_voice_settings_create_separate_cache_fixed_and_seed_directories(
    tmp_path,
) -> None:
    public_dir = tmp_path / "public"
    seed_dir = tmp_path / "seeds"

    make_settings(VOICE_PUBLIC_DIR=public_dir, VOICE_SEED_DIR=seed_dir)

    assert (public_dir / "cache").is_dir()
    assert (public_dir / "fixed").is_dir()
    assert seed_dir.is_dir()


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("VOICE_GENERATION_MAX_CONCURRENCY", 0),
        ("VOICE_GENERATION_MAX_CONCURRENCY", 5),
        ("VOICE_CACHE_MAX_FILES", 0),
        ("VOICE_CACHE_MAX_BYTES", 1_048_575),
        ("COSYVOICE_CONNECT_TIMEOUT_SECONDS", 0.09),
        ("COSYVOICE_TOTAL_TIMEOUT_SECONDS", 31),
        ("COSYVOICE_FAILURE_THRESHOLD", 21),
        ("COSYVOICE_COOLDOWN_SECONDS", 0),
    ],
)
def test_voice_settings_reject_unsafe_bounds(field: str, value: object) -> None:
    with pytest.raises(ValidationError):
        make_settings(**{field: value})
