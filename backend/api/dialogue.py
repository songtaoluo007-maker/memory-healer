"""对话API"""
import json
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, validator
from slowapi import Limiter
from slowapi.util import get_remote_address
from backend.engine.npc import chat_with_npc, chat_with_npc_stream
from backend.engine.world import get_fragment
from backend.engine.butterfly import record_choice

limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix="/api/dialogue", tags=["dialogue"])


class DialogueRequest(BaseModel):
    npc_id: str
    player_input: str
    game_state: dict

    @validator('npc_id')
    def validate_npc_id(cls, v):
        if not v or len(v) > 50:
            raise ValueError('npc_id长度必须在1-50之间')
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('npc_id只能包含字母、数字、下划线和连字符')
        return v

    @validator('player_input')
    def validate_player_input(cls, v):
        if not v or len(v) > 500:
            raise ValueError('输入长度必须在1-500之间')
        # 基本XSS防护
        dangerous_patterns = ['<script', 'javascript:', 'onerror=', 'onload=']
        v_lower = v.lower()
        for pattern in dangerous_patterns:
            if pattern in v_lower:
                raise ValueError('输入包含不允许的内容')
        return v.strip()


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


class ChoiceRequest(BaseModel):
    scene: str
    choice: str
    game_state: dict


@router.post("/choice")
def record_player_choice(req: ChoiceRequest):
    """记录玩家选择（蝴蝶效应触发）"""
    updated_state = record_choice(req.game_state, req.scene, req.choice)
    return {"status": "ok", "butterfly_choices": updated_state.get("butterfly_choices", {})}
