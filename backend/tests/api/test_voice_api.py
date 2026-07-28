from __future__ import annotations

from fastapi.testclient import TestClient

from backend.api import voice as voice_api
from backend.content.models import VoiceCueContent
from backend.domain.errors import DomainError
from backend.integrations.voice_contracts import VoiceSynthesisResult
from backend.main import app


class SuccessfulVoiceService:
    async def speak_npc(self, **_kwargs) -> VoiceSynthesisResult:
        return VoiceSynthesisResult(
            url="/voice/cache/generated.wav",
            provider="cosyvoice",
            cache_hit=False,
            media_type="audio/wav",
            duration_ms=None,
            line_id=None,
            cues=(),
            degraded=False,
        )

    async def get_fixed_line(self, line_id: str) -> VoiceSynthesisResult:
        return VoiceSynthesisResult(
            url=None,
            provider="silent",
            cache_hit=False,
            media_type=None,
            duration_ms=None,
            line_id=line_id,
            cues=(),
            degraded=True,
        )


class InvalidLineVoiceService(SuccessfulVoiceService):
    async def get_fixed_line(self, _line_id: str) -> VoiceSynthesisResult:
        raise DomainError("VOICE_LINE_INVALID", "语音行不存在")


class CuedFixedLineVoiceService(SuccessfulVoiceService):
    async def get_fixed_line(self, line_id: str) -> VoiceSynthesisResult:
        return VoiceSynthesisResult(
            url="/voice/fixed/line.opus",
            provider="fixed",
            cache_hit=True,
            media_type="audio/ogg; codecs=opus",
            duration_ms=1200,
            line_id=line_id,
            cues=(VoiceCueContent(start_ms=0, end_ms=1200, text="开场。"),),
            degraded=False,
        )


def test_voice_api_returns_provider_neutral_response(monkeypatch) -> None:
    monkeypatch.setattr(voice_api, "voice_service", SuccessfulVoiceService())

    response = TestClient(app).post(
        "/api/voice/speak",
        json={
            "text": "戏要开场了。",
            "npc_id": "chen_shouyi_young",
            "emotion": "warm",
            "intensity": 0.4,
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "url": "/voice/cache/generated.wav",
        "provider": "cosyvoice",
        "cached": False,
        "media_type": "audio/wav",
        "duration_ms": None,
        "line_id": None,
        "cues": [],
        "degraded": False,
    }


def test_voice_api_returns_fixed_line_metadata(monkeypatch) -> None:
    monkeypatch.setattr(voice_api, "voice_service", SuccessfulVoiceService())

    response = TestClient(app).get("/api/voice/lines/scene_1972.transition_in")

    assert response.status_code == 200
    assert response.json()["line_id"] == "scene_1972.transition_in"
    assert response.json()["provider"] == "silent"


def test_voice_api_serializes_fixed_line_cues(monkeypatch) -> None:
    monkeypatch.setattr(voice_api, "voice_service", CuedFixedLineVoiceService())

    response = TestClient(app).get("/api/voice/lines/scene_1972.transition_in")

    assert response.status_code == 200
    assert response.json()["cues"] == [
        {"start_ms": 0, "end_ms": 1200, "text": "开场。"}
    ]


def test_voice_api_maps_invalid_voice_lines_to_not_found(monkeypatch) -> None:
    monkeypatch.setattr(voice_api, "voice_service", InvalidLineVoiceService())

    response = TestClient(app).get("/api/voice/lines/missing.line")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "VOICE_LINE_INVALID"


def test_voice_api_rejects_unknown_fields_before_the_service(monkeypatch) -> None:
    monkeypatch.setattr(voice_api, "voice_service", SuccessfulVoiceService())

    response = TestClient(app).post(
        "/api/voice/speak",
        json={"text": "戏要开场了。", "npc_id": "chen_shouyi_young", "unknown": True},
    )

    assert response.status_code == 422
