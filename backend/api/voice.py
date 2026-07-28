"""Provider-neutral voice playback API."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field

from backend.api.tts import tts_service
from backend.application.voice_service import VoiceService
from backend.config import settings
from backend.content.registry import ContentRegistry
from backend.integrations.cosyvoice import CosyVoiceHttpProvider
from backend.integrations.edge_voice import EdgeVoiceProvider
from backend.integrations.voice_contracts import VoiceSynthesisResult


router = APIRouter(prefix="/api/voice", tags=["voice"])


class VoiceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str = Field(min_length=1, max_length=500)
    npc_id: str = Field(min_length=1, max_length=100)
    emotion: Literal["neutral", "warm", "guarded", "sad", "hopeful"] = "neutral"
    intensity: float = Field(default=0.5, ge=0, le=1)


class VoiceCueResponse(BaseModel):
    start_ms: int
    end_ms: int
    text: str


class VoiceResponse(BaseModel):
    url: str | None
    provider: Literal["fixed", "cosyvoice", "edge", "silent"]
    cached: bool
    media_type: str | None
    duration_ms: int | None
    line_id: str | None
    cues: list[VoiceCueResponse]
    degraded: bool


def _primary_provider() -> CosyVoiceHttpProvider | None:
    if not settings.VOICE_PRIMARY_ENABLED:
        return None
    return CosyVoiceHttpProvider(
        base_url=settings.COSYVOICE_BASE_URL,
        bridge_token=settings.COSYVOICE_BRIDGE_TOKEN,
        cache_dir=settings.VOICE_PUBLIC_DIR / "cache",
        seed_root=settings.VOICE_SEED_DIR,
        model_revision=settings.COSYVOICE_MODEL_REVISION,
        model_commit=settings.COSYVOICE_MODEL_COMMIT,
        connect_timeout_seconds=settings.COSYVOICE_CONNECT_TIMEOUT_SECONDS,
        total_timeout_seconds=settings.COSYVOICE_TOTAL_TIMEOUT_SECONDS,
        max_concurrency=settings.VOICE_GENERATION_MAX_CONCURRENCY,
        max_cache_files=settings.VOICE_CACHE_MAX_FILES,
        max_cache_bytes=settings.VOICE_CACHE_MAX_BYTES,
    )


def _voice_service() -> VoiceService:
    data_dir = Path(__file__).resolve().parents[1] / "data"
    return VoiceService(
        ContentRegistry.load(data_dir),
        primary=_primary_provider(),
        fallback=EdgeVoiceProvider(tts_service),
        failure_threshold=settings.COSYVOICE_FAILURE_THRESHOLD,
        cooldown_seconds=settings.COSYVOICE_COOLDOWN_SECONDS,
        max_primary_concurrency=settings.VOICE_GENERATION_MAX_CONCURRENCY,
    )


voice_service = _voice_service()


def _response(result: VoiceSynthesisResult) -> VoiceResponse:
    return VoiceResponse(
        url=result.url,
        provider=result.provider,
        cached=result.cache_hit,
        media_type=result.media_type,
        duration_ms=result.duration_ms,
        line_id=result.line_id,
        cues=[
            VoiceCueResponse(
                start_ms=cue.start_ms,
                end_ms=cue.end_ms,
                text=cue.text,
            )
            for cue in result.cues
        ],
        degraded=result.degraded,
    )


@router.post("/speak", response_model=VoiceResponse)
async def speak(request: VoiceRequest) -> VoiceResponse:
    return _response(
        await voice_service.speak_npc(
            npc_id=request.npc_id,
            text=request.text,
            emotion=request.emotion,
            intensity=request.intensity,
        )
    )


@router.get("/lines/{line_id}", response_model=VoiceResponse)
async def fixed_line(line_id: str) -> VoiceResponse:
    return _response(await voice_service.get_fixed_line(line_id))
