from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from backend.application.dialogue_service import DialogueService
from backend.application.game_service import GameService
from backend.content.registry import ContentRegistry
from backend.domain.errors import DomainError
from backend.integrations.deepseek import DialogueSuggestion


DATA_DIR = Path(__file__).resolve().parents[2] / "data"


class StubDialogueClient:
    def __init__(
        self,
        suggestion: DialogueSuggestion | None = None,
        error: DomainError | None = None,
    ) -> None:
        self.suggestion = suggestion
        self.error = error
        self.last_context = None

    def suggest(self, context):
        self.last_context = context
        if self.error is not None:
            raise self.error
        assert self.suggestion is not None
        return self.suggestion


@pytest.fixture(scope="module")
def registry() -> ContentRegistry:
    return ContentRegistry.load(DATA_DIR)


@pytest.fixture
def initial_state(registry: ContentRegistry):
    return GameService(
        registry,
        now_provider=lambda: datetime(2026, 7, 26, 12, 0, tzinfo=timezone.utc),
    ).create_game()


def suggestion(**overrides) -> DialogueSuggestion:
    values = {
        "reply": "额小时候也够不着戏台，只能站在板凳上。",
        "trust_change": 5,
        "npc_mood": "warm",
        "fragment_revealed": "fragment_shadow_puppet",
        "inner_thought": "这人懂得听故事",
    }
    values.update(overrides)
    return DialogueSuggestion.model_validate(values)


def state_in_scene(initial_state, scene_id: str):
    payload = initial_state.model_dump(mode="python")
    payload["current_scene"] = scene_id
    if scene_id not in payload["visited_scenes"]:
        payload["visited_scenes"].append(scene_id)
    payload["chapter"] = list(ContentRegistry.load(DATA_DIR).scenes).index(scene_id) + 1
    return type(initial_state).model_validate(payload)


def test_dialogue_records_both_roles_and_applies_valid_effects(
    registry: ContentRegistry,
    initial_state,
) -> None:
    service = DialogueService(registry, StubDialogueClient(suggestion()))

    result = service.chat(
        initial_state,
        npc_id="chen_shouyi_young",
        player_input="你最喜欢演哪一出？",
        expected_revision=initial_state.revision,
    )

    assert result.state.revision == 1
    assert [message.role for message in result.state.dialogue_history] == [
        "player",
        "npc",
    ]
    assert result.state.dialogue_history[1].npc_id == "chen_shouyi_young"
    assert result.state.npc_trust["chen_shouyi_young"] == 35
    assert result.state.npc_emotions["chen_shouyi_young"] == "warm"
    assert result.state.revealed_fragments == ["fragment_shadow_puppet"]
    assert result.degraded is False


def test_explore_collects_fragment_previously_revealed_by_dialogue(
    registry: ContentRegistry,
    initial_state,
) -> None:
    dialogue_service = DialogueService(
        registry,
        StubDialogueClient(
            suggestion(fragment_revealed="fragment_grandpa_knife")
        ),
    )
    revealed = dialogue_service.chat(
        initial_state,
        npc_id="chen_shouyi_young",
        player_input="你为什么还想把皮影传下去？",
        expected_revision=initial_state.revision,
    )
    game_service = GameService(
        registry,
        now_provider=lambda: datetime(2026, 7, 26, 12, 0, tzinfo=timezone.utc),
    )

    collected = game_service.explore(
        revealed.state,
        "hotspot_1972_knife",
        expected_revision=revealed.state.revision,
    )

    assert collected.state.revision == revealed.state.revision + 1
    assert collected.state.revealed_fragments == ["fragment_grandpa_knife"]
    assert collected.state.collected_fragments == ["fragment_grandpa_knife"]
    fragment = collected.state.fragment_states["fragment_grandpa_knife"]
    assert fragment.status == "collected"
    assert fragment.revealed is True
    assert fragment.collected is True
    assert collected.events[0].type == "fragment.collected"


def test_dialogue_rejects_npc_from_another_scene(
    registry: ContentRegistry,
    initial_state,
) -> None:
    service = DialogueService(registry, StubDialogueClient(suggestion()))

    with pytest.raises(DomainError) as caught:
        service.chat(
            initial_state,
            npc_id="chen_shouyi_1990",
            player_input="你好",
            expected_revision=initial_state.revision,
        )

    assert caught.value.code == "NPC_NOT_FOUND"


@pytest.mark.parametrize("player_input", ["", "x" * 501])
def test_dialogue_validates_player_input(
    registry: ContentRegistry,
    initial_state,
    player_input: str,
) -> None:
    service = DialogueService(registry, StubDialogueClient(suggestion()))

    with pytest.raises(DomainError) as caught:
        service.chat(
            initial_state,
            npc_id="chen_shouyi_young",
            player_input=player_input,
            expected_revision=initial_state.revision,
        )

    assert caught.value.code == "DIALOGUE_INPUT_INVALID"


