"""
蝴蝶效应引擎 — 1972年的选择影响2024/2089的场景描述和NPC对话

设计:
- player_choices: 记录每个场景中的关键选择
- butterfly_effects: 定义选择→影响的映射规则
- get_scene_modifiers(): 根据历史选择返回场景描述修改片段
- get_npc_modifiers(): 根据历史选择返回NPC对话上下文修改
"""

from typing import Any


# ── 蝴蝶效应规则定义 ──

BUTTERFLY_RULES: list[dict[str, Any]] = [
    # 1972年 → 2024年
    {
        "id": "encourage_puppetry",
        "trigger": {
            "scene": "scene_1972",
            "choice_key": "encourage_art",
            "min_trust": {"chen_shouyi_young": 50},
        },
        "effects": [
            {
                "target_scene": "scene_2024",
                "scene_mod": "墙上多了一张泛黄的演出海报——\"陈守义皮影戏专场\"，边角已经卷起，但被仔细抚平过。",
                "npc_mod": {
                    "chen_shouyi_old": "他谈起年轻时的演出，眼里闪过一丝光芒：'有人曾经告诉我，手艺不该被埋没。'"
                },
            },
            {
                "target_scene": "scene_2089",
                "scene_mod": "全息投影中多了一段完整的皮影戏表演影像——\"三英战吕布\"，画面清晰而生动。",
            },
        ],
    },
    {
        "id": "discourage_puppetry",
        "trigger": {
            "scene": "scene_1972",
            "choice_key": "discourage_art",
            "min_trust": {"chen_shouyi_young": 40},
        },
        "effects": [
            {
                "target_scene": "scene_2024",
                "scene_mod": "桌上没有刻刀，只有一堆文件和一个计算器。墙角的皮影箱子蒙着厚厚的灰。",
                "npc_mod": {
                    "chen_shouyi_old": "他叹了口气：'年轻时有人劝我放弃，说这行没前途。我差点就信了。'"
                },
            },
        ],
    },
    # 1972年 → 2089年
    {
        "id": "tell_about_xiaoyu",
        "trigger": {
            "scene": "scene_1972",
            "choice_key": "mention_xiaoyu",
            "min_trust": {"chen_shouyi_young": 60},
        },
        "effects": [
            {
                "target_scene": "scene_2089",
                "npc_mod": {
                    "xiaoyu": "小雨看着你，眼眶微红：'爷爷年轻时候……还记得我吗？他跟你提过我？'"
                },
            },
        ],
    },
    # 2024年 → 2089年
    {
        "id": "find_xiaoyu_letter",
        "trigger": {
            "scene": "scene_2024",
            "choice_key": "found_letter",
            "min_trust": {"xiaoyu": 50},
        },
        "effects": [
            {
                "target_scene": "scene_2089",
                "npc_mod": {
                    "xiaoyu": "小雨轻声说：'那封信……我一直以为丢了。原来在爷爷那里。谢谢你找到它。'",
                },
                "fragment_boost": {"xiaoyu": 10},
            },
        ],
    },
    {
        "id": "help_old_chenshouyi",
        "trigger": {
            "scene": "scene_2024",
            "choice_key": "help_elderly",
            "min_trust": {"chen_shouyi_old": 55},
        },
        "effects": [
            {
                "target_scene": "scene_2089",
                "scene_mod": "实验室的AI助手声音温柔了几分：'陈守义先生的记忆修复进展良好——有人曾经给过他温暖。'",
            },
        ],
    },
]


def get_butterfly_effects(game_state: dict[str, Any]) -> list[dict[str, Any]]:
    """根据玩家历史选择，计算触发的蝴蝶效应"""
    triggered = []
    player_choices = game_state.get("butterfly_choices", {})
    npc_trust = game_state.get("npc_trust", {})

    for rule in BUTTERFLY_RULES:
        trigger = rule["trigger"]
        choice_key = trigger["choice_key"]
        scene = trigger["scene"]

        # 检查是否做出对应选择
        if player_choices.get(scene) != choice_key:
            continue

        # 检查信任度条件
        trust_met = True
        for npc_id, min_trust in trigger.get("min_trust", {}).items():
            if npc_trust.get(npc_id, 30) < min_trust:
                trust_met = False
                break

        if trust_met:
            triggered.append(rule)

    return triggered


def get_scene_modifiers(game_state: dict[str, Any], target_scene: str) -> list[str]:
    """获取目标场景的描述修改片段"""
    effects = get_butterfly_effects(game_state)
    mods = []
    for effect in effects:
        for eff in effect["effects"]:
            if eff.get("target_scene") == target_scene and eff.get("scene_mod"):
                mods.append(eff["scene_mod"])
    return mods


def get_npc_modifiers(game_state: dict[str, Any], target_scene: str, npc_id: str) -> list[str]:
    """获取目标NPC的对话上下文修改"""
    effects = get_butterfly_effects(game_state)
    mods = []
    for effect in effects:
        for eff in effect["effects"]:
            if eff.get("target_scene") == target_scene:
                npc_mods = eff.get("npc_mod", {})
                if npc_id in npc_mods:
                    mods.append(npc_mods[npc_id])
    return mods


def get_fragment_boost(game_state: dict[str, Any], npc_id: str) -> int:
    """获取碎片揭露的信任度加成"""
    effects = get_butterfly_effects(game_state)
    boost = 0
    for effect in effects:
        for eff in effect["effects"]:
            boost += eff.get("fragment_boost", {}).get(npc_id, 0)
    return boost


def record_choice(game_state: dict[str, Any], scene: str, choice: str) -> dict[str, Any]:
    """记录玩家选择"""
    if "butterfly_choices" not in game_state:
        game_state["butterfly_choices"] = {}
    game_state["butterfly_choices"][scene] = choice
    return game_state
