"""
蝴蝶效应引擎测试
"""
import pytest
from backend.engine.butterfly import (
    get_butterfly_effects,
    get_scene_modifiers,
    get_npc_modifiers,
    get_fragment_boost,
    record_choice,
)


class TestButterflyEffects:
    """蝴蝶效应计算测试"""

    def test_no_choices_no_effects(self):
        """没有选择时无效应"""
        state = {"butterfly_choices": {}, "npc_trust": {}}
        effects = get_butterfly_effects(state)
        assert len(effects) == 0

    def test_encourage_puppetry_triggered(self):
        """鼓励皮影戏触发效应"""
        state = {
            "butterfly_choices": {"scene_1972": "encourage_art"},
            "npc_trust": {"chen_shouyi_young": 60},
        }
        effects = get_butterfly_effects(state)
        assert len(effects) >= 1
        assert any(e["id"] == "encourage_puppetry" for e in effects)

    def test_encourage_puppetry_low_trust(self):
        """信任度不足不触发"""
        state = {
            "butterfly_choices": {"scene_1972": "encourage_art"},
            "npc_trust": {"chen_shouyi_young": 30},
        }
        effects = get_butterfly_effects(state)
        assert len(effects) == 0

    def test_discourage_puppetry_triggered(self):
        """劝阻皮影戏触发效应"""
        state = {
            "butterfly_choices": {"scene_1972": "discourage_art"},
            "npc_trust": {"chen_shouyi_young": 50},
        }
        effects = get_butterfly_effects(state)
        assert len(effects) >= 1
        assert any(e["id"] == "discourage_puppetry" for e in effects)

    def test_scene_modifiers_for_2024(self):
        """获取2024年场景修改"""
        state = {
            "butterfly_choices": {"scene_1972": "encourage_art"},
            "npc_trust": {"chen_shouyi_young": 60},
        }
        mods = get_scene_modifiers(state, "scene_2024")
        assert len(mods) >= 1
        assert any("海报" in m or "刻刀" in m for m in mods)

    def test_npc_modifiers_for_old_chen(self):
        """获取老年陈守义的对话修改"""
        state = {
            "butterfly_choices": {"scene_1972": "encourage_art"},
            "npc_trust": {"chen_shouyi_young": 60},
        }
        mods = get_npc_modifiers(state, "scene_2024", "chen_shouyi_old")
        assert len(mods) >= 1

    def test_fragment_boost(self):
        """碎片揭露信任度加成"""
        state = {
            "butterfly_choices": {"scene_2024": "found_letter"},
            "npc_trust": {"xiaoyu": 60},
        }
        boost = get_fragment_boost(state, "xiaoyu")
        assert boost >= 10

    def test_record_choice(self):
        """记录玩家选择"""
        state = {}
        updated = record_choice(state, "scene_1972", "encourage_art")
        assert updated["butterfly_choices"]["scene_1972"] == "encourage_art"

    def test_record_choice_overwrite(self):
        """覆盖已有选择"""
        state = {"butterfly_choices": {"scene_1972": "old_choice"}}
        updated = record_choice(state, "scene_1972", "new_choice")
        assert updated["butterfly_choices"]["scene_1972"] == "new_choice"

    def test_multiple_effects_accumulate(self):
        """多个效应累积"""
        state = {
            "butterfly_choices": {
                "scene_1972": "encourage_art",
                "scene_2024": "found_letter",
            },
            "npc_trust": {
                "chen_shouyi_young": 60,
                "xiaoyu": 60,
            },
        }
        effects = get_butterfly_effects(state)
        assert len(effects) >= 2


class TestEdgeCases:
    """边界情况测试"""

    def test_empty_game_state(self):
        """空游戏状态"""
        state = {}
        effects = get_butterfly_effects(state)
        assert len(effects) == 0

    def test_none_trust(self):
        """信任度为None"""
        state = {
            "butterfly_choices": {"scene_1972": "encourage_art"},
            "npc_trust": {},
        }
        effects = get_butterfly_effects(state)
        assert len(effects) == 0

    def test_unknown_scene(self):
        """未知场景"""
        mods = get_scene_modifiers({}, "scene_unknown")
        assert len(mods) == 0

    def test_unknown_npc(self):
        """未知NPC"""
        mods = get_npc_modifiers({}, "scene_2024", "unknown_npc")
        assert len(mods) == 0
