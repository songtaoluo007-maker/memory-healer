from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ContentModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class SceneContent(ContentModel):
    id: str
    title: str
    time_period: str
    location: str
    description: str
    mood: str
    bgm: str | None = None
    npcs: tuple[str, ...]
    fragments: tuple[str, ...]
    exits: dict[str, str] = Field(default_factory=dict)
    triggers: dict[str, str] = Field(default_factory=dict)
    transition_in: str = ""
    transition_out: str = ""
    fallback_asset: str


class NpcContent(ContentModel):
    id: str
    name: str
    title: str
    age: int = Field(ge=0, le=200)
    scene: str
    avatar: str
    personality: str
    background: str
    system_prompt: str
    initial_trust: int = Field(ge=0, le=100)
    fragments_to_reveal: tuple[str, ...]
    fallback_dialogue: str


class FragmentContent(ContentModel):
    id: str
    name: str
    scene: str
    description: str
    unlock_method: Literal["dialogue", "explore", "trust"]
    unlock_hint: str
    memory_text: str
    collected: bool = False


class HotspotContent(ContentModel):
    id: str
    scene_id: str
    label: str
    x: float = Field(ge=0, le=1)
    y: float = Field(ge=0, le=1)
    radius: float = Field(gt=0, le=0.25)
    fragment_id: str | None = None
    npc_id: str | None = None
    interaction: Literal["inspect", "collect", "talk"]
    presentation_event: str


class ChoiceEffects(ContentModel):
    trust_changes: dict[str, int] = Field(default_factory=dict)
    reveal_fragments: tuple[str, ...] = ()
    current_mood: str | None = None


class ChoiceContent(ContentModel):
    id: str
    scene_id: str
    label: str
    target_scene: str | None = None
    is_key: bool = True
    effects: ChoiceEffects = Field(default_factory=ChoiceEffects)


class HypothesisContent(ContentModel):
    id: str
    scene_id: str
    question: str = Field(min_length=1, max_length=120)
    statement: str = Field(min_length=1, max_length=300)
    evidence_ids: tuple[str, ...] = Field(min_length=2)
    resolution: str = Field(min_length=1, max_length=200)


class EndingConditions(ContentModel):
    min_collected_ratio: float = Field(ge=0, le=1)
    min_key_choices: int = Field(ge=0)
    required_npc_trust: dict[str, int] = Field(default_factory=dict)


class EndingContent(ContentModel):
    id: Literal["legacy", "hope", "bittersweet", "tragic"]
    title: str
    description: str
    priority: int = Field(ge=0)
    conditions: EndingConditions
