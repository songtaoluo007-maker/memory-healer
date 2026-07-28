from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

import pytest
from pydantic import ValidationError

from backend.content.registry import ContentRegistry
from backend.domain.errors import DomainError
from backend.domain.game_state import GameState


DATA_DIR = Path(__file__).resolve().parents[2] / "data"
EXPECTED_FIELDS = {
    "schema_version",
    "game_id",
    "revision",
    "current_scene",
    "visited_scenes",
    "collected_fragments",
    "revealed_fragments",
    "fragment_states",
    "npc_trust",
    "npc_emotions",
    "key_choices",
    "butterfly_choices",
    "confirmed_hypotheses",
    "dialogue_history",
    "current_mood",
    "play_time_seconds",
    "started_at",
    "chapter",
    "ending",
}


@pytest.fixture(scope="module")
def registry() -> ContentRegistry:
    return ContentRegistry.load(DATA_DIR)


@pytest.fixture
def fixed_now() -> datetime:
    return datetime(2026, 7, 26, 12, 0, tzinfo=timezone.utc)


def test_initial_state_has_versioned_contract(
    registry: ContentRegistry,
    fixed_now: datetime,
) -> None:
    state = GameState.new(registry, fixed_now, UUID(int=1))
    payload = state.model_dump(mode="json")

    assert set(payload) == EXPECTED_FIELDS
    assert payload["schema_version"] == 1
    assert payload["game_id"] == "00000000-0000-0000-0000-000000000001"
    assert payload["revision"] == 0
    assert payload["current_scene"] == "scene_1972"
    assert payload["visited_scenes"] == ["scene_1972"]
    assert payload["started_at"] == "2026-07-26T12:00:00Z"
    assert len(payload["fragment_states"]) == 17
    assert set(payload["npc_trust"]) == set(registry.npcs)
    assert set(payload["npc_emotions"]) == set(registry.npcs)
    assert payload["confirmed_hypotheses"] == {}


def test_initial_state_has_no_confirmed_hypotheses(
    registry: ContentRegistry,
    fixed_now: datetime,
) -> None:
    state = GameState.new(registry, fixed_now, UUID(int=9))

    assert state.confirmed_hypotheses == {}


def test_initial_fragments_are_hidden_and_consistent(
    registry: ContentRegistry,
    fixed_now: datetime,
) -> None:
    state = GameState.new(registry, fixed_now, UUID(int=2))

    assert state.collected_fragments == []
    assert state.revealed_fragments == []
    assert all(fragment.status == "hidden" for fragment in state.fragment_states.values())
    assert all(not fragment.revealed for fragment in state.fragment_states.values())
    assert all(not fragment.collected for fragment in state.fragment_states.values())


def test_unknown_state_fields_are_rejected(
    registry: ContentRegistry,
    fixed_now: datetime,
) -> None:
    payload = GameState.new(registry, fixed_now, UUID(int=3)).model_dump(mode="json")
    payload["client_modal"] = "inventory"

    with pytest.raises(ValidationError):
        GameState.model_validate(payload)


def test_duplicate_state_ids_are_rejected(
    registry: ContentRegistry,
    fixed_now: datetime,
) -> None:
    payload = GameState.new(registry, fixed_now, UUID(int=4)).model_dump(mode="json")
    payload["visited_scenes"] = ["scene_1972", "scene_1972"]

    with pytest.raises(ValidationError, match="visited_scenes"):
        GameState.model_validate(payload)


def test_collected_fragments_must_also_be_revealed(
    registry: ContentRegistry,
    fixed_now: datetime,
) -> None:
    payload = GameState.new(registry, fixed_now, UUID(int=5)).model_dump(mode="json")
    payload["collected_fragments"] = ["fragment_grandpa_knife"]

    with pytest.raises(ValidationError, match="collected_fragments"):
        GameState.model_validate(payload)


def test_trust_must_stay_between_zero_and_one_hundred(
    registry: ContentRegistry,
    fixed_now: datetime,
) -> None:
    payload = GameState.new(registry, fixed_now, UUID(int=6)).model_dump(mode="json")
    payload["npc_trust"]["chen_shouyi_young"] = 101

    with pytest.raises(ValidationError, match="npc_trust"):
        GameState.model_validate(payload)


def test_started_at_requires_timezone(
    registry: ContentRegistry,
    fixed_now: datetime,
) -> None:
    payload = GameState.new(registry, fixed_now, UUID(int=7)).model_dump(mode="json")
    payload["started_at"] = "2026-07-26T12:00:00"

    with pytest.raises(ValidationError, match="started_at"):
        GameState.model_validate(payload)


def test_content_reference_validation_rejects_unknown_scene(
    registry: ContentRegistry,
    fixed_now: datetime,
) -> None:
    state = GameState.new(registry, fixed_now, UUID(int=8))
    state = state.model_copy(
        update={
            "current_scene": "scene_missing",
            "visited_scenes": ["scene_1972", "scene_missing"],
        }
    )

    with pytest.raises(DomainError) as caught:
        state.validate_content_references(registry)

    assert caught.value.code == "SCENE_NOT_FOUND"
