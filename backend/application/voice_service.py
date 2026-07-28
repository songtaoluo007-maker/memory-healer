"""Provider-neutral voice orchestration with safe silent degradation."""

from __future__ import annotations

import asyncio
import time
from collections.abc import Callable

from backend.application.voice_metrics import (
    VoiceMetricsEmitter,
    default_voice_metrics,
)
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
        metrics: VoiceMetricsEmitter = default_voice_metrics,
        latency_clock: Callable[[], float] = time.perf_counter,
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
            max(1, max_primary_concurrency)
        )
        self.metrics = metrics
        self.latency_clock = latency_clock

    async def speak_npc(
        self,
        *,
        npc_id: str,
        text: str,
        emotion: str,
        intensity: float,
    ) -> VoiceSynthesisResult:
        started_at = self.latency_clock()
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
                        return self._record_metrics(
                            result,
                            started_at=started_at,
                            fallback_used=False,
                        )

        if self.fallback is not None:
            try:
                result = await self.fallback.synthesize(request)
            except Exception:
                pass
            else:
                return self._record_metrics(
                    result,
                    started_at=started_at,
                    fallback_used=self.primary is not None,
                )
        return self._record_metrics(
            self._silent_result(),
            started_at=started_at,
            fallback_used=self.primary is not None,
        )

    def _record_metrics(
        self,
        result: VoiceSynthesisResult,
        *,
        started_at: float,
        fallback_used: bool,
    ) -> VoiceSynthesisResult:
        event: dict[str, object] = {
            "event": "voice_synthesis",
            "provider": result.provider,
            "cache_hit": result.cache_hit,
            "asset_hit": result.provider == "fixed",
            "latency_ms": round(
                max(0.0, self.latency_clock() - started_at) * 1_000,
                3,
            ),
            "fallback": fallback_used,
            "silent_degradation": result.provider == "silent",
        }
        try:
            self.metrics.emit(event)
        except Exception:
            pass
        return result

    async def get_fixed_line(self, line_id: str) -> VoiceSynthesisResult:
        try:
            self.registry.get_voice_line(line_id)
        except DomainError as exc:
            if exc.code == "VOICE_LINE_NOT_FOUND":
                raise DomainError("VOICE_LINE_INVALID", "语音行不存在") from exc
            raise

        started_at = self.latency_clock()
        asset = self.registry.get_voice_asset(line_id)
        if asset is None:
            result = self._silent_result(line_id=line_id)
        else:
            result = VoiceSynthesisResult(
                url=f"/voice/{asset.filename.lstrip('/')}",
                provider="fixed",
                cache_hit=False,
                media_type=asset.media_type,
                duration_ms=asset.duration_ms,
                line_id=line_id,
                cues=asset.cues,
                degraded=False,
            )
        return self._record_metrics(
            result,
            started_at=started_at,
            fallback_used=False,
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
