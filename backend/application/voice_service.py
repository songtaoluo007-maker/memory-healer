"""Provider-neutral voice orchestration with safe silent degradation."""

from __future__ import annotations

import asyncio
import time
from collections.abc import Callable

from backend.content.registry import ContentRegistry
from backend.domain.errors import DomainError
from backend.integrations.voice_contracts import (
    VoiceProvider,
    VoiceSynthesisRequest,
    VoiceSynthesisResult,
)


class VoiceCircuitBreaker:
    """Stops repeated primary-provider attempts for a bounded cooldown."""

    def __init__(
        self,
        *,
        failure_threshold: int,
        cooldown_seconds: float,
        monotonic: Callable[[], float] = time.monotonic,
    ) -> None:
        self.failure_threshold = max(1, failure_threshold)
        self.cooldown_seconds = max(0, cooldown_seconds)
        self.monotonic = monotonic
        self._consecutive_failures = 0
        self._open_until = 0.0

    def allows_request(self) -> bool:
        return self.monotonic() >= self._open_until

    def record_success(self) -> None:
        self._consecutive_failures = 0
        self._open_until = 0.0

    def record_failure(self) -> None:
        self._consecutive_failures += 1
        if self._consecutive_failures >= self.failure_threshold:
            self._open_until = self.monotonic() + self.cooldown_seconds


class VoiceService:
    def __init__(
        self,
        registry: ContentRegistry,
        *,
        primary: VoiceProvider | None = None,
        fallback: VoiceProvider | None = None,
        failure_threshold: int = 3,
        cooldown_seconds: float = 30,
        max_primary_concurrency: int = 1,
        monotonic: Callable[[], float] = time.monotonic,
    ) -> None:
        self.registry = registry
        self.primary = primary
        self.fallback = fallback
        self.circuit = VoiceCircuitBreaker(
            failure_threshold=failure_threshold,
            cooldown_seconds=cooldown_seconds,
            monotonic=monotonic,
        )
        self._primary_slots = asyncio.Semaphore(
            max(1, min(max_primary_concurrency, failure_threshold))
        )

    async def speak_npc(
        self,
        *,
        npc_id: str,
        text: str,
        emotion: str,
        intensity: float,
    ) -> VoiceSynthesisResult:
        npc = self.registry.get_npc(npc_id)
        try:
            profile = self.registry.get_voice_profile(npc.voice_profile_id)
        except DomainError as exc:
            if exc.code == "VOICE_PROFILE_NOT_FOUND":
                raise DomainError("VOICE_PROFILE_INVALID", "声音档案不存在") from exc
            raise

        request = VoiceSynthesisRequest(
            text=text.strip(),
            profile=profile,
            emotion=emotion,
            intensity=intensity,
            line_id=None,
        )
        if self.primary is not None:
            async with self._primary_slots:
                if self.circuit.allows_request():
                    try:
                        result = await self.primary.synthesize(request)
                    except Exception:
                        self.circuit.record_failure()
                    else:
                        self.circuit.record_success()
                        return result

        if self.fallback is not None:
            try:
                return await self.fallback.synthesize(request)
            except Exception:
                pass
        return self._silent_result()

    async def get_fixed_line(self, line_id: str) -> VoiceSynthesisResult:
        try:
            self.registry.get_voice_line(line_id)
        except DomainError as exc:
            if exc.code == "VOICE_LINE_NOT_FOUND":
                raise DomainError("VOICE_LINE_INVALID", "语音行不存在") from exc
            raise

        asset = self.registry.get_voice_asset(line_id)
        if asset is None:
            return self._silent_result(line_id=line_id)
        return VoiceSynthesisResult(
            url=f"/voice/{asset.filename.lstrip('/')}",
            provider="fixed",
            cache_hit=True,
            media_type=asset.media_type,
            duration_ms=asset.duration_ms,
            line_id=line_id,
            cues=asset.cues,
            degraded=False,
        )

    @staticmethod
    def _silent_result(*, line_id: str | None = None) -> VoiceSynthesisResult:
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
