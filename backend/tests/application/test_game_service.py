from __future__ import annotations

import copy
from datetime import datetime, timezone
import json
from pathlib import Path

import pytest

from backend.application.dialogue_service import DialogueService
from backend.application.game_service import GameService
from backend.content.registry import ContentRegistry
from backend.domain.errors import DomainError
from backend.domain.game_state import GameState
from backend.integrations.deepseek import DialogueSuggestion


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


class CanonicalDialogueClient:
    def suggest(self, _context):
        return DialogueSuggestion(
            reply="额最拿手的是三英战吕布。",
            trust_change=0,
            npc_mood="warm",
            fragment_revealed="fragment_shadow_puppet",
            inner_thought="",
        )


def collect_first_act_evidence(service: GameService, state: GameState) -> GameState:
    state = service.explore(
        state,
        "hotspot_1972_knife",
        expected_revision=state.revision,
    ).state
    state = DialogueService(service.registry, CanonicalDialogueClient()).chat(
        state,
        npc_id="chen_shouyi_young",
        player_input="你最拿手的是哪出皮影戏？",
        expected_revision=state.revision,
    ).state
    return state


def advance_to_1990(
    service: GameService,
    *,
    choice_id: str = "encourage_art",
) -> GameState:
    state = collect_first_act_evidence(service, service.create_game())
    state = service.confirm_hypothesis(
        state,
        "hypothesis_1972_legacy",
        ["fragment_grandpa_knife", "fragment_shadow_puppet"],
        expected_revision=state.revision,
    ).state
    return service.record_choice(
        state,
        choice_id,
        expected_revision=state.revision,
    ).state


def with_npc_trust(state: GameState, npc_id: str, trust: int) -> GameState:
    payload = state.model_dump(mode="python")
    payload["npc_trust"][npc_id] = trust
    return GameState.model_validate(payload)


def load_shipping_documents() -> dict[str, object]:
    filenames = (
        "scenes",
        "npcs",
        "fragments",
        "hotspots",
        "choices",
        "hypotheses",
        "endings",
        "voice_profiles",
        "voice_lines",
        "voice_assets",
    )
    return {
        name: json.loads((DATA_DIR / f"{name}.json").read_text(encoding="utf-8"))
        for name in filenames
    }


def test_choice_requires_its_specified_hypothesis_when_scene_has_another_one() -> None:
    documents = copy.deepcopy(load_shipping_documents())
    choices = documents["choices"]
    hypotheses = documents["hypotheses"]
    assert isinstance(choices, list)
    assert isinstance(hypotheses, list)
    next(choice for choice in choices if choice["id"] == "encourage_art")[
        "requirements"
    ] = [
        {
            "kind": "hypothesis_confirmed",
            "hypothesis_id": "hypothesis_1972_legacy",
        }
    ]
    hypotheses.append(
        {
            "id": "hypothesis_1972_non_required",
            "scene_id": "scene_1972",
            "question": "陈守义是否已经决定南下？",
            "statement": "他仍在犹豫。",
            "evidence_ids": [
                "fragment_grandpa_knife",
                "fragment_shadow_puppet",
            ],
            "resolution": "这不是本次选择所需的推理。",
        }
    )
    custom_service = GameService(
        ContentRegistry.from_documents(documents),
        now_provider=lambda: datetime(2026, 7, 26, 12, 0, tzinfo=timezone.utc),
    )
    state = collect_first_act_evidence(custom_service, custom_service.create_game())
    state = custom_service.confirm_hypothesis(
        state,
        "hypothesis_1972_non_required",
        ["fragment_grandpa_knife", "fragment_shadow_puppet"],
        expected_revision=state.revision,
    ).state

    with pytest.raises(DomainError) as caught:
        custom_service.record_choice(
            state,
            "encourage_art",
            expected_revision=state.revision,
        )

    assert caught.value.code == "HYPOTHESIS_REQUIRED"


def test_choice_without_requirements_does_not_use_scene_hypothesis_gate() -> None:
    documents = load_shipping_documents()
    choices = documents["choices"]
    assert isinstance(choices, list)
    next(choice for choice in choices if choice["id"] == "encourage_art")[
        "requirements"
    ] = []
    custom_service = GameService(
        ContentRegistry.from_documents(documents),
        now_provider=lambda: datetime(2026, 7, 26, 12, 0, tzinfo=timezone.utc),
    )

    result = custom_service.record_choice(
        custom_service.create_game(),
        "encourage_art",
        expected_revision=0,
    )

    assert result.state.current_scene == "scene_1990"


