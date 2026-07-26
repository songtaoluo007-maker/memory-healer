from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.database import Base, get_db
from backend.main import app
from backend.persistence.models import User, UserSession


@pytest.fixture
def auth_context():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    testing_session = sessionmaker(bind=engine, expire_on_commit=False)
    db = testing_session()

    def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    client = TestClient(app)
    try:
        yield client, db
    finally:
        client.close()
        app.dependency_overrides.clear()
        db.close()


def register(client: TestClient, username: str = "memorykeeper"):
    return client.post(
        "/api/auth/register",
        json={
            "username": username,
            "password": "correct-horse",
            "nickname": "守忆人",
        },
    )


def test_registration_sets_secure_cookie_and_hides_raw_token(auth_context) -> None:
    client, db = auth_context

    response = register(client)

    assert response.status_code == 200
    assert response.json() == {
        "user_id": 1,
        "username": "memorykeeper",
        "nickname": "守忆人",
    }
    cookie = response.headers["set-cookie"]
    assert "memory_session=" in cookie
    assert "HttpOnly" in cookie
    assert "SameSite=lax" in cookie
    user = db.scalar(select(User).where(User.username == "memorykeeper"))
    session = db.scalar(select(UserSession).where(UserSession.user_id == user.id))
    assert user.password_hash.startswith("$argon2id$")
    assert len(session.token_hash) == 64
    assert session.token_hash not in cookie


def test_cookie_authenticates_me_and_logout_revokes(auth_context) -> None:
    client, _db = auth_context
    register(client)

    me_response = client.get("/api/auth/me")
    logout_response = client.post("/api/auth/logout")
    logged_out_response = client.get("/api/auth/me")

    assert me_response.status_code == 200
    assert me_response.json()["username"] == "memorykeeper"
    assert logout_response.status_code == 200
    assert "memory_session=" in logout_response.headers["set-cookie"]
    assert "Max-Age=0" in logout_response.headers["set-cookie"]
    assert logged_out_response.status_code == 401
    assert logged_out_response.json()["error"]["code"] == "AUTH_REQUIRED"


def test_expired_cookie_session_is_rejected(auth_context) -> None:
    client, db = auth_context
    register(client)
    session = db.scalar(select(UserSession))
    session.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    db.commit()

    response = client.get("/api/auth/me")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTH_REQUIRED"


def test_duplicate_username_returns_stable_conflict(auth_context) -> None:
    client, _db = auth_context
    register(client)

    response = register(client)

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "USERNAME_TAKEN"


def test_invalid_credentials_use_one_generic_error(auth_context) -> None:
    client, _db = auth_context
    register(client)
    client.cookies.clear()

    wrong_password = client.post(
        "/api/auth/login",
        json={"username": "memorykeeper", "password": "wrong-password"},
    )
    unknown_user = client.post(
        "/api/auth/login",
        json={"username": "not-a-user", "password": "wrong-password"},
    )

    assert wrong_password.status_code == 401
    assert unknown_user.status_code == 401
    assert wrong_password.json() == unknown_user.json()
    assert wrong_password.json()["error"]["code"] == "INVALID_CREDENTIALS"
