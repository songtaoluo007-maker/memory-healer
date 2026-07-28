from __future__ import annotations

import hashlib
import importlib
import json
from pathlib import Path

import httpx
import pytest

from backend.content.models import VoiceProfileContent
from backend.integrations.voice_contracts import VoiceSynthesisRequest


def remote_voice_module():
    return importlib.import_module("backend.integrations.remote_voice")


def make_profile() -> VoiceProfileContent:
    return VoiceProfileContent(
        id="test.profile",
        voice_lineage_id="test",
        register="mid",
        pace=1.0,
        provider={
            "edge_voice": "zh-CN-XiaoxiaoNeural",
            "edge_rate": "+0%",
            "edge_pitch": "+0Hz",
        },
        version=2,
    )


def make_request(
    *,
    text: str = "时间不等人，手艺也不等人。",
) -> VoiceSynthesisRequest:
    return VoiceSynthesisRequest(
        text=text,
        profile=make_profile(),
        emotion="guarded",
        intensity=0.4,
        line_id="line.test",
    )


def expected_cache_key(request: VoiceSynthesisRequest) -> str:
    payload = {
        "emotion": request.emotion,
        "intensity": request.intensity,
        "profile_id": request.profile.id,
        "profile_version": request.profile.version,
        "text": request.text.strip(),
    }
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def make_provider(tmp_path: Path, handler, **overrides):
    module = remote_voice_module()
    options = {
        "base_url": "https://voice-provider.example",
        "token": "remote-token",
        "cache_dir": tmp_path / "cache",
        "client": httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    }
    options.update(overrides)
    return module.RemoteVoiceHttpProvider(**options)


@pytest.mark.asyncio
async def test_remote_provider_posts_json_without_local_seed_or_model_data(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    received: dict[str, object] = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        received["authorization"] = request.headers.get("Authorization")
        received["content_type"] = request.headers.get("Content-Type")
        received["json"] = json.loads((await request.aread()).decode())
        return httpx.Response(
            200,
            headers={"content-type": "audio/wav"},
            content=b"RIFFgenerated",
        )

    def reject_file_reads(_path: Path) -> bytes:
        raise AssertionError("remote provider attempted a local file read")

    monkeypatch.setattr(Path, "read_bytes", reject_file_reads)
    request = make_request()
    provider = make_provider(tmp_path, handler)

    result = await provider.synthesize(request)

    cache_key = expected_cache_key(request)
    assert received == {
        "authorization": "Bearer remote-token",
        "content_type": "application/json",
        "json": {
            "text": request.text,
            "profile_id": "test.profile",
            "profile_version": 2,
            "emotion": "guarded",
            "intensity": 0.4,
            "cache_key": cache_key,
        },
    }
    serialized = json.dumps(received, ensure_ascii=False).casefold()
    assert "seed" not in serialized
    assert "model" not in serialized
    assert "bridge" not in serialized
    assert result.provider == "remote"
    assert result.url == f"/voice/cache/{cache_key}.wav"
    assert result.cache_hit is False


@pytest.mark.asyncio
async def test_remote_provider_reuses_cached_audio_without_second_request(
    tmp_path: Path,
) -> None:
    calls = 0

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(
            200,
            headers={"content-type": "audio/wav"},
            content=b"RIFFgenerated",
        )

    provider = make_provider(tmp_path, handler)
    request = make_request()

    first = await provider.synthesize(request)
    second = await provider.synthesize(request)

    assert calls == 1
    assert first.cache_hit is False
    assert second.cache_hit is True


@pytest.mark.asyncio
async def test_remote_provider_translates_timeout(tmp_path: Path) -> None:
    module = remote_voice_module()

    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("remote slow", request=request)

    provider = make_provider(tmp_path, handler)

    with pytest.raises(module.VoiceProviderTimeout, match="timed out"):
        await provider.synthesize(make_request())


@pytest.mark.asyncio
async def test_remote_provider_rejects_non_audio_response(tmp_path: Path) -> None:
    module = remote_voice_module()
    provider = make_provider(
        tmp_path,
        lambda _request: httpx.Response(
            200,
            headers={"content-type": "application/json"},
            json={"error": "not audio"},
        ),
    )

    with pytest.raises(module.VoiceProviderError, match="audio/wav"):
        await provider.synthesize(make_request())
