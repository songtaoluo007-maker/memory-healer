from __future__ import annotations

import asyncio
import builtins
import hashlib
import importlib.util
import json
import os
from pathlib import Path
from types import ModuleType, SimpleNamespace

import httpx
import pytest
from fastapi.testclient import TestClient

from backend.content.models import VoiceProfileContent
from backend.integrations.cosyvoice import (
    CosyVoiceHttpProvider,
    VoiceProviderError,
    VoiceProviderTimeout,
)
from backend.integrations.voice_contracts import VoiceSynthesisRequest


def make_profile(*, seed_name: str = "seed.wav") -> VoiceProfileContent:
    return VoiceProfileContent(
        id="test.profile",
        voice_lineage_id="test",
        register="mid",
        pace=1.0,
        provider={
            "cosyvoice_seed": seed_name,
            "cosyvoice_instruction": "calm, restrained Mandarin",
            "edge_voice": "zh-CN-XiaoxiaoNeural",
        },
        seed_provenance="cosyvoice_sft_synthetic",
        version=2,
    )


def make_request(
    *,
    seed_name: str = "seed.wav",
    text: str = "时间不等人，手艺也不等人。",
) -> VoiceSynthesisRequest:
    return VoiceSynthesisRequest(
        text=text,
        profile=make_profile(seed_name=seed_name),
        emotion="guarded",
        intensity=0.4,
        line_id="line.test",
    )


def make_provider(
    tmp_path: Path,
    handler,
    **overrides,
) -> CosyVoiceHttpProvider:
    options = {
        "base_url": "http://cosy.local",
        "bridge_token": "test-token",
        "cache_dir": tmp_path / "cache",
        "seed_root": tmp_path,
        "client": httpx.AsyncClient(transport=httpx.MockTransport(handler)),
        "model_revision": "Fun-CosyVoice3-0.5B-2512",
    }
    options.update(overrides)
    return CosyVoiceHttpProvider(**options)


def expected_cache_path(tmp_path: Path, request: VoiceSynthesisRequest) -> Path:
    payload = {
        "emotion": request.emotion,
        "instruction": request.profile.provider.cosyvoice_instruction,
        "intensity": request.intensity,
        "model_revision": "Fun-CosyVoice3-0.5B-2512",
        "profile_id": request.profile.id,
        "profile_version": request.profile.version,
        "seed": request.profile.provider.cosyvoice_seed,
        "text": request.text.strip(),
    }
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return tmp_path / "cache" / f"{hashlib.sha256(encoded).hexdigest()}.wav"


@pytest.mark.asyncio
async def test_cosyvoice_provider_posts_synthetic_seed_and_returns_cached_url(
    tmp_path: Path,
) -> None:
    seed = tmp_path / "seed.wav"
    seed.write_bytes(b"RIFFsynthetic")
    received: dict[str, object] = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        received["authorization"] = request.headers.get("X-Voice-Bridge-Token")
        received["body"] = await request.aread()
        return httpx.Response(
            200,
            headers={"content-type": "audio/wav"},
            content=b"RIFFgenerated",
        )

    provider = make_provider(tmp_path, handler)

    result = await provider.synthesize(make_request())

    assert result.provider == "cosyvoice"
    assert result.url is not None
    assert result.url.startswith("/voice/cache/")
    assert result.line_id == "line.test"
    assert result.cues == ()
    assert result.degraded is False
    assert (tmp_path / "cache" / Path(result.url).name).read_bytes() == b"RIFFgenerated"
    assert received["authorization"] == "test-token"
    body = received["body"]
    assert isinstance(body, bytes)
    assert b'name="tts_text"' in body
    assert "时间不等人，手艺也不等人。".encode() in body
    assert b'name="instruct_text"' in body
    assert b"calm, restrained Mandarin" in body
    assert b'name="prompt_wav"; filename="seed.wav"' in body
    assert b"RIFFsynthetic" in body


@pytest.mark.asyncio
async def test_cosyvoice_provider_maps_one_logical_seeds_prefix_under_seed_root(
    tmp_path: Path,
) -> None:
    (tmp_path / "chen.wav").write_bytes(b"RIFFsynthetic")
    seen_prompt = False

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal seen_prompt
        seen_prompt = b"RIFFsynthetic" in await request.aread()
        return httpx.Response(
            200,
            headers={"content-type": "audio/wav"},
            content=b"RIFFgenerated",
        )

    provider = make_provider(tmp_path, handler)

    await provider.synthesize(make_request(seed_name="seeds/chen.wav"))

    assert seen_prompt is True


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "seed_name",
    [
        "../outside.wav",
        "seeds/../outside.wav",
        "seeds/seeds/nested.wav",
        "/absolute.wav",
        "C:\\absolute.wav",
    ],
)
async def test_cosyvoice_provider_rejects_seed_paths_that_escape_or_repeat_namespace(
    tmp_path: Path,
    seed_name: str,
) -> None:
    provider = make_provider(
        tmp_path,
        lambda request: httpx.Response(
            200,
            headers={"content-type": "audio/wav"},
            content=b"RIFFgenerated",
        ),
    )

    with pytest.raises(VoiceProviderError, match="seed"):
        await provider.synthesize(make_request(seed_name=seed_name))


