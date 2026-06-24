"""结局评估 API"""

from fastapi import APIRouter
from pydantic import BaseModel
from ..engine.ending import evaluate_ending, get_ending_hint

router = APIRouter(prefix="/api/ending", tags=["ending"])


class GameStateRequest(BaseModel):
    game_state: dict


@router.post("/evaluate")
async def evaluate(req: GameStateRequest):
    """评估当前结局"""
    return evaluate_ending(req.game_state)


@router.post("/hint")
async def hint(req: GameStateRequest):
    """获取结局提示"""
    return {"hint": get_ending_hint(req.game_state)}
