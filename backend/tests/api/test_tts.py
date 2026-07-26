from __future__ import annotations

from fastapi.testclient import TestClient

from backend.api import tts as tts_api
from backend.integrations.tts import TtsResult
from backend.main import app


class SuccessfulTts:
    async def synthesize(self, _request) -> TtsResult:
        return TtsResult(filename="voice.mp3", cache_hit=False)


class UnavailableTts:
    async def synthesize(self, _request) -> TtsResult:
        raise RuntimeError("network unavailable")


def test_tts_returns_same_origin_audio_url(monkeypatch) -> None:
    monkeypatch.setattr(tts_api, "tts_service", SuccessfulTts())

    response = TestClient(app).post(
        "/api/tts/speak",
        json={"text": "戏要开场了。", "npc_id": "chen_shouyi_young"},
    )

    assert response.status_code == 200
    assert response.json() == {"url": "/tts/voice.mp3", "cached": False}


def test_tts_provider_failure_is_a_stable_optional_error(monkeypatch) -> None:
    monkeypatch.setattr(tts_api, "tts_service", UnavailableTts())

    response = TestClient(app).post(
        "/api/tts/speak",
        json={"text": "文字对白仍然可以继续。", "npc_id": "chen_shouyi_young"},
    )

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "TTS_UNAVAILABLE"


def test_tts_rejects_oversized_text_before_provider(monkeypatch) -> None:
    monkeypatch.setattr(tts_api, "tts_service", SuccessfulTts())

    response = TestClient(app).post(
        "/api/tts/speak",
        json={"text": "字" * 501, "npc_id": "chen_shouyi_young"},
    )

    assert response.status_code == 422