@pytest.mark.asyncio
async def test_cosyvoice_provider_rejects_missing_seed(tmp_path: Path) -> None:
    provider = make_provider(
        tmp_path,
        lambda request: httpx.Response(
            200,
            headers={"content-type": "audio/wav"},
            content=b"RIFFgenerated",
        ),
    )

    with pytest.raises(VoiceProviderError, match="seed"):
        await provider.synthesize(make_request(seed_name="missing.wav"))


@pytest.mark.asyncio
async def test_cosyvoice_provider_translates_http_timeout(tmp_path: Path) -> None:
    (tmp_path / "seed.wav").write_bytes(b"RIFFsynthetic")

    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("slow bridge", request=request)

    provider = make_provider(tmp_path, handler)

    with pytest.raises(VoiceProviderTimeout, match="timed out"):
        await provider.synthesize(make_request())


@pytest.mark.asyncio
async def test_cosyvoice_provider_rejects_non_audio_response(tmp_path: Path) -> None:
    (tmp_path / "seed.wav").write_bytes(b"RIFFsynthetic")
    provider = make_provider(
        tmp_path,
        lambda request: httpx.Response(
            200,
            headers={"content-type": "application/json"},
            json={"error": "not audio"},
        ),
    )

    with pytest.raises(VoiceProviderError, match="audio/wav"):
        await provider.synthesize(make_request())


@pytest.mark.asyncio
async def test_identical_requests_use_cache_after_one_http_request(tmp_path: Path) -> None:
    (tmp_path / "seed.wav").write_bytes(b"RIFFsynthetic")
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
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
async def test_concurrent_identical_requests_are_coalesced_per_cache_key(
    tmp_path: Path,
) -> None:
    (tmp_path / "seed.wav").write_bytes(b"RIFFsynthetic")
    calls = 0
    release = asyncio.Event()

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        await release.wait()
        return httpx.Response(
            200,
            headers={"content-type": "audio/wav"},
            content=b"RIFFgenerated",
        )

    provider = make_provider(tmp_path, handler)
    request = make_request()
    first_task = asyncio.create_task(provider.synthesize(request))
    second_task = asyncio.create_task(provider.synthesize(request))
    await asyncio.sleep(0)
    release.set()

    first, second = await asyncio.gather(first_task, second_task)

    assert calls == 1
    assert {first.cache_hit, second.cache_hit} == {False, True}


@pytest.mark.asyncio
async def test_generation_respects_configured_concurrency(tmp_path: Path) -> None:
    (tmp_path / "seed.wav").write_bytes(b"RIFFsynthetic")
    active = 0
    maximum_active = 0
    release = asyncio.Event()
    two_started = asyncio.Event()

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal active, maximum_active
        active += 1
        maximum_active = max(maximum_active, active)
        if active == 2:
            two_started.set()
        await release.wait()
        active -= 1
        return httpx.Response(
            200,
            headers={"content-type": "audio/wav"},
            content=b"RIFFgenerated",
        )

    provider = make_provider(tmp_path, handler, max_concurrency=2)
    tasks = [
        asyncio.create_task(provider.synthesize(make_request(text=f"line {index}")))
        for index in range(3)
    ]
    await asyncio.wait_for(two_started.wait(), timeout=1)
    assert maximum_active == 2
    release.set()
    await asyncio.gather(*tasks)

    assert maximum_active == 2


@pytest.mark.asyncio
async def test_lru_cleanup_enforces_file_count_limit(tmp_path: Path) -> None:
    (tmp_path / "seed.wav").write_bytes(b"RIFFsynthetic")
    provider = make_provider(
        tmp_path,
        lambda request: httpx.Response(
            200,
            headers={"content-type": "audio/wav"},
            content=b"RIFFgenerated",
        ),
        max_cache_files=2,
        max_cache_bytes=1_000_000,
    )

    for index in range(3):
        await provider.synthesize(make_request(text=f"line {index}"))

    cache_files = sorted((tmp_path / "cache").glob("*.wav"))
    assert len(cache_files) == 2
    assert expected_cache_path(tmp_path, make_request(text="line 0")) not in cache_files


@pytest.mark.asyncio
async def test_lru_cleanup_enforces_total_byte_limit(tmp_path: Path) -> None:
    (tmp_path / "seed.wav").write_bytes(b"RIFFsynthetic")
    provider = make_provider(
        tmp_path,
        lambda request: httpx.Response(
            200,
            headers={"content-type": "audio/wav"},
            content=b"RIFF012345",
        ),
        max_cache_files=10,
        max_cache_bytes=15,
    )

    await provider.synthesize(make_request(text="first"))
    await provider.synthesize(make_request(text="second"))

    cache_files = list((tmp_path / "cache").glob("*.wav"))
    assert sum(path.stat().st_size for path in cache_files) <= 15
    assert cache_files == [expected_cache_path(tmp_path, make_request(text="second"))]


