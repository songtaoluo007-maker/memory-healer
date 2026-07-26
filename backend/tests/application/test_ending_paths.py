from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from backend.application.game_service import GameService
from backend.content.registry import ContentRegistry
from backend.domain.game_state import GameState


DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def build_service() -> GameService:
    return GameService(
        ContentRegistry.load(DATA_DIR),
        now_provider=lambda: datetime(2026, 7, 26, 12, 0, tzinfo=timezone.utc),
    )


def explore_current_scene(
    service: GameService,
    state: GameState,
    *,
    limit: int | None = None,
) -> GameState:
    hotspot_ids = [
        hotspot.id
        for hotspot in service.get_scene_view(state).hotspots
        if hotspot.fragment_id is not None
    ]
    for hotspot_id in hotspot_ids[:limit]:
        state = service.explore(
            state,
            hotspot_id,
            expected_revision=state.revision,
        ).state
    return state


def follow_good_path(service: GameService, stop_after_scene: str) -> GameState:
    choices = {
        "scene_1972": "encourage_art",
        "scene_1990": "talk_to_stranger",
        "scene_2024": "help_elderly",
        "scene_2050": "accept_award",
        "scene_2089": "protect_legacy",
    }
    state = service.create_game()
    while True:
        state = explore_current_scene(service, state)
        if state.current_scene == stop_after_scene:
            return state
        state = service.record_choice(
            state,
            choices[state.current_scene],
            expected_revision=state.revision,
        ).state


LEGAL_ENDING_PATHS = [
    ("tragic", "new"),
    ("bittersweet", "seven_fragments"),
    ("hope", "fourteen_fragments"),
    ("legacy", "complete"),
]


@pytest.mark.parametrize(("ending_id", "path"), LEGAL_ENDING_PATHS)
def test_every_ending_has_a_legal_path(ending_id: str, path: str) -> None:
    service = build_service()
    if path == "new":
        state = service.create_game()
    elif path == "seven_fragments":
        state = service.create_game()
        state = explore_current_scene(service, state)
        state = service.record_choice(
            state,
            "encourage_art",
            expected_revision=state.revision,
        ).state
        state = explore_current_scene(service, state)
    elif path == "fourteen_fragments":
        state = follow_good_path(service, "scene_2050")
    else:
        state = follow_good_path(service, "scene_2089")
        state = service.record_choice(
            state,
            "protect_legacy",
            expected_revision=state.revision,
        ).state

    assert service.evaluate_ending(state).id == ending_id
