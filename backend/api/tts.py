"""语音合成API"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.engine.tts import generate_tts_sync

router = APIRouter(prefix="/api/tts", tags=["tts"])


class TTSRequest(BaseModel):
    text: str
    npc_id: str


@router.post("/generate")
def generate_voice(req: TTSRequest):
    """为NPC对话生成语音"""
    if not req.text or not req.npc_id:
        raise HTTPException(status_code=400, detail="缺少text或npc_id")

    print(f"[TTS] npc={req.npc_id}, text={req.text[:100]}")
    path = generate_tts_sync(req.text, req.npc_id)
    if not path:
        raise HTTPException(status_code=500, detail="语音生成失败")

    return {"success": True, "audio_url": f"/static/{path}"}
