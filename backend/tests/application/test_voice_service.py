from __future__ import annotations

import asyncio
import hashlib
from pathlib import Path
from types import SimpleNamespace

import pytest

from backend.application.voice_service import VoiceService
from backend.content.models import VoiceAssetContent
from backend.content.registry import ContentRegistry
from backend.domain.errors import DomainError
from backend.integrations.cosyvoice import VoiceProviderTimeout
from backend.integrations.voice_contracts import VoiceSynthesisResult


DATA_DIR = Path(__file__).resolve().parents[2] / "data"


class FailingProvider:
    def __init__(self, error: Exception) -> None:
        self.error = error
        self.calls = 0

    async def synthesize(self, _request) -> VoiceSynthesisResult:
        self.calls += 1
        raise self.error


class SuccessfulProvider:
    def __init__(self, *, provider: str, url: str) -> None:
        self.provider = provider
        self.url = url
        self.calls = 0

    async def synthesize(self, request) -> VoiceSynthesisResult:
        self.calls += 1
        return VoiceSynthesisResult(
            url=self.url,
            provider=self.provider,
            cache_hit=False,
            media_type="audio/mpeg",
            duration_ms=None,
            line_id=request.line_id,
            cues=(),
            degraded=self.provider == "edge",
        )


class BlockingFailingProvider:
    def __init__(self) -> None:
        self.calls = 0
        self.first_entered = asyncio.Event()
        self.release = asyncio.Event()

    async def synthesize(self, _request) -> VoiceSynthesisResult:
        self.calls += 1
        self.first_entered.set()
        await self.release.wait()
        raise RuntimeError("primary")


class BlockingSuccessfulProvider:
    def __init__(self) -> None:
        self.calls = 0
        self.first_entered = asyncio.Event()
        self.second_entered = asyncio.Event()
        self.fourth_entered = asyncio.Event()
        self.release = asyncio.Event()

    async def synthesize(self, request) -> VoiceSynthesisResult:
        self.calls += 1
        self.first_entered.set()
        if self.calls == 2:
            self.second_entered.set()
        if self.calls == 4:
            self.fourth_entered.set()
        await self.release.wait()
        return VoiceSynthesisResult(
            url="/voice/cache/generated.wav",
            provider="cosyvoice",
            cache_hit=False,
            media_type="audio/wav",
            duration_ms=None,
            line_id=request.line_id,
            cues=(),
            degraded=False,
        )


@pytest.fixture
def registry() -> ContentRegistry:
    return ContentRegistry.load(DATA_DIR)


def registry_with_asset(*, approved: bool) -> ContentRegistry:
    registry = ContentRegistry.load(DATA_DIR)
    line = registry.get_voice_line("scene_1972.transition_in")
    asset = VoiceAssetContent(
        id=line.id,
        filename="fixed/scene-1972-transition-in.opus",
        media_type="audio/ogg; codecs=opus",
        duration_ms=1200,
        sha256="0" * 64,
        text_sha256=hashlib.sha256(line.text.encode("utf-8")).hexdigest(),
        integrated_lufs=-18,
        true_peak_dbfs=-1,
        generator="cosyvoice3",
        generator_revision="074ca6dc9e80a2f424f1f74b48bdd7d3fea531cc",
        model_id="FunAudioLLM/CosyVoice3-0.5B",
        seed_provenance="cosyvoice_sft_synthetic",
        profile_version=1,
        postprocess_version=1,
        cues=(),
        approved=approved,
    )
    return ContentRegistry(
        scenes=registry.scenes,
        npcs=registry.npcs,
        fragments=registry.fragments,
        hotspots=registry.hotspots,
        choices=registry.choices,
        hypotheses=registry.hypotheses,
        endings=registry.endings,
        voice_profiles=registry.voice_profiles,
        voice_lines=registry.voice_lines,
        voice_assets={asset.id: asset},
    )


