"""蝴蝶效应可视化 API"""

from fastapi import APIRouter
from pydantic import BaseModel
from ..engine.butterfly import get_butterfly_effects, BUTTERFLY_RULES

router = APIRouter(prefix="/api/butterfly", tags=["butterfly"])


class GameStateRequest(BaseModel):
    game_state: dict


@router.post("/status")
async def status(req: GameStateRequest):
    """获取蝴蝶效应状态"""
    triggered = get_butterfly_effects(req.game_state)
    triggered_ids = {t["id"] for t in triggered}
    choices = req.game_state.get("butterfly_choices", {})

    rules = []
    for rule in BUTTERFLY_RULES:
        r = {
            "id": rule["id"],
            "trigger_scene": rule["trigger"]["scene"],
            "trigger_choice": rule["trigger"]["choice_key"],
            "triggered": rule["id"] in triggered_ids,
            "effects_count": len(rule["effects"]),
            "target_scenes": [e["target_scene"] for e in rule["effects"]],
        }
        rules.append(r)

    return {
        "triggered_count": len(triggered),
        "total_rules": len(BUTTERFLY_RULES),
        "choices_made": choices,
        "rules": rules,
    }
