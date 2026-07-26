"""Non-blocking Edge TTS API."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field

from backend.config import settings
from backend.domain.errors import DomainError
from backend.integrations.tts import TtsRequest as SynthesisRequest
from backend.integrations.tts import TtsService

router = APIRouter(prefix="/api/tts", tags=["tts"])

NPC_VOICES = {
    "chen_shouyi_young": ("zh-CN-YunxiNeural", "+0%", "+0Hz"),
    "chen_shouyi_1990": ("zh-CN-YunxiNeural", "-10%", "-5Hz"),
    "stranger_1990": ("zh-CN-YunjianNeural", "+0%", "+0Hz"),
    "chen_shouyi_old": ("zh-CN-YunyangNeural", "-20%", "-15Hz"),
    "xiaoyu_2050": ("zh-CN-XiaoxiaoNeural", "-5%", "-5Hz"),
    "journalist_2050": ("zh-CN-XiaoyiNeural", "+0%", "+0Hz"),
    "xiaoyu": ("zh-CN-XiaoyiNeural", "+5%", "+5Hz"),
}
DEFAULT_VOICE = ("zh-CN-XiaoxiaoNeural", "+0%", "+0Hz")

tts_service = TtsService(
    settings.TTS_CACHE_DIR,
    max_text_length=settings.TTS_MAX_TEXT_LENGTH,
    max_concurrency=settings.TTS_MAX_CONCURRENCY,
    max_cache_files=settings.TTS_MAX_CACHE_FILES,
    max_cache_bytes=settings.TTS_MAX_CACHE_BYTES,
)


class TTSRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str = Field(min_length=1, max_length=500)
    npc_id: str = Field(default="", max_length=100)


@router.post("/speak")
async def speak(req: TTSRequest) -> dict[str, str | bool]:
    voice, rate, pitch = NPC_VOICES.get(req.npc_id, DEFAULT_VOICE)
    try:
        result = await tts_service.synthesize(
            SynthesisRequest(
                text=req.text,
                voice=voice,
                rate=rate,
                pitch=pitch,
            )
        )
    except ValueError as exc:
        raise DomainError("TTS_INVALID_REQUEST", str(exc)) from exc
    except Exception as exc:
        raise DomainError("TTS_UNAVAILABLE", "语音暂时不可用，请继续阅读文字对白") from exc
    return {"url": result.url, "cached": result.cache_hit}
