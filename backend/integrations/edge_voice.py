"""Edge TTS implementation of the provider-neutral voice contract."""

from __future__ import annotations

from backend.integrations.tts import TtsRequest, TtsService
from backend.integrations.voice_contracts import (
    VoiceSynthesisRequest,
    VoiceSynthesisResult,
)


class EdgeVoiceProvider:
    def __init__(self, tts_service: TtsService) -> None:
        self.tts_service = tts_service

    async def synthesize(self, request: VoiceSynthesisRequest) -> VoiceSynthesisResult:
        result = await self.tts_service.synthesize(
            TtsRequest(
                text=request.text,
                voice=request.profile.provider.edge_voice,
                rate=request.profile.provider.edge_rate,
                pitch=request.profile.provider.edge_pitch,
            )
        )
        return VoiceSynthesisResult(
            url=result.url,
            provider="edge",
            cache_hit=result.cache_hit,
            media_type="audio/mpeg",
            duration_ms=None,
            line_id=request.line_id,
            cues=(),
            degraded=True,
        )