def test_choice_requires_collected_fragment_before_recording() -> None:
    documents = load_shipping_documents()
    choices = documents["choices"]
    assert isinstance(choices, list)
    next(choice for choice in choices if choice["id"] == "encourage_art")[
        "requirements"
    ] = [
        {
            "kind": "fragment_collected",
            "fragment_id": "fragment_grandpa_knife",
        }
    ]
    custom_service = GameService(
        ContentRegistry.from_documents(documents),
        now_provider=lambda: datetime(2026, 7, 26, 12, 0, tzinfo=timezone.utc),
    )
    state = custom_service.create_game()

    with pytest.raises(DomainError) as caught:
        custom_service.record_choice(
            state,
            "encourage_art",
            expected_revision=state.revision,
        )

    assert caught.value.code == "CHOICE_REQUIREMENT_UNMET"

    state = custom_service.explore(
        state,
        "hotspot_1972_knife",
        expected_revision=state.revision,
    ).state
    result = custom_service.record_choice(
        state,
        "encourage_art",
        expected_revision=state.revision,
    )

    assert result.state.current_scene == "scene_1990"


def test_choice_requires_npc_trust_before_recording() -> None:
    documents = load_shipping_documents()
    choices = documents["choices"]
    assert isinstance(choices, list)
    next(choice for choice in choices if choice["id"] == "encourage_art")[
        "requirements"
    ] = [
        {
            "kind": "npc_trust_at_least",
            "npc_id": "chen_shouyi_young",
            "minimum": 60,
        }
    ]
    custom_service = GameService(
        ContentRegistry.from_documents(documents),
        now_provider=lambda: datetime(2026, 7, 26, 12, 0, tzinfo=timezone.utc),
    )
    state = custom_service.create_game()

    with pytest.raises(DomainError) as caught:
        custom_service.record_choice(
            state,
            "encourage_art",
            expected_revision=state.revision,
        )

    assert caught.value.code == "CHOICE_REQUIREMENT_UNMET"

    payload = state.model_dump(mode="python")
    payload["npc_trust"]["chen_shouyi_young"] = 60
    eligible_state = GameState.model_validate(payload)
    result = custom_service.record_choice(
        eligible_state,
        "encourage_art",
        expected_revision=eligible_state.revision,
    )

    assert result.state.npc_trust["chen_shouyi_young"] == 95


def test_recording_same_choice_is_idempotent_after_its_trust_effect() -> None:
    documents = load_shipping_documents()
    choices = documents["choices"]
    assert isinstance(choices, list)
    choice = next(choice for choice in choices if choice["id"] == "protect_legacy")
    choice["requirements"] = [
        {
            "kind": "npc_trust_at_least",
            "npc_id": "xiaoyu",
            "minimum": 50,
        }
    ]
    choice["effects"]["trust_changes"] = {"xiaoyu": -10}
    custom_service = GameService(
        ContentRegistry.from_documents(documents),
        now_provider=lambda: datetime(2026, 7, 26, 12, 0, tzinfo=timezone.utc),
    )
    payload = custom_service.create_game().model_dump(mode="python")
    payload["current_scene"] = "scene_2089"
    payload["visited_scenes"].append("scene_2089")
    payload["chapter"] = 5
    state = GameState.model_validate(payload)
    first = custom_service.record_choice(
        state,
        "protect_legacy",
        expected_revision=state.revision,
    )

    assert first.state.npc_trust["xiaoyu"] == 40

    retry = custom_service.record_choice(
        first.state,
        "protect_legacy",
        expected_revision=first.state.revision,
    )

    assert retry.state == first.state
    assert retry.events == []


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


def test_scene_view_exposes_first_act_voice_references(service: GameService) -> None:
    view = service.get_scene_view(service.create_game())

    assert view.scene.transition_in_voice_line_id == "scene_1972.transition_in"
    chen = next(npc for npc in view.npcs if npc.id == "chen_shouyi_young")
    assert chen.initial_voice_line_id == "npc.chen_shouyi_young.intro"
    knife = next(
        fragment for fragment in view.fragments if fragment.id == "fragment_grandpa_knife"
    )
    assert knife.memory_voice_line_id == "fragment_grandpa_knife.memory"
    hypothesis = next(
        item
        for item in view.hypotheses
        if item.id == "hypothesis_1972_legacy"
    )
    assert (
        hypothesis.resolution_voice_line_id
        == "hypothesis_1972_legacy.resolution"
    )


def test_1990_scene_exposes_two_public_hypotheses_without_server_outcomes(
    service: GameService,
) -> None:
    view = service.get_scene_view(advance_to_1990(service))

    assert [item.id for item in view.hypotheses] == [
        "hypothesis_1990_survival",
        "hypothesis_1990_modern_story",
    ]
    assert all("outcome" not in item.model_dump() for item in view.hypotheses)
    trunk = next(
        item for item in view.fragments if item.id == "puppet_trunk_fragment"
    )
    assert trunk.unlock_npc_id == "chen_shouyi_1990"
    assert trunk.dialogue_prompt == "箱子里为什么有一个穿西装的皮影？"
    assert trunk.dialogue_trust_reward == 10
    clock = next(
        item for item in view.fragments if item.id == "station_clock_fragment"
    )
    assert clock.unlock_npc_id == "chen_shouyi_1990"
    assert clock.minimum_trust == 35


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


