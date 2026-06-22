"""
蝴蝶效应引擎 — 跨越1972→1990→2024→2050→2089的因果链

设计:
- player_choices: 记录每个场景中的关键选择
- butterfly_effects: 定义选择→影响的映射规则
- get_scene_modifiers(): 根据历史选择返回场景描述修改片段
- get_npc_modifiers(): 根据历史选择返回NPC对话上下文修改
"""

from typing import Any


# ── 蝴蝶效应规则定义 ──

BUTTERFLY_RULES: list[dict[str, Any]] = [
    # ── 1972年 → 1990年 ──
    {
        "id": "encourage_puppetry_1972_1990",
        "trigger": {
            "scene": "scene_1972",
            "choice_key": "encourage_art",
            "min_trust": {"chen_shouyi_young": 50},
        },
        "effects": [
            {
                "target_scene": "scene_1990",
                "scene_mod": "木箱里的皮影道具比平时多了一倍——他把爷爷留下的所有皮影都带上了。箱盖内侧贴着一张纸条：'手艺不该被埋没。'",
                "npc_mod": {
                    "chen_shouyi_1990": "他摸了摸木箱，轻声说：'当年有人说手艺不该被埋没。我一直记着。'",
                },
            },
            {
                "target_scene": "scene_2024",
                "scene_mod": "墙上多了一张泛黄的演出海报——\"陈守义皮影戏专场\"，边角已经卷起，但被仔细抚平过。",
                "npc_mod": {
                    "chen_shouyi_old": "他谈起年轻时的演出，眼里闪过一丝光芒：'有人曾经告诉我，手艺不该被埋没。'",
                },
            },
            {
                "target_scene": "scene_2050",
                "scene_mod": "照片墙上多了一张1990年深圳火车站的照片：年轻的陈守义抱着木箱，眼里有光。"
            },
            {
                "target_scene": "scene_2089",
                "scene_mod": "全息投影中多了一段完整的皮影戏表演影像——\"三英战吕布\"，画面清晰而生动。",
            },
        ],
    },
    {
        "id": "discourage_puppetry_1972_1990",
        "trigger": {
            "scene": "scene_1972",
            "choice_key": "discourage_art",
            "min_trust": {"chen_shouyi_young": 40},
        },
        "effects": [
            {
                "target_scene": "scene_1990",
                "scene_mod": "木箱里只有寥寥几个皮影。陈守义看起来有些犹豫，似乎在考虑要不要把箱子留在站台上。",
                "npc_mod": {
                    "chen_shouyi_1990": "他低头看着木箱，喃喃道：'有人说这行没前途。也许……他说得对。'",
                },
            },
            {
                "target_scene": "scene_2024",
                "scene_mod": "桌上没有刻刀，只有一堆文件和一个计算器。墙角的皮影箱子蒙着厚厚的灰。",
                "npc_mod": {
                    "chen_shouyi_old": "他叹了口气：'年轻时有人劝我放弃，说这行没前途。我差点就信了。'",
                },
            },
        ],
    },
    # ── 1990年 → 2024年/2050年 ──
    {
        "id": "meet_stranger_1990",
        "trigger": {
            "scene": "scene_1990",
            "choice_key": "talk_to_stranger",
            "min_trust": {"stranger_1990": 50},
        },
        "effects": [
            {
                "target_scene": "scene_2024",
                "scene_mod": "桌上有一张名片，已经泛黄：'深圳鹏城文化发展有限公司 李志远'。名片背面写着：'陈师傅，皮影戏的事，随时联系我。'",
                "npc_mod": {
                    "chen_shouyi_old": "他突然想起什么：'1990年在深圳火车站遇到一个人，他说我的皮影能卖钱。后来……他真的帮我开了一场演出。'",
                },
            },
            {
                "target_scene": "scene_2050",
                "scene_mod": "颁奖典礼嘉宾名单中有一个名字：李志远，鹏城文化集团董事长。他坐在第一排，看着台上的小雨，微微点头。"
            },
        ],
    },
    # ── 1972年 → 2089年 ──
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
                    "xiaoyu": "小雨看着你，眼眶微红：'爷爷年轻时候……还记得我吗？他跟你提过我？'",
                },
            },
        ],
    },
    # ── 2024年 → 2050年/2089年 ──
    {
        "id": "letter_inspiration_2024_2050",
        "trigger": {
            "scene": "scene_2024",
            "choice_key": "found_letter",
            "min_trust": {"chen_shouyi_old": 50},
        },
        "effects": [
            {
                "target_scene": "scene_2050",
                "scene_mod": "小雨演讲时提到了那封信：'爷爷收到我6岁时写的信，坐了36个小时火车来深圳。那一刻我知道——记忆可以跨越时间和疾病。'",
                "npc_mod": {
                    "xiaoyu_2050": "小雨轻声说：'那封信……我一直以为丢了。原来在爷爷那里。谢谢帮我找到它的那个人。'",
                },
            },
        ],
    },
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
    # ── 2050年 → 2089年 ──
    {
        "id": "award_memory_2050_2089",
        "trigger": {
            "scene": "scene_2050",
            "choice_key": "accept_award",
            "min_trust": {"xiaoyu_2050": 55},
        },
        "effects": [
            {
                "target_scene": "scene_2089",
                "scene_mod": "实验室的全息相册中多了一段颁奖典礼影像。小雨看着影像说：'爷爷，这是我替你领的奖。'",
                "npc_mod": {
                    "xiaoyu": "小雨的声音有些颤抖：'2050年那个奖杯……我把它放在爷爷病房里了。爷爷摸着奖杯笑了。'",
                },
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

        if player_choices.get(scene) != choice_key:
            continue

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