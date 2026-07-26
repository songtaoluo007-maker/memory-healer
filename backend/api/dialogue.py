"""对话API"""

import json

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator
from slowapi import Limiter
from slowapi.util import get_remote_address

from backend.application.dialogue_service import DialogueResult, DialogueService
from backend.config import settings
from backend.domain.game_state import GameState
from backend.engine.butterfly import record_choice
from backend.engine.npc import chat_with_npc_stream
from backend.engine.world import CONTENT_REGISTRY, get_fragment
from backend.integrations.deepseek import DeepSeekDialogueClient

limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix="/api/dialogue", tags=["dialogue"])
dialogue_service = DialogueService(
    CONTENT_REGISTRY,
    DeepSeekDialogueClient(
        api_key=settings.DEEPSEEK_API_KEY,
        base_url=settings.DEEPSEEK_BASE_URL,
        model=settings.DEEPSEEK_MODEL,
        connect_timeout_seconds=settings.DEEPSEEK_CONNECT_TIMEOUT_SECONDS,
        total_timeout_seconds=settings.DEEPSEEK_TOTAL_TIMEOUT_SECONDS,
        max_retries=settings.DEEPSEEK_MAX_RETRIES,
        failure_threshold=settings.DEEPSEEK_FAILURE_THRESHOLD,
        cooldown_seconds=settings.DEEPSEEK_COOLDOWN_SECONDS,
    ),
)


class ApiRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")


class DialogueRequest(ApiRequest):
    npc_id: str
    player_input: str
    game_state: GameState
    expected_revision: int = Field(ge=0)

    @field_validator("npc_id")
    @classmethod
    def validate_npc_id(cls, v: str) -> str:
        if not v or len(v) > 50:
            raise ValueError("npc_id长度必须在1-50之间")
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError("npc_id只能包含字母、数字、下划线和连字符")
        return v

    @field_validator("player_input")
    @classmethod
    def validate_player_input(cls, v: str) -> str:
        normalized = v.strip()
        if not normalized or len(normalized) > 500:
            raise ValueError("输入长度必须在1-500之间")
        return normalized


@router.post("/chat", response_model=DialogueResult)
@limiter.limit("10/minute")
def dialogue_chat(req: DialogueRequest, request: Request):
    """与 NPC 对话，并返回唯一权威的新游戏状态。"""
    return dialogue_service.chat(
        req.game_state,
        npc_id=req.npc_id,
        player_input=req.player_input,
        expected_revision=req.expected_revision,
    )


class LegacyStreamDialogueRequest(BaseModel):
    """Temporary compatibility contract removed by the canonical frontend migration."""

    npc_id: str
    player_input: str
    game_state: dict


@router.post("/chat/stream")
@limiter.limit("10/minute")
def dialogue_chat_stream(req: LegacyStreamDialogueRequest, request: Request):
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