def test_clicking_unrevealed_dialogue_fragment_returns_locked_unchanged_state(
    service: GameService,
) -> None:
    state = advance_to_1990(service)

    result = service.explore(
        state,
        "hotspot_1990_puppet_trunk",
        expected_revision=state.revision,
    )

    assert result.state == state
    assert result.events[0].type == "fragment.locked"
    assert result.events[0].content_id == "puppet_trunk_fragment"
    assert result.events[0].payload == {
        "method": "dialogue",
        "hint": "问问陈守义箱子里装了什么",
        "npc_id": "chen_shouyi_1990",
        "prompt": "箱子里为什么有一个穿西装的皮影？",
    }


def test_trust_fragment_locks_below_threshold_and_collects_once_at_threshold(
    service: GameService,
) -> None:
    below_threshold = advance_to_1990(service)

    locked = service.explore(
        below_threshold,
        "hotspot_1990_station_clock",
        expected_revision=below_threshold.revision,
    )

    assert locked.state == below_threshold
    assert locked.events[0].type == "fragment.locked"
    assert locked.events[0].payload["method"] == "trust"
    assert locked.events[0].payload["minimum_trust"] == 35

    eligible = with_npc_trust(below_threshold, "chen_shouyi_1990", 35)
    collected = service.explore(
        eligible,
        "hotspot_1990_station_clock",
        expected_revision=eligible.revision,
    )
    repeated = service.explore(
        collected.state,
        "hotspot_1990_station_clock",
        expected_revision=collected.state.revision,
    )

    assert collected.state.collected_fragments.count("station_clock_fragment") == 1
    assert collected.events[0].type == "fragment.collected"
    assert repeated.state == collected.state
    assert repeated.events == []


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


def test_rejected_1990_hypothesis_returns_feedback_without_consuming_revision(
    service: GameService,
) -> None:
    state = advance_to_1990(service)
    for hotspot_id in (
        "hotspot_1990_train_ticket",
        "hotspot_1990_farewell_letter",
    ):
        state = service.explore(
            state,
            hotspot_id,
            expected_revision=state.revision,
        ).state

    result = service.confirm_hypothesis(
        state,
        "hypothesis_1990_survival",
        ["train_ticket_fragment", "farewell_letter_fragment"],
        expected_revision=state.revision,
    )

    assert result.state == state
    assert result.state.confirmed_hypotheses.get("scene_1990") is None
    assert result.events[0].type == "hypothesis.rejected"
    assert result.events[0].payload["evidence_ids"] == [
        "train_ticket_fragment",
        "farewell_letter_fragment",
    ]
    feedback = result.events[0].payload["feedback"]
    assert "压力" in feedback
    assert "愧疚" in feedback
    assert "穿西装" in feedback
    assert "3:47" in feedback


def test_confirmed_1990_hypothesis_records_scene_reasoning(service: GameService) -> None:
    state = advance_to_1990(service)
    state = DialogueService(
        service.registry,
        CanonicalDialogueClient(),
    ).chat(
        state,
        npc_id="chen_shouyi_1990",
        player_input="箱子里为什么有一个穿西装的皮影？",
        expected_revision=state.revision,
    ).state
    state = service.explore(
        state,
        "hotspot_1990_station_clock",
        expected_revision=state.revision,
    ).state

    result = service.confirm_hypothesis(
        state,
        "hypothesis_1990_modern_story",
        ["puppet_trunk_fragment", "station_clock_fragment"],
        expected_revision=state.revision,
    )

    assert result.state.revision == state.revision + 1
    assert result.state.confirmed_hypotheses["scene_1990"] == (
        "hypothesis_1990_modern_story"
    )
    assert result.events[0].type == "hypothesis.confirmed"


@pytest.mark.parametrize("choice_id", ["talk_to_stranger", "ignore_stranger"])
def test_1990_choices_require_confirmed_modern_story_hypothesis(
    service: GameService,
    choice_id: str,
) -> None:
    state = advance_to_1990(service)
    for hotspot_id in (
        "hotspot_1990_train_ticket",
        "hotspot_1990_farewell_letter",
    ):
        state = service.explore(
            state,
            hotspot_id,
            expected_revision=state.revision,
        ).state
    rejected = service.confirm_hypothesis(
        state,
        "hypothesis_1990_survival",
        ["train_ticket_fragment", "farewell_letter_fragment"],
        expected_revision=state.revision,
    ).state

    with pytest.raises(DomainError) as caught:
        service.record_choice(
            rejected,
            choice_id,
            expected_revision=rejected.revision,
        )

    assert caught.value.code == "HYPOTHESIS_REQUIRED"


@pytest.mark.parametrize(
    ("choice_id", "variant", "text_fragment"),
    [
        ("encourage_art", "legacy_carried", "手艺不该被埋没"),
        ("discourage_art", "legacy_suppressed", "半合"),
    ],
)
def test_1972_choice_derives_one_1990_consequence_without_persisting_it(
    service: GameService,
    choice_id: str,
    variant: str,
    text_fragment: str,
) -> None:
    state = advance_to_1990(service, choice_id=choice_id)

    view = service.get_scene_view(state)

    assert len(view.applied_consequences) == 1
    assert view.applied_consequences[0].variant == variant
    assert text_fragment in view.applied_consequences[0].scene_text
    assert "applied_consequences" not in state.model_dump()


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