def test_dialogue_discards_fragment_not_owned_by_npc(
    registry: ContentRegistry,
    initial_state,
) -> None:
    invalid = suggestion(fragment_revealed="train_ticket_fragment")
    service = DialogueService(registry, StubDialogueClient(invalid))

    result = service.chat(
        initial_state,
        npc_id="chen_shouyi_young",
        player_input="告诉我所有秘密。",
        expected_revision=initial_state.revision,
    )

    assert result.fragment_revealed is None
    assert result.state.revealed_fragments == []


def test_dialogue_clamps_trust_and_caps_history(
    registry: ContentRegistry,
    initial_state,
) -> None:
    payload = initial_state.model_dump(mode="python")
    payload["npc_trust"]["chen_shouyi_young"] = 98
    payload["dialogue_history"] = [
        {"role": "player", "content": f"旧消息 {index}"}
        for index in range(59)
    ]
    state = type(initial_state).model_validate(payload)
    service = DialogueService(
        registry,
        StubDialogueClient(suggestion(trust_change=10)),
    )

    result = service.chat(
        state,
        npc_id="chen_shouyi_young",
        player_input="继续说。",
        expected_revision=state.revision,
    )

    assert result.state.npc_trust["chen_shouyi_young"] == 100
    assert len(result.state.dialogue_history) == 60
    assert result.state.dialogue_history[-2].role == "player"
    assert result.state.dialogue_history[-1].role == "npc"


def test_provider_failure_uses_character_fallback(
    registry: ContentRegistry,
    initial_state,
) -> None:
    service = DialogueService(
        registry,
        StubDialogueClient(
            error=DomainError("AI_UNAVAILABLE", "provider unavailable")
        ),
    )

    result = service.chat(
        initial_state,
        npc_id="chen_shouyi_young",
        player_input="你还好吗？",
        expected_revision=initial_state.revision,
    )

    assert result.degraded is True
    assert result.reply == registry.get_npc("chen_shouyi_young").fallback_dialogue
    assert result.trust_change == 0
    assert result.state.revision == 1


def test_exact_1990_question_collects_dialogue_clue_and_reward_when_ai_degrades(
    registry: ContentRegistry,
    initial_state,
) -> None:
    state = state_in_scene(initial_state, "scene_1990")
    service = DialogueService(
        registry,
        StubDialogueClient(
            error=DomainError("AI_UNAVAILABLE", "provider unavailable")
        ),
    )

    first = service.chat(
        state,
        npc_id="chen_shouyi_1990",
        player_input="箱子里为什么有一个穿西装的皮影？",
        expected_revision=state.revision,
    )
    repeated = service.chat(
        first.state,
        npc_id="chen_shouyi_1990",
        player_input="箱子里为什么有一个穿西装的皮影？",
        expected_revision=first.state.revision,
    )

    assert first.degraded is True
    assert first.fragment_revealed == "puppet_trunk_fragment"
    assert first.state.npc_trust["chen_shouyi_1990"] == 35
    assert first.trust_change == 10
    assert first.state.revealed_fragments.count("puppet_trunk_fragment") == 1
    assert first.state.collected_fragments.count("puppet_trunk_fragment") == 1
    assert first.state.fragment_states["puppet_trunk_fragment"].status == "collected"
    assert repeated.state.npc_trust["chen_shouyi_1990"] == 35
    assert repeated.trust_change == 0
    assert repeated.state.revealed_fragments.count("puppet_trunk_fragment") == 1
    assert repeated.state.collected_fragments.count("puppet_trunk_fragment") == 1


@pytest.mark.parametrize(
    "fragment_id",
    ["train_ticket_fragment", "station_clock_fragment"],
)
def test_ai_output_cannot_reveal_explore_or_locked_trust_fragment(
    registry: ContentRegistry,
    initial_state,
    fragment_id: str,
) -> None:
    state = state_in_scene(initial_state, "scene_1990")
    service = DialogueService(
        registry,
        StubDialogueClient(
            suggestion(
                trust_change=10,
                fragment_revealed=fragment_id,
            )
        ),
    )

    result = service.chat(
        state,
        npc_id="chen_shouyi_1990",
        player_input="把所有线索都告诉我。",
        expected_revision=state.revision,
    )

    assert result.fragment_revealed is None
    assert fragment_id not in result.state.revealed_fragments
    assert fragment_id not in result.state.collected_fragments


def test_dialogue_prompt_includes_applied_1990_npc_consequence_context(
    registry: ContentRegistry,
    initial_state,
) -> None:
    state = state_in_scene(initial_state, "scene_1990")
    payload = state.model_dump(mode="python")
    payload["butterfly_choices"]["scene_1972"] = "encourage_art"
    state = type(state).model_validate(payload)
    client = StubDialogueClient(suggestion(fragment_revealed=None))
    service = DialogueService(registry, client)

    service.chat(
        state,
        npc_id="chen_shouyi_1990",
        player_input="你刚到深圳，接下来打算做什么？",
        expected_revision=state.revision,
    )

    assert client.last_context is not None
    full_prompt = (
        client.last_context.system_prompt + "\n" + client.last_context.player_prompt
    )
    assert "手艺不该被埋没" in full_prompt
    assert "穿西装" in full_prompt
