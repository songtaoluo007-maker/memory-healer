"""Persistence repositories with explicit credential and concurrency boundaries."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta, timezone
import secrets

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.persistence.models import User, UserSession
from backend.security import generate_session_token, hash_session_token


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


class SessionRepository:
    def __init__(
        self,
        db: Session,
        *,
        now_provider: Callable[[], datetime] | None = None,
    ) -> None:
        self.db = db
        self._now = now_provider or (lambda: datetime.now(timezone.utc))

    def create(self, user_id: int, *, ttl_seconds: int) -> tuple[str, UserSession]:
        raw_token = generate_session_token()
        now = _as_utc(self._now())
        session = UserSession(
            token_hash=hash_session_token(raw_token),
            user_id=user_id,
            created_at=now,
            expires_at=now + timedelta(seconds=ttl_seconds),
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return raw_token, session

    def resolve(self, raw_token: str) -> User | None:
        if not raw_token:
            return None
        token_hash = hash_session_token(raw_token)
        session = self.db.scalar(
            select(UserSession).where(UserSession.token_hash == token_hash)
        )
        if (
            session is None
            or not secrets.compare_digest(session.token_hash, token_hash)
            or session.revoked_at is not None
        ):
            return None

        now = _as_utc(self._now())
        if _as_utc(session.expires_at) <= now:
            session.revoked_at = now
            self.db.commit()
            return None
        return self.db.get(User, session.user_id)

    def revoke(self, raw_token: str) -> bool:
        if not raw_token:
            return False
        session = self.db.scalar(
            select(UserSession).where(
                UserSession.token_hash == hash_session_token(raw_token),
                UserSession.revoked_at.is_(None),
            )
        )
        if session is None:
            return False
        session.revoked_at = _as_utc(self._now())
        self.db.commit()
        return True
