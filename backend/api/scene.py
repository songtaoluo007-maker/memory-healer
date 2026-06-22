"""场景API"""
from fastapi import APIRouter
from pydantic import BaseModel
from backend.engine.narrative import advance_narrative
from backend.engine.world import (
    get_scene, get_npc_by_scene, get_scene_fragments,
    get_all_scene_ids, create_initial_state,
)
from backend.engine.butterfly import get_scene_modifiers, get_npc_modifiers

router = APIRouter(prefix="/api/scene", tags=["scene"])


class SceneRequest(BaseModel):
    scene_id: str
    game_state: dict


class ActionRequest(BaseModel):
    action: str
    game_state: dict


@router.get("/list")
def list_scenes():
    """获取所有场景列表"""
    scenes = []
    for sid in get_all_scene_ids():
        scene = get_scene(sid)
        if scene:
            scenes.append({
                "id": sid,
                "title": scene["title"],
                "mood": scene["mood"],
            })
    return {"scenes": scenes}


@router.post("/detail")
def scene_detail(req: SceneRequest):
    """获取场景详情"""
    scene = get_scene(req.scene_id)
    if not scene:
        return {"error": "场景不存在"}

    npcs = get_npc_by_scene(req.scene_id)
    fragments = get_scene_fragments(req.scene_id)

    # 标记碎片收集状态
    collected = req.game_state.get("collected_fragments", [])
    fragment_list = []
    for f in fragments:
        fragment_list.append({
            **f,
            "is_collected": f["id"] in collected,
        })

    return {
        "scene": scene,
        "npcs": [{"id": n["id"], "name": n["name"], "title": n["title"], "avatar": n["avatar"]} for n in npcs],
        "fragments": fragment_list,
        "butterfly_mods": get_scene_modifiers(req.game_state, req.scene_id),
    }


@router.post("/advance")
def advance(req: ActionRequest):
    """推进叙事"""
    result = advance_narrative(req.game_state, req.action)
    return result


@router.get("/initial-state")
def initial_state():
    """获取初始游戏状态"""
    return create_initial_state()