@pytest.mark.asyncio
async def test_voice_service_falls_back_to_edge_without_blocking_text(
    registry: ContentRegistry,
) -> None:
    primary = FailingProvider(VoiceProviderTimeout("timeout"))
    fallback = SuccessfulProvider(provider="edge", url="/tts/fallback.mp3")
    service = VoiceService(registry, primary=primary, fallback=fallback)

    result = await service.speak_npc(
        npc_id="chen_shouyi_young",
        text="额守着这方幕布。",
        emotion="warm",
        intensity=0.5,
    )

    assert result.provider == "edge"
    assert result.degraded is True


@pytest.mark.asyncio
async def test_all_provider_failures_return_stable_silent_result(
    registry: ContentRegistry,
) -> None:
    service = VoiceService(
        registry,
        primary=FailingProvider(RuntimeError("primary")),
        fallback=FailingProvider(RuntimeError("fallback")),
    )

    result = await service.speak_npc(
        npc_id="chen_shouyi_young",
        text="文字仍然继续。",
        emotion="neutral",
        intensity=0.2,
    )

    assert result.provider == "silent"
    assert result.url is None
    assert result.degraded is True


@pytest.mark.asyncio
async def test_approved_fixed_asset_wins_over_runtime_providers() -> None:
    fallback = SuccessfulProvider(provider="edge", url="/tts/fallback.mp3")
    service = VoiceService(registry_with_asset(approved=True), fallback=fallback)

    result = await service.get_fixed_line("scene_1972.transition_in")

    assert result.provider == "fixed"
    assert result.url == "/voice/fixed/scene-1972-transition-in.opus"
    assert fallback.calls == 0


@pytest.mark.asyncio
async def test_unapproved_fixed_asset_is_ignored() -> None:
    service = VoiceService(registry_with_asset(approved=False))

    result = await service.get_fixed_line("scene_1972.transition_in")

    assert result.provider == "silent"
    assert result.url is None
    assert result.cues == ()


@pytest.mark.asyncio
async def test_three_primary_failures_open_the_circuit(registry: ContentRegistry) -> None:
    primary = FailingProvider(RuntimeError("primary"))
    fallback = SuccessfulProvider(provider="edge", url="/tts/fallback.mp3")
    service = VoiceService(
        registry,
        primary=primary,
        fallback=fallback,
        failure_threshold=3,
    )

    for _ in range(4):
        await service.speak_npc(
            npc_id="chen_shouyi_young",
            text="文字仍然继续。",
            emotion="neutral",
            intensity=0.2,
        )

    assert primary.calls == 3
    assert fallback.calls == 4


@pytest.mark.asyncio
async def test_primary_is_retried_after_the_configured_cooldown(
    registry: ContentRegistry,
) -> None:
    clock = [100.0]
    primary = FailingProvider(RuntimeError("primary"))
    fallback = SuccessfulProvider(provider="edge", url="/tts/fallback.mp3")
    service = VoiceService(
        registry,
        primary=primary,
        fallback=fallback,
        failure_threshold=1,
        cooldown_seconds=30,
        monotonic=lambda: clock[0],
    )

    await service.speak_npc(
        npc_id="chen_shouyi_young", text="一次失败。", emotion="neutral", intensity=0.2
    )
    await service.speak_npc(
        npc_id="chen_shouyi_young", text="仍在冷却。", emotion="neutral", intensity=0.2
    )
    clock[0] += 30
    await service.speak_npc(
        npc_id="chen_shouyi_young", text="冷却结束。", emotion="neutral", intensity=0.2
    )

    assert primary.calls == 2


@pytest.mark.asyncio
async def test_concurrent_requests_do_not_queue_past_the_primary_failure_threshold(
    registry: ContentRegistry,
) -> None:
    primary = BlockingFailingProvider()
    fallback = SuccessfulProvider(provider="edge", url="/tts/fallback.mp3")
    service = VoiceService(
        registry,
        primary=primary,
        fallback=fallback,
        failure_threshold=3,
    )

    requests = [
        asyncio.create_task(
            service.speak_npc(
                npc_id="chen_shouyi_young",
                text=f"第 {index} 句。",
                emotion="neutral",
                intensity=0.2,
            )
        )
        for index in range(4)
    ]
    await asyncio.wait_for(primary.first_entered.wait(), timeout=0.2)
    await asyncio.sleep(0)
    assert primary.calls == 1

    primary.release.set()
    results = await asyncio.gather(*requests)

    assert [result.provider for result in results] == ["edge"] * 4
    assert fallback.calls == 4


