"""对话API"""

from fastapi import APIRouter, Request
from pydantic import BaseModel, ConfigDict, Field, field_validator
from slowapi import Limiter
from slowapi.util import get_remote_address

from backend.application.dialogue_service import DialogueResult, DialogueService
from backend.config import settings
from backend.domain.game_state import GameState
from backend.engine.world import CONTENT_REGISTRY
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
