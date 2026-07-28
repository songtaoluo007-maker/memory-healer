from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from backend.application.game_service import GameService
from backend.content.registry import ContentRegistry
from backend.domain.errors import DomainError
from backend.domain.game_state import GameState


DATA_DIR = Path(__file__).resolve().parents[2] / "data"


@pytest.fixture(scope="module")
def registry() -> ContentRegistry:
    return ContentRegistry.load(DATA_DIR)


@pytest.fixture
def service(registry: ContentRegistry) -> GameService:
    return GameService(
        registry,
        now_provider=lambda: datetime(2026, 7, 26, 12, 0, tzinfo=timezone.utc),
    )


def collect_first_act_evidence(service: GameService, state: GameState) -> GameState:
    for hotspot_id in ("hotspot_1972_knife", "hotspot_1972_shadow_stage"):
        state = service.explore(
            state,
            hotspot_id,
            expected_revision=state.revision,
        ).state
    return state


def test_scene_view_contains_only_canonical_current_scene_content(
    service: GameService,
) -> None:
    state = service.create_game()

    view = service.get_scene_view(state)

    assert view.scene.id == "scene_1972"
    assert {hotspot.scene_id for hotspot in view.hotspots} == {"scene_1972"}
    assert {choice.scene_id for choice in view.choices} == {"scene_1972"}
    assert {hypothesis.id for hypothesis in view.hypotheses} == {
        "hypothesis_1972_legacy"
    }
    assert {fragment.id for fragment in view.fragments} == {
        "fragment_shadow_puppet",
        "fragment_grandpa_knife",
        "fragment_three_kings",
    }


def test_explore_rejects_hotspot_from_another_scene(service: GameService) -> None:
    state = service.create_game()

    with pytest.raises(DomainError) as caught:
        service.explore(
            state,
            "hotspot_1990_train_ticket",
            expected_revision=state.revision,
        )

    assert caught.value.code == "HOTSPOT_INVALID"


def test_explore_rejects_a_stale_revision(service: GameService) -> None:
    state = service.create_game()

    with pytest.raises(DomainError) as caught:
        service.explore(
            state,
            "hotspot_1972_knife",
            expected_revision=9,
        )

    assert caught.value.code == "GAME_REVISION_CONFLICT"


def test_explore_collects_canonical_fragment_and_increments_once(
    service: GameService,
) -> None:
    state = service.create_game()

    result = service.explore(
        state,
        "hotspot_1972_knife",
        expected_revision=state.revision,
    )

    assert result.state.revision == 1
    assert result.state.collected_fragments == ["fragment_grandpa_knife"]
    assert result.state.revealed_fragments == ["fragment_grandpa_knife"]
    fragment = result.state.fragment_states["fragment_grandpa_knife"]
    assert fragment.status == "collected"
    assert fragment.revealed is True
    assert fragment.collected is True
    assert result.events[0].type == "fragment.collected"


def test_repeated_exploration_is_idempotent(service: GameService) -> None:
    state = service.create_game()
    first = service.explore(
        state,
        "hotspot_1972_knife",
        expected_revision=state.revision,
    )

    second = service.explore(
        first.state,
        "hotspot_1972_knife",
        expected_revision=first.state.revision,
    )

    assert second.state.revision == first.state.revision
    assert second.state.collected_fragments == ["fragment_grandpa_knife"]
    assert second.events == []


def test_confirm_hypothesis_records_authoritative_scene_reasoning(
    service: GameService,
) -> None:
    state = collect_first_act_evidence(service, service.create_game())

    result = service.confirm_hypothesis(
        state,
        "hypothesis_1972_legacy",
        ["fragment_grandpa_knife", "fragment_shadow_puppet"],
        expected_revision=state.revision,
    )

    assert result.state.revision == state.revision + 1
    assert result.state.confirmed_hypotheses == {
        "scene_1972": "hypothesis_1972_legacy"
    }
    assert result.events[0].type == "hypothesis.confirmed"
    assert result.events[0].payload["evidence_ids"] == [
        "fragment_grandpa_knife",
        "fragment_shadow_puppet",
    ]


def test_confirm_hypothesis_requires_collected_evidence(service: GameService) -> None:
    state = service.create_game()

    with pytest.raises(DomainError) as caught:
        service.confirm_hypothesis(
            state,
            "hypothesis_1972_legacy",
            ["fragment_grandpa_knife", "fragment_shadow_puppet"],
            expected_revision=state.revision,
        )

    assert caught.value.code == "EVIDENCE_NOT_COLLECTED"


def test_confirm_hypothesis_rejects_incorrect_evidence(service: GameService) -> None:
    state = collect_first_act_evidence(service, service.create_game())

    with pytest.raises(DomainError) as caught:
        service.confirm_hypothesis(
            state,
            "hypothesis_1972_legacy",
            ["fragment_grandpa_knife", "fragment_three_kings"],
            expected_revision=state.revision,
        )

    assert caught.value.code == "EVIDENCE_INVALID"


def test_choice_requires_confirmed_scene_hypothesis(service: GameService) -> None:
    state = service.create_game()

    with pytest.raises(DomainError) as caught:
        service.record_choice(
            state,
            "encourage_art",
            expected_revision=state.revision,
        )

    assert caught.value.code == "HYPOTHESIS_REQUIRED"


def test_choice_records_standardized_effects_and_transition(
    service: GameService,
) -> None:
    state = collect_first_act_evidence(service, service.create_game())
    state = service.confirm_hypothesis(
        state,
        "hypothesis_1972_legacy",
        ["fragment_grandpa_knife", "fragment_shadow_puppet"],
        expected_revision=state.revision,
    ).state

    result = service.record_choice(
        state,
        "encourage_art",
        expected_revision=state.revision,
    )

    assert result.state.revision == state.revision + 1
    assert result.state.current_scene == "scene_1990"
    assert result.state.visited_scenes == ["scene_1972", "scene_1990"]
    assert result.state.npc_trust["chen_shouyi_young"] == 65
    assert result.state.butterfly_choices == {"scene_1972": "encourage_art"}
    assert result.state.key_choices[0].choice_id == "encourage_art"
    assert result.state.key_choices[0].scene_id == "scene_1972"
    assert result.state.revealed_fragments == [
        "fragment_grandpa_knife",
        "fragment_shadow_puppet",
        "fragment_three_kings",
    ]
    assert result.events[-1].type == "scene.entered"


def test_choice_must_belong_to_current_scene(service: GameService) -> None:
    state = service.create_game()

    with pytest.raises(DomainError) as caught:
        service.record_choice(
            state,
            "talk_to_stranger",
            expected_revision=state.revision,
        )

    assert caught.value.code == "CHOICE_INVALID"
