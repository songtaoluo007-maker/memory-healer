from __future__ import annotations

from datetime import datetime
from typing import Literal, Self
from uuid import UUID, uuid4

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from backend.content.registry import ContentRegistry
from backend.domain.errors import DomainError


DialogueRole = Literal["player", "npc", "system"]
FragmentStatus = Literal["hidden", "revealed", "collected"]
EndingId = Literal["legacy", "hope", "bittersweet", "tragic"]


class DomainModel(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class DialogueMessage(DomainModel):
    role: DialogueRole
    content: str = Field(min_length=1, max_length=1000)
    npc_id: str | None = None
    emotion: str | None = None

    @model_validator(mode="after")
    def npc_messages_require_an_npc(self) -> Self:
        if self.role == "npc" and not self.npc_id:
            raise ValueError("npc dialogue message requires npc_id")
        return self


class KeyChoiceRecord(DomainModel):
    choice_id: str
    scene_id: str
    made_at_revision: int = Field(ge=0)


class FragmentState(DomainModel):
    id: str
    name: str
    scene: str
    status: FragmentStatus = "hidden"
    revealed: bool = False
    collected: bool = False

    @model_validator(mode="after")
    def flags_match_status(self) -> Self:
        expected = {
            "hidden": (False, False),
            "revealed": (True, False),
            "collected": (True, True),
        }[self.status]
        if (self.revealed, self.collected) != expected:
            raise ValueError("fragment status and flags must be consistent")
        return self


class GameState(DomainModel):
    schema_version: Literal[1] = 1
    game_id: UUID = Field(default_factory=uuid4)
    revision: int = Field(default=0, ge=0)
    current_scene: str
    visited_scenes: list[str]
    collected_fragments: list[str] = Field(default_factory=list)
    revealed_fragments: list[str] = Field(default_factory=list)
    fragment_states: dict[str, FragmentState]
    npc_trust: dict[str, int]
    npc_emotions: dict[str, str]
    key_choices: list[KeyChoiceRecord] = Field(default_factory=list)
    butterfly_choices: dict[str, str] = Field(default_factory=dict)
    confirmed_hypotheses: dict[str, str] = Field(default_factory=dict)
    dialogue_history: list[DialogueMessage] = Field(default_factory=list, max_length=60)
    current_mood: str = Field(min_length=1, max_length=50)
    play_time_seconds: int = Field(default=0, ge=0)
    started_at: datetime
    chapter: int = Field(default=1, ge=1, le=5)
    ending: EndingId | None = None

    @field_validator(
        "visited_scenes",
        "collected_fragments",
        "revealed_fragments",
    )
    @classmethod
    def ids_must_be_unique(cls, value: list[str], info) -> list[str]:
        if len(value) != len(set(value)):
            raise ValueError(f"{info.field_name} must not contain duplicates")
        return value

    @field_validator("npc_trust")
    @classmethod
    def trust_must_be_bounded(cls, value: dict[str, int]) -> dict[str, int]:
        if any(trust < 0 or trust > 100 for trust in value.values()):
            raise ValueError("npc_trust values must be between 0 and 100")
        return value

    @field_validator("started_at")
    @classmethod
    def started_at_must_be_timezone_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("started_at must include a timezone")
        return value

    @model_validator(mode="after")
    def state_collections_must_agree(self) -> Self:
        if self.current_scene not in self.visited_scenes:
            raise ValueError("current_scene must be included in visited_scenes")
        if not set(self.collected_fragments).issubset(self.revealed_fragments):
            raise ValueError("collected_fragments must also be revealed")

        for fragment_id, fragment in self.fragment_states.items():
            if fragment_id != fragment.id:
                raise ValueError("fragment_states keys must match fragment ids")
            is_revealed = fragment_id in self.revealed_fragments
            is_collected = fragment_id in self.collected_fragments
            if fragment.revealed != is_revealed or fragment.collected != is_collected:
                raise ValueError(
                    "fragment_states must agree with revealed and collected fragments"
                )
        return self

    @classmethod
    def new(
        cls,
        registry: ContentRegistry,
        now: datetime,
        game_id: UUID | None = None,
    ) -> "GameState":
        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError("now must include a timezone")

        state = cls(
            game_id=game_id or uuid4(),
            current_scene="scene_1972",
            visited_scenes=["scene_1972"],
            fragment_states={
                fragment.id: FragmentState(
                    id=fragment.id,
                    name=fragment.name,
                    scene=fragment.scene,
                )
                for fragment in registry.fragments.values()
            },
            npc_trust={
                npc.id: npc.initial_trust for npc in registry.npcs.values()
            },
            npc_emotions={npc.id: "neutral" for npc in registry.npcs.values()},
            current_mood=registry.get_scene("scene_1972").mood,
            started_at=now,
        )
        state.validate_content_references(registry)
        return state

    def validate_content_references(self, registry: ContentRegistry) -> None:
        if self.current_scene not in registry.scenes:
            raise DomainError(
                "SCENE_NOT_FOUND",
                f"当前场景不存在：{self.current_scene}",
            )
        for scene_id in self.visited_scenes:
            if scene_id not in registry.scenes:
                raise DomainError(
                    "SCENE_NOT_FOUND",
                    f"访问记录中的场景不存在：{scene_id}",
                )

        if set(self.fragment_states) != set(registry.fragments):
            raise DomainError(
                "CONTENT_INVALID",
                "存档碎片集合与当前内容版本不一致",
            )
        for fragment_id in (*self.revealed_fragments, *self.collected_fragments):
            if fragment_id not in registry.fragments:
                raise DomainError(
                    "CONTENT_INVALID",
                    f"存档引用了不存在的碎片：{fragment_id}",
                )

        if set(self.npc_trust) != set(registry.npcs):
            raise DomainError(
                "CONTENT_INVALID",
                "存档 NPC 信任集合与当前内容版本不一致",
            )
        if set(self.npc_emotions) != set(registry.npcs):
            raise DomainError(
                "CONTENT_INVALID",
                "存档 NPC 情绪集合与当前内容版本不一致",
            )

        for record in self.key_choices:
            choice = registry.choices.get(record.choice_id)
            if choice is None or choice.scene_id != record.scene_id:
                raise DomainError(
                    "CHOICE_INVALID",
                    f"存档引用了无效选择：{record.choice_id}",
                )
        for scene_id, choice_id in self.butterfly_choices.items():
            choice = registry.choices.get(choice_id)
            if choice is None or choice.scene_id != scene_id:
                raise DomainError(
                    "CHOICE_INVALID",
                    f"存档引用了无效蝴蝶选择：{choice_id}",
                )

        for scene_id, hypothesis_id in self.confirmed_hypotheses.items():
            hypothesis = registry.hypotheses.get(hypothesis_id)
            if hypothesis is None or hypothesis.scene_id != scene_id:
                raise DomainError(
                    "HYPOTHESIS_INVALID",
                    f"存档引用了无效推理命题：{hypothesis_id}",
                )

        for message in self.dialogue_history:
            if message.npc_id is not None and message.npc_id not in registry.npcs:
                raise DomainError(
                    "CONTENT_INVALID",
                    f"对话记录引用了不存在的 NPC：{message.npc_id}",
                )
        if self.ending is not None and self.ending not in registry.endings:
            raise DomainError(
                "CONTENT_INVALID",
                f"存档引用了不存在的结局：{self.ending}",
            )
