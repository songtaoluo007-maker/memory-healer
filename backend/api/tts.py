"""TTS语音合成API - 使用Edge TTS"""
import asyncio
import tempfile
import os
from fastapi import APIRouter
from fastapi.responses import Response
from pydantic import BaseModel

router = APIRouter(prefix="/api/tts", tags=["tts"])

# NPC语音映射（与 npcs.json 中的 ID 一致）
NPC_VOICES = {
    # 陈守义 25岁 · 1972年西安 — 年轻男性，沉稳
    "chen_shouyi_young": {"voice": "zh-CN-YunxiNeural", "rate": "+0%", "pitch": "+0Hz"},
    # 陈守义 43岁 · 1990年深圳 — 中年男性，略低沉
    "chen_shouyi_1990": {"voice": "zh-CN-YunxiNeural", "rate": "-10%", "pitch": "-5Hz"},
    # 站台陌生人 28岁 · 1990年 — 年轻男性，干练
    "stranger_1990": {"voice": "zh-CN-YunjianNeural", "rate": "+0%", "pitch": "+0Hz"},
    # 陈守义 77岁 · 2024年 — 老年男性，缓慢低沉
    "chen_shouyi_old": {"voice": "zh-CN-YunyangNeural", "rate": "-20%", "pitch": "-15Hz"},
    # 小雨 48岁 · 2050年 — 中年女性，成熟稳重
    "xiaoyu_2050": {"voice": "zh-CN-XiaoxiaoNeural", "rate": "-5%", "pitch": "-5Hz"},
    # 记者 30岁 · 2050年 — 年轻职业女性
    "journalist_2050": {"voice": "zh-CN-XiaoyiNeural", "rate": "+0%", "pitch": "+0Hz"},
    # 小雨 22岁 · 2089年 — 年轻女性，活泼
    "xiaoyu": {"voice": "zh-CN-XiaoyiNeural", "rate": "+5%", "pitch": "+5Hz"},
}

DEFAULT_VOICE = {"voice": "zh-CN-XiaoxiaoNeural", "rate": "+0%", "pitch": "+0Hz"}

# 缓存目录
CACHE_DIR = os.path.join(tempfile.gettempdir(), "mh_tts_cache")
os.makedirs(CACHE_DIR, exist_ok=True)


class TTSRequest(BaseModel):
    text: str
    npc_id: str = ""


@router.post("/speak")
async def speak(req: TTSRequest):
    """生成NPC语音，返回MP3音频"""
    import edge_tts

    text = req.text.strip()
    if not text:
        return Response(content=b"", media_type="audio/mpeg")

    # 截断过长文本
    if len(text) > 200:
        text = text[:200] + "……"

    config = NPC_VOICES.get(req.npc_id, DEFAULT_VOICE)

    # 生成缓存key
    import hashlib
    cache_key = hashlib.md5(f"{req.npc_id}:{text}".encode()).hexdigest()
    cache_path = os.path.join(CACHE_DIR, f"{cache_key}.mp3")

    # 检查缓存
    if os.path.exists(cache_path):
        with open(cache_path, "rb") as f:
            return Response(content=f.read(), media_type="audio/mpeg")

    # 生成语音
    try:
        communicate = edge_tts.Communicate(
            text=text,
            voice=config["voice"],
            rate=config["rate"],
            pitch=config["pitch"],
        )

        # 写入临时文件
        tmp_path = cache_path + ".tmp"
        await communicate.save(tmp_path)

        # 读取并返回
        with open(tmp_path, "rb") as f:
            audio_data = f.read()

        # 重命名为缓存
        os.rename(tmp_path, cache_path)

        return Response(content=audio_data, media_type="audio/mpeg")
    except Exception as e:
        # 回退到空响应
        return Response(content=b"", media_type="audio/mpeg")
