from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ContentModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class VoiceDialect(ContentModel):
    name: str = "standard_mandarin"
    strength: float = Field(default=0, ge=0, le=1)


class VoiceProviderProfile(ContentModel):
    edge_voice: str
    edge_rate: str = "+0%"
    edge_pitch: str = "+0Hz"


class VoiceProfileContent(ContentModel):
    id: str
    voice_lineage_id: str
    age_stage: int | None = Field(default=None, ge=0, le=200)
    register: str
    pace: float = Field(ge=0.5, le=1.5)
    dialect: VoiceDialect = Field(default_factory=VoiceDialect)
    breathiness: float = Field(default=0, ge=0, le=1)
    emotion_limits: dict[str, float] = Field(default_factory=dict)
    forbidden_traits: tuple[str, ...] = ()
    provider: VoiceProviderProfile
    version: int = Field(ge=1)


class VoiceCueContent(ContentModel):
    start_ms: int = Field(ge=0)
    end_ms: int = Field(gt=0)
    text: str = Field(min_length=1)


class VoiceLineContent(ContentModel):
    id: str
    source_ref: str
    speaker_profile: str
    text: str = Field(min_length=1, max_length=1000)
    subtitle_segments: tuple[str, ...] = ()
    emotion: Literal["neutral", "warm", "guarded", "sad", "hopeful"]
    intensity: float = Field(ge=0, le=1)
    space: str
    delivery: Literal["pre_generated", "runtime", "silent"]
    priority: Literal["ending", "critical", "dialogue", "narration", "system"]
    version: int = Field(ge=1)


class VoiceAssetContent(ContentModel):
    id: str
    filename: str
    media_type: Literal["audio/wav", "audio/mpeg", "audio/ogg; codecs=opus"]
    duration_ms: int = Field(gt=0)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    text_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    integrated_lufs: float = Field(ge=-30, le=-10)
    true_peak_dbfs: float = Field(le=0)
    generator: Literal["edge_tts"]
    generator_revision: str
    model_id: str
    seed_provenance: Literal["edge_tts_synthetic"]
    line_version: int = Field(ge=1)
    profile_version: int = Field(ge=1)
    postprocess_version: int = Field(ge=1)
    cues: tuple[VoiceCueContent, ...] = ()
    approved: bool


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
    transition_in_voice_line_id: str | None = None
    transition_out_voice_line_id: str | None = None
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
    voice_profile_id: str
    initial_voice_line_id: str | None = None


class FragmentContent(ContentModel):
    id: str
    name: str
    scene: str
    description: str
    unlock_method: Literal["dialogue", "explore", "trust"]
    unlock_hint: str
    memory_text: str
    memory_voice_line_id: str | None = None
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
    resolution_voice_line_id: str | None = None


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
    voice_line_id: str | None = None
