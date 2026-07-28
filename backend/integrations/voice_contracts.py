"""Provider-neutral voice synthesis contracts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol

from backend.content.models import VoiceCueContent, VoiceProfileContent

VoiceProviderName = Literal["fixed", "cosyvoice", "edge", "silent"]


@dataclass(frozen=True, slots=True)
class VoiceSynthesisRequest:
    text: str
    profile: VoiceProfileContent
    emotion: str
    intensity: float
    line_id: str | None = None


@dataclass(frozen=True, slots=True)
class VoiceSynthesisResult:
    url: str | None
    provider: VoiceProviderName
    cache_hit: bool
    media_type: str | None
    duration_ms: int | None
    line_id: str | None
    cues: tuple[VoiceCueContent, ...]
    degraded: bool


class VoiceProvider(Protocol):
    async def synthesize(self, request: VoiceSynthesisRequest) -> VoiceSynthesisResult:
        raise NotImplementedError
