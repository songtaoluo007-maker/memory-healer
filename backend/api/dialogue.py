"""对话API"""
import json
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address
from backend.engine.npc import chat_with_npc, chat_with_npc_stream
from backend.engine.world import get_fragment

limiter = Limiter(key_func=get_remote_address)
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
    inner_thought: str = ""


@router.post("/chat", response_model=DialogueResponse)
@limiter.limit("10/minute")
def dialogue_chat(req: DialogueRequest, request: Request):
    """与NPC对话（同步）"""
    result = chat_with_npc(req.npc_id, req.player_input, req.game_state)
    fragment_data = None
    if result.get("fragment_revealed"):
        fragment_data = get_fragment(result["fragment_revealed"])
    return DialogueResponse(
        reply=result["reply"],
        fragment_revealed=result.get("fragment_revealed"),
        fragment_data=fragment_data,
        trust_change=result.get("trust_change", 0),
        npc_mood=result.get("npc_mood", "neutral"),
        inner_thought=result.get("inner_thought", ""),
    )


@router.post("/chat/stream")
@limiter.limit("10/minute")
def dialogue_chat_stream(req: DialogueRequest, request: Request):
    """与NPC对话（SSE 流式）"""

    def event_generator():
        buffer = ""
        metadata = {}
        for chunk in chat_with_npc_stream(req.npc_id, req.player_input, req.game_state):
            if chunk["type"] == "token":
                buffer += chunk["content"]
                yield f"data: {json.dumps({'type': 'token', 'content': chunk['content']}, ensure_ascii=False)}\n\n"
            elif chunk["type"] == "done":
                metadata = chunk["metadata"]
                fragment_data = None
                if metadata.get("fragment_revealed"):
                    fragment_data = get_fragment(metadata["fragment_revealed"])
                yield f"data: {json.dumps({'type': 'done', 'reply': buffer, 'fragment_revealed': metadata.get('fragment_revealed'), 'fragment_data': fragment_data, 'trust_change': metadata.get('trust_change', 0), 'npc_mood': metadata.get('npc_mood', 'neutral'), 'inner_thought': metadata.get('inner_thought', '')}, ensure_ascii=False)}\n\n"
            elif chunk["type"] == "error":
                yield f"data: {json.dumps({'type': 'error', 'content': chunk['content']}, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
