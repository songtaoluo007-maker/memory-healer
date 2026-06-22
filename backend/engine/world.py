"""世界状态管理"""
import json
from pathlib import Path
from typing import Optional

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def load_json(name: str) -> dict:
    path = DATA_DIR / name
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


SCENES = load_json("scenes.json")
NPCS = load_json("npcs.json")
FRAGMENTS = load_json("fragments.json")


def get_scene(scene_id: str) -> Optional[dict]:
    return SCENES.get(scene_id)


def get_npc(npc_id: str) -> Optional[dict]:
    return NPCS.get(npc_id)


def get_npc_by_scene(scene_id: str) -> list[dict]:
    scene = SCENES.get(scene_id, {})
    npc_ids = scene.get("npcs", [])
    return [NPCS[nid] for nid in npc_ids if nid in NPCS]


def get_fragment(fragment_id: str) -> Optional[dict]:
    return FRAGMENTS.get(fragment_id)


def get_scene_fragments(scene_id: str) -> list[dict]:
    scene = SCENES.get(scene_id, {})
    fids = scene.get("fragments", [])
    return [FRAGMENTS[fid] for fid in fids if fid in FRAGMENTS]


def get_all_scene_ids() -> list[str]:
    return list(SCENES.keys())


def create_initial_state() -> dict:
    """创建初始游戏状态"""
    # 初始化所有碎片为未收集
    fragment_states = {}
    for fid, fdata in FRAGMENTS.items():
        fragment_states[fid] = {
            "id": fid,
            "name": fdata["name"],
            "collected": False,
            "revealed": False,
            "scene": fdata["scene"],
        }

    import time
    return {
        "current_scene": "scene_1972",
        "collected_fragments": [],
        "revealed_fragments": [],
        "fragment_states": fragment_states,
        "npc_trust": {},
        "key_choices": [],
        "dialogue_history": [],
        "current_mood": "warm",
        "play_time": 0,
        "play_start_time": int(time.time() * 1000),
        "chapter": 1,
        "ending": None,
    }
