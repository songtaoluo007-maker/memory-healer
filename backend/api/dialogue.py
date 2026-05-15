"""对话API"""
from fastapi import APIRouter
from pydantic import BaseModel
from backend.engine.npc import chat_with_npc
from backend.engine.world import get_fragment

router = APIRouter(prefix="/api/dialogue", tags=["dialogue"])


class DialogueRequest(BaseModel):
    npc_id: str
    player_input: str
    game_state: dict


class DialogueResponse(BaseModel):
    reply: str
    fragment_revealed: str | None = None
    fragment_data: dict | None = None
    trust_change: int = 0
    npc_mood: str = "neutral"


@router.post("/chat", response_model=DialogueResponse)
def dialogue_chat(req: DialogueRequest):
    """与NPC对话"""
    result = chat_with_npc(req.npc_id, req.player_input, req.game_state)

    # 如果揭示了碎片，返回碎片详情
    fragment_data = None
    if result.get("fragment_revealed"):
        fragment_data = get_fragment(result["fragment_revealed"])

    return DialogueResponse(
        reply=result["reply"],
        fragment_revealed=result.get("fragment_revealed"),
        fragment_data=fragment_data,
        trust_change=result.get("trust_change", 0),
        npc_mood=result.get("npc_mood", "neutral"),
    )