@pytest.mark.asyncio
async def test_concurrent_healthy_requests_remain_primary_first(
    registry: ContentRegistry,
) -> None:
    primary = BlockingSuccessfulProvider()
    fallback = SuccessfulProvider(provider="edge", url="/tts/fallback.mp3")
    service = VoiceService(
        registry,
        primary=primary,
        fallback=fallback,
        failure_threshold=3,
    )

    requests = [
        asyncio.create_task(
            service.speak_npc(
                npc_id="chen_shouyi_young",
                text=f"第 {index} 句。",
                emotion="neutral",
                intensity=0.2,
            )
        )
        for index in range(4)
    ]
    await asyncio.wait_for(primary.first_entered.wait(), timeout=0.2)
    primary.release.set()
    results = await asyncio.gather(*requests)

    assert primary.calls == 4
    assert fallback.calls == 0
    assert [result.provider for result in results] == ["cosyvoice"] * 4


@pytest.mark.asyncio
async def test_voice_service_honors_non_default_primary_concurrency(
    registry: ContentRegistry,
) -> None:
    primary = BlockingSuccessfulProvider()
    service = VoiceService(
        registry,
        primary=primary,
        failure_threshold=3,
        max_primary_concurrency=2,
    )

    requests = [
        asyncio.create_task(
            service.speak_npc(
                npc_id="chen_shouyi_young",
                text=f"第 {index} 句。",
                emotion="neutral",
                intensity=0.2,
            )
        )
        for index in range(3)
    ]
    await asyncio.wait_for(primary.second_entered.wait(), timeout=0.2)
    primary.release.set()
    results = await asyncio.gather(*requests)

    assert primary.calls == 3
    assert [result.provider for result in results] == ["cosyvoice"] * 3


@pytest.mark.asyncio
async def test_healthy_primary_concurrency_is_not_capped_by_failure_threshold(
    registry: ContentRegistry,
) -> None:
    primary = BlockingSuccessfulProvider()
    service = VoiceService(
        registry,
        primary=primary,
        failure_threshold=1,
        max_primary_concurrency=4,
    )

    requests = [
        asyncio.create_task(
            service.speak_npc(
                npc_id="chen_shouyi_young",
                text=f"第 {index} 句。",
                emotion="neutral",
                intensity=0.2,
            )
        )
        for index in range(4)
    ]
    try:
        await asyncio.wait_for(primary.fourth_entered.wait(), timeout=0.2)
    finally:
        primary.release.set()

    results = await asyncio.gather(*requests)

    assert primary.calls == 4
    assert [result.provider for result in results] == ["cosyvoice"] * 4


@pytest.mark.asyncio
async def test_unknown_npc_and_line_expose_stable_domain_codes(
    registry: ContentRegistry,
) -> None:
    service = VoiceService(registry)

    with pytest.raises(DomainError, match="NPC") as npc_error:
        await service.speak_npc(
            npc_id="missing", text="文字", emotion="neutral", intensity=0.2
        )
    with pytest.raises(DomainError, match="语音") as line_error:
        await service.get_fixed_line("missing.line")

    assert npc_error.value.code == "NPC_NOT_FOUND"
    assert line_error.value.code == "VOICE_LINE_INVALID"


@pytest.mark.asyncio
async def test_unknown_voice_profile_exposes_a_stable_domain_code(
    registry: ContentRegistry,
) -> None:
    class MissingProfileRegistry:
        def get_npc(self, _npc_id):
            return SimpleNamespace(voice_profile_id="missing.profile")

        def get_voice_profile(self, _profile_id):
            raise DomainError("VOICE_PROFILE_NOT_FOUND", "声音档案不存在")

    service = VoiceService(MissingProfileRegistry())

    with pytest.raises(DomainError) as caught:
        await service.speak_npc(
            npc_id="known", text="文字", emotion="neutral", intensity=0.2
        )

    assert caught.value.code == "VOICE_PROFILE_INVALID"
