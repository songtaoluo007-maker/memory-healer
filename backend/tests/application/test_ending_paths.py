from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from backend.application.dialogue_service import DialogueService
from backend.application.game_service import GameService
from backend.content.registry import ContentRegistry
from backend.domain.game_state import GameState
from backend.integrations.deepseek import DialogueSuggestion


DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def build_service() -> GameService:
    return GameService(
        ContentRegistry.load(DATA_DIR),
        now_provider=lambda: datetime(2026, 7, 26, 12, 0, tzinfo=timezone.utc),
    )


class CanonicalDialogueClient:
    def suggest(self, _context):
        return DialogueSuggestion(
            reply="我愿意讲讲这段记忆。",
            trust_change=0,
            npc_mood="warm",
            fragment_revealed=None,
            inner_thought="",
        )


def explore_current_scene(
    service: GameService,
    state: GameState,
    *,
    limit: int | None = None,
) -> GameState:
    view = service.get_scene_view(state)
    fragments = view.fragments[:limit]
    hotspots = {
        hotspot.fragment_id: hotspot
        for hotspot in view.hotspots
        if hotspot.fragment_id is not None
    }
    dialogue_service = DialogueService(service.registry, CanonicalDialogueClient())
    for fragment in fragments:
        if fragment.unlock_method == "dialogue":
            state = dialogue_service.chat(
                state,
                npc_id=fragment.unlock_npc_id,
                player_input=fragment.dialogue_prompt,
                expected_revision=state.revision,
            ).state
        else:
            state = service.explore(
                state,
                hotspots[fragment.id].id,
                expected_revision=state.revision,
            ).state
    return state


def confirm_current_scene_hypothesis(
    service: GameService,
    state: GameState,
) -> GameState:
    hypotheses = service.get_scene_view(state).hypotheses
    if not hypotheses:
        return state
    hypothesis_id = {
        "scene_1972": "hypothesis_1972_legacy",
        "scene_1990": "hypothesis_1990_modern_story",
    }[state.current_scene]
    hypothesis = next(item for item in hypotheses if item.id == hypothesis_id)
    return service.confirm_hypothesis(
        state,
        hypothesis.id,
        list(hypothesis.evidence_ids),
        expected_revision=state.revision,
    ).state


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
        state = confirm_current_scene_hypothesis(service, state)
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
        state = confirm_current_scene_hypothesis(service, state)
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
