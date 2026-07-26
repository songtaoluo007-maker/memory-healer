"""Persistence repositories with explicit credential and concurrency boundaries."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta, timezone
import secrets

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.domain.errors import DomainError
from backend.domain.game_state import GameState
from backend.persistence.models import SaveSlot, User, UserSession
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


class SaveRepository:
    def __init__(
        self,
        db: Session,
        *,
        now_provider: Callable[[], datetime] | None = None,
    ) -> None:
        self.db = db
        self._now = now_provider or (lambda: datetime.now(timezone.utc))

    def write(
        self,
        *,
        user_id: int,
        slot_id: int,
        slot_name: str,
        expected_revision: int,
        state: GameState,
    ) -> SaveSlot:
        existing = self.db.scalar(
            select(SaveSlot)
            .where(SaveSlot.user_id == user_id, SaveSlot.slot_id == slot_id)
            .with_for_update()
        )
        current_revision = existing.save_revision if existing is not None else 0
        if expected_revision != current_revision:
            raise DomainError(
                "GAME_REVISION_CONFLICT",
                "存档已在其他位置更新，请重新载入后再保存",
                details={
                    "expected_revision": expected_revision,
                    "current_revision": current_revision,
                },
            )

        now = _as_utc(self._now())
        serialized = state.model_dump_json()
        if existing is None:
            slot = SaveSlot(
                user_id=user_id,
                slot_id=slot_id,
                slot_name=slot_name,
                game_state=serialized,
                save_revision=1,
                state_schema_version=state.schema_version,
                state_revision=state.revision,
                scene_id=state.current_scene,
                play_time=state.play_time_seconds,
                created_at=now,
                updated_at=now,
            )
            self.db.add(slot)
        else:
            slot = existing
            slot.slot_name = slot_name
            slot.game_state = serialized
            slot.save_revision += 1
            slot.state_schema_version = state.schema_version
            slot.state_revision = state.revision
            slot.scene_id = state.current_scene
            slot.play_time = state.play_time_seconds
            slot.updated_at = now

        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise DomainError(
                "GAME_REVISION_CONFLICT",
                "存档已在其他位置创建或更新，请重新载入后再保存",
                details={"expected_revision": expected_revision},
            ) from exc
        self.db.refresh(slot)
        return slot

    def get(self, *, user_id: int, slot_id: int) -> SaveSlot | None:
        return self.db.scalar(
            select(SaveSlot).where(
                SaveSlot.user_id == user_id,
                SaveSlot.slot_id == slot_id,
            )
        )

    def list_for_user(self, user_id: int) -> list[SaveSlot]:
        return list(
            self.db.scalars(
                select(SaveSlot)
                .where(SaveSlot.user_id == user_id)
                .order_by(SaveSlot.slot_id)
            )
        )

    def delete(self, *, user_id: int, slot_id: int) -> bool:
        slot = self.get(user_id=user_id, slot_id=slot_id)
        if slot is None:
            return False
        self.db.delete(slot)
        self.db.commit()
        return True
