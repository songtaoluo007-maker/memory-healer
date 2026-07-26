"""Authoritative gameplay API."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field

from backend.application.game_service import GameService
from backend.domain.game_state import GameState
from backend.engine.world import CONTENT_REGISTRY


router = APIRouter(prefix="/api/game", tags=["game"])
game_service = GameService(CONTENT_REGISTRY)


class ApiRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")


class StateRequest(ApiRequest):
    game_state: GameState


class ExploreRequest(StateRequest):
    hotspot_id: str = Field(min_length=1, max_length=100)
    expected_revision: int = Field(ge=0)


class ChoiceRequest(StateRequest):
    choice_id: str = Field(min_length=1, max_length=100)
    expected_revision: int = Field(ge=0)


@router.get("/new")
def new_game():
    state = game_service.create_game()
    return {
        "state": state,
        "scene_view": game_service.get_scene_view(state),
        "content_version": 1,
    }


@router.post("/scene")
def get_scene(req: StateRequest):
    return game_service.get_scene_view(req.game_state)


@router.post("/explore")
def explore(req: ExploreRequest):
    return game_service.explore(
        req.game_state,
        req.hotspot_id,
        expected_revision=req.expected_revision,
    )


@router.post("/choice")
def record_choice(req: ChoiceRequest):
    return game_service.record_choice(
        req.game_state,
        req.choice_id,
        expected_revision=req.expected_revision,
    )


@router.post("/ending")
def evaluate_ending(req: StateRequest):
    return {"ending": game_service.evaluate_ending(req.game_state)}
