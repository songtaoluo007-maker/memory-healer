from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.database import Base
from backend.persistence.models import User
from backend.persistence.repositories import SessionRepository
from backend.security import hash_password, hash_session_token


def make_db():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)()


def test_session_repository_stores_only_token_hash() -> None:
    db = make_db()
    user = User(
        username="session_owner",
        password_hash=hash_password("correct-horse"),
        nickname="会话测试",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    now = datetime(2026, 7, 26, 12, 0, tzinfo=timezone.utc)
    repository = SessionRepository(db, now_provider=lambda: now)

    raw_token, session = repository.create(user.id, ttl_seconds=3600)

    assert raw_token not in session.token_hash
    assert session.token_hash == hash_session_token(raw_token)
    assert len(session.token_hash) == 64
    assert repository.resolve(raw_token).id == user.id


def test_expired_and_revoked_sessions_do_not_resolve() -> None:
    db = make_db()
    user = User(
        username="expiring_owner",
        password_hash=hash_password("correct-horse"),
        nickname="过期测试",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    now = datetime(2026, 7, 26, 12, 0, tzinfo=timezone.utc)
    clock = {"now": now}
    repository = SessionRepository(db, now_provider=lambda: clock["now"])

    expired_token, _ = repository.create(user.id, ttl_seconds=60)
    clock["now"] = now + timedelta(seconds=61)
    assert repository.resolve(expired_token) is None

    clock["now"] = now
    revoked_token, _ = repository.create(user.id, ttl_seconds=60)
    assert repository.revoke(revoked_token) is True
    assert repository.resolve(revoked_token) is None
