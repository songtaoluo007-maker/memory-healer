"""engine/world.py 单元测试"""
import pytest
from backend.engine.world import (
    get_scene, get_npc, get_fragment,
    get_npc_by_scene, get_scene_fragments,
    get_all_scene_ids, create_initial_state,
)


def test_get_scene_valid():
    scene = get_scene("scene_1972")
    assert scene is not None
    assert scene["title"] == "1972年 · 西安老巷"
    assert scene["time_period"] == "1972"


def test_get_scene_invalid():
    assert get_scene("nonexistent") is None


def test_get_npc_valid():
    npc = get_npc("chen_shouyi_young")
    assert npc is not None
    assert npc["name"] == "陈守义"
    assert npc["age"] == 25


def test_get_npc_invalid():
    assert get_npc("nonexistent") is None


def test_get_fragment_valid():
    frag = get_fragment("fragment_shadow_puppet")
    assert frag is not None
    assert frag["name"] == "皮影戏台"
    assert frag["scene"] == "scene_1972"


def test_get_fragment_invalid():
    assert get_fragment("nonexistent") is None


def test_get_npc_by_scene():
    npcs = get_npc_by_scene("scene_1972")
    assert len(npcs) == 1
    assert npcs[0]["id"] == "chen_shouyi_young"


def test_get_npc_by_scene_empty():
    npcs = get_npc_by_scene("nonexistent")
    assert len(npcs) == 0


def test_get_scene_fragments():
    frags = get_scene_fragments("scene_1972")
    assert len(frags) == 3
    ids = [f["id"] for f in frags]
    assert "fragment_shadow_puppet" in ids


def test_get_all_scene_ids():
    ids = get_all_scene_ids()
    assert len(ids) == 5
    assert "scene_1972" in ids
    assert "scene_1990" in ids
    assert "scene_2024" in ids
    assert "scene_2050" in ids
    assert "scene_2089" in ids


def test_create_initial_state():
    state = create_initial_state()
    assert state["current_scene"] == "scene_1972"
    assert state["collected_fragments"] == []
    assert state["chapter"] == 1
    assert state["ending"] is None
    assert len(state["fragment_states"]) == 17
    # 所有碎片初始状态为未收集
    for fid, fstate in state["fragment_states"].items():
        assert fstate["collected"] is False
        assert fstate["revealed"] is False
