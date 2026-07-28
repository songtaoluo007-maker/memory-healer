from __future__ import annotations

import pytest

from backend.content.models import VoiceProfileContent
from backend.integrations.edge_voice import EdgeVoiceProvider
from backend.integrations.tts import TtsRequest, TtsResult
from backend.integrations.voice_contracts import VoiceSynthesisRequest


class RecordingTts:
    def __init__(self) -> None:
        self.request: TtsRequest | None = None

    async def synthesize(self, request: TtsRequest) -> TtsResult:
        self.request = request
        return TtsResult(filename="voice.mp3", cache_hit=False)


def make_profile(**provider_overrides: str) -> VoiceProfileContent:
    provider = {
        "cosyvoice_seed": "synthetic-seed",
        "cosyvoice_instruction": "calm, restrained Mandarin",
        "edge_voice": "zh-CN-XiaoxiaoNeural",
        "edge_rate": "+0%",
        "edge_pitch": "+0Hz",
    }
    provider.update(provider_overrides)
    return VoiceProfileContent(
        id="test.profile",
        voice_lineage_id="test",
        register="mid",
        pace=1.0,
        provider=provider,
        seed_provenance="edge_tts_synthetic",
        version=1,
    )


@pytest.mark.asyncio
async def test_edge_adapter_uses_profile_fallback_settings() -> None:
    tts = RecordingTts()
    provider = EdgeVoiceProvider(tts)
    profile = make_profile(
        edge_voice="zh-CN-YunxiNeural",
        edge_rate="-10%",
        edge_pitch="-5Hz",
    )

    result = await provider.synthesize(
        VoiceSynthesisRequest(
            text="时间不等人，手艺也不等人。",
            profile=profile,
            emotion="guarded",
            intensity=0.4,
            line_id=None,
        )
    )

    assert tts.request == TtsRequest(
        text="时间不等人，手艺也不等人。",
        voice="zh-CN-YunxiNeural",
        rate="-10%",
        pitch="-5Hz",
    )
    assert result.provider == "edge"
    assert result.url == "/tts/voice.mp3"