@pytest.mark.asyncio
async def test_lru_cleanup_does_not_evict_an_in_flight_cache_key(
    tmp_path: Path,
) -> None:
    (tmp_path / "seed.wav").write_bytes(b"RIFFsynthetic")
    slow_started = asyncio.Event()
    release_slow = asyncio.Event()

    async def handler(request: httpx.Request) -> httpx.Response:
        body = await request.aread()
        if b"slow" in body:
            slow_started.set()
            await release_slow.wait()
        return httpx.Response(
            200,
            headers={"content-type": "audio/wav"},
            content=b"RIFFgenerated",
        )

    provider = make_provider(
        tmp_path,
        handler,
        max_concurrency=2,
        max_cache_files=1,
        max_cache_bytes=1_000_000,
    )
    slow_request = make_request(text="slow")
    slow_task = asyncio.create_task(provider.synthesize(slow_request))
    await asyncio.wait_for(slow_started.wait(), timeout=1)

    in_flight_path = expected_cache_path(tmp_path, slow_request)
    in_flight_path.parent.mkdir(parents=True, exist_ok=True)
    in_flight_path.write_bytes(b"RIFFpartial")
    os.utime(in_flight_path, ns=(1_000_000_000, 1_000_000_000))

    await provider.synthesize(make_request(text="fast"))

    assert in_flight_path.exists()
    release_slow.set()
    await slow_task
    assert in_flight_path.read_bytes() == b"RIFFgenerated"


def load_bridge_module(monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    real_import = builtins.__import__

    def guarded_import(name, *args, **kwargs):
        if name.split(".", 1)[0] in {"torch", "torchaudio", "cosyvoice"}:
            raise AssertionError(f"heavy import at module import time: {name}")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded_import)
    module_path = Path("tools/cosyvoice_bridge/app.py").resolve()
    spec = importlib.util.spec_from_file_location("test_cosyvoice_bridge", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_bridge_import_is_lightweight_and_routes_are_authenticated(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = load_bridge_module(monkeypatch)
    monkeypatch.setenv("COSYVOICE_BRIDGE_TOKEN", "bridge-secret")
    monkeypatch.setenv("COSYVOICE_MODEL_DIR", "synthetic-model")
    calls: dict[str, object] = {"loads": 0}

    class FakeModel:
        sample_rate = 24_000

        def inference_instruct2(
            self,
            tts_text,
            instruct_text,
            prompt,
            *,
            stream,
        ):
            calls["inference"] = (tts_text, instruct_text, prompt, stream)
            yield {"tts_speech": "chunk-a"}
            yield {"tts_speech": "chunk-b"}

    class FakeTorch:
        @staticmethod
        def cat(chunks, *, dim):
            calls["cat"] = (chunks, dim)
            return "speech"

    class FakeTorchaudio:
        @staticmethod
        def save(output, speech, sample_rate, *, format):
            calls["save"] = (speech, sample_rate, format)
            output.write(b"RIFFbridge")

    def fake_load_runtime(model_dir: str):
        calls["loads"] = int(calls["loads"]) + 1
        calls["model_dir"] = model_dir
        return SimpleNamespace(
            model=FakeModel(),
            torch=FakeTorch(),
            torchaudio=FakeTorchaudio(),
            load_wav=lambda source, sample_rate: ("prompt", sample_rate, source.read()),
        )

    monkeypatch.setattr(module, "load_cosyvoice_runtime", fake_load_runtime)

    with TestClient(module.app) as client:
        health = client.get("/health")
        unauthorized = client.post(
            "/v1/synthesize",
            data={"tts_text": "开场", "instruct_text": "克制"},
            files={"prompt_wav": ("seed.wav", b"RIFFsynthetic", "audio/wav")},
        )
        synthesized = client.post(
            "/v1/synthesize",
            headers={"X-Voice-Bridge-Token": "bridge-secret"},
            data={"tts_text": "开场", "instruct_text": "克制"},
            files={"prompt_wav": ("seed.wav", b"RIFFsynthetic", "audio/wav")},
        )
        too_long = client.post(
            "/v1/synthesize",
            headers={"X-Voice-Bridge-Token": "bridge-secret"},
            data={"tts_text": "长" * 501, "instruct_text": "克制"},
            files={"prompt_wav": ("seed.wav", b"RIFFsynthetic", "audio/wav")},
        )

    assert health.status_code == 200
    assert health.json()["status"] == "ok"
    assert unauthorized.status_code == 401
    assert synthesized.status_code == 200
    assert synthesized.headers["content-type"] == "audio/wav"
    assert synthesized.content == b"RIFFbridge"
    assert too_long.status_code == 422
    assert calls["loads"] == 1
    assert calls["model_dir"] == "synthetic-model"
    assert calls["inference"] == ("开场", "克制", ("prompt", 16_000, b"RIFFsynthetic"), False)
    assert calls["cat"] == (["chunk-a", "chunk-b"], 1)
    assert calls["save"] == ("speech", 24_000, "wav")
