"""Revision-safe, user-isolated save API."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Path
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy.orm import Session

from backend.api.auth import get_current_user
from backend.database import get_db
from backend.domain.errors import DomainError
from backend.domain.game_state import GameState
from backend.engine.world import CONTENT_REGISTRY
from backend.persistence.models import SaveSlot, User
from backend.persistence.repositories import SaveRepository

router = APIRouter(prefix="/api/save", tags=["save"])


class ApiRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SaveRequest(ApiRequest):
    slot_id: int = Field(ge=0, le=10)
    slot_name: str = Field(default="", max_length=50)
    game_state: GameState
    expected_revision: int = Field(ge=0)

    @field_validator("slot_name")
    @classmethod
    def normalize_slot_name(cls, value: str) -> str:
        return value.strip()


class LoadRequest(ApiRequest):
    slot_id: int = Field(ge=0, le=10)


def _summary(slot: SaveSlot) -> dict[str, Any]:
    return {
        "slot_id": slot.slot_id,
        "slot_name": slot.slot_name,
        "scene_id": slot.scene_id,
        "play_time": slot.play_time,
        "save_revision": slot.save_revision,
        "state_revision": slot.state_revision,
        "created_at": slot.created_at.isoformat(),
        "updated_at": slot.updated_at.isoformat(),
        "saved_at": slot.updated_at.isoformat(),
    }


@router.post("/save")
def save_game(
    req: SaveRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    req.game_state.validate_content_references(CONTENT_REGISTRY)
    slot = SaveRepository(db).write(
        user_id=user.id,
        slot_id=req.slot_id,
        slot_name=req.slot_name,
        expected_revision=req.expected_revision,
        state=req.game_state,
    )
    return {"success": True, **_summary(slot)}


@router.post("/load")
def load_game(
    req: LoadRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    slot = SaveRepository(db).get(user_id=user.id, slot_id=req.slot_id)
    if slot is None:
        raise DomainError("SAVE_NOT_FOUND", "存档不存在")
    state = GameState.model_validate_json(slot.game_state)
    state.validate_content_references(CONTENT_REGISTRY)
    return {**_summary(slot), "game_state": state}


@router.get("/list")
def list_saves(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, list[dict[str, Any]]]:
    slots = SaveRepository(db).list_for_user(user.id)
    return {"saves": [_summary(slot) for slot in slots]}


@router.delete("/delete/{slot_id}")
def delete_save(
    slot_id: int = Path(ge=0, le=10),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, bool]:
    deleted = SaveRepository(db).delete(user_id=user.id, slot_id=slot_id)
    if not deleted:
        raise DomainError("SAVE_NOT_FOUND", "存档不存在")
    return {"success": True}
