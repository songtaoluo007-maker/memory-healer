"""
NPC情感状态机 — 让情感变化有实际效果

设计:
- 状态转移: neutral ↔ happy ↔ touched ↔ nostalgic, neutral → annoyed, happy → sad
- 情感影响: 影响碎片揭露概率、对话语气、解锁条件
- 情感衰减: 长时间不对话自动回归neutral
"""

from typing import Optional
from datetime import datetime


# ── 情感状态定义 ──

EMOTION_STATES = {
    "neutral": {
        "name": "平静",
        "description": "NPC处于正常状态",
        "fragment_bonus": 0,
        "trust_multiplier": 1.0,
        "decay_target": None,
    },
    "happy": {
        "name": "开心",
        "description": "NPC心情愉悦，更愿意分享",
        "fragment_bonus": 10,
        "trust_multiplier": 1.2,
        "decay_target": "neutral",
    },
    "touched": {
        "name": "感动",
        "description": "NPC被触动，可能揭露深层记忆",
        "fragment_bonus": 20,
        "trust_multiplier": 1.5,
        "decay_target": "happy",
    },
    "nostalgic": {
        "name": "怀旧",
        "description": "NPC沉浸在回忆中，容易触发特殊碎片",
        "fragment_bonus": 25,
        "trust_multiplier": 1.3,
        "decay_target": "neutral",
    },
    "sad": {
        "name": "难过",
        "description": "NPC情绪低落，需要安慰",
        "fragment_bonus": -5,
        "trust_multiplier": 0.8,
        "decay_target": "neutral",
    },
    "annoyed": {
        "name": "不悦",
        "description": "NPC感到被冒犯，对话效率降低",
        "fragment_bonus": -15,
        "trust_multiplier": 0.5,
        "decay_target": "neutral",
    },
    "worried": {
        "name": "担忧",
        "description": "NPC有所顾虑，需要建立信任",
        "fragment_bonus": -5,
        "trust_multiplier": 0.7,
        "decay_target": "neutral",
    },
}


# ── 情感转移规则 ──

EMOTION_TRANSITIONS = {
    "neutral": {
        "关心": "happy",
        "鼓励": "happy",
        "询问过去": "nostalgic",
        "冷漠": "annoyed",
        "冒犯": "annoyed",
        "默认": "neutral",
    },
    "happy": {
        "深入话题": "touched",
        "分享记忆": "touched",
        "打断": "neutral",
        "冷漠": "sad",
        "默认": "happy",
    },
    "touched": {
        "安慰": "happy",
        "继续深入": "nostalgic",
        "信任破裂": "sad",
        "默认": "touched",
    },
    "nostalgic": {
        "倾听": "touched",
        "分享": "happy",
        "打断": "neutral",
        "默认": "nostalgic",
    },
    "sad": {
        "安慰": "neutral",
        "关心": "happy",
        "冷漠": "annoyed",
        "默认": "sad",
    },
    "annoyed": {
        "道歉": "neutral",
        "耐心": "neutral",
        "继续冒犯": "annoyed",
        "默认": "annoyed",
    },
    "worried": {
        "建立信任": "neutral",
        "鼓励": "happy",
        "施压": "annoyed",
        "默认": "worried",
    },
}


# ── 情感分析关键词 ──

EMOTION_KEYWORDS = {
    "关心": ["你好", "怎么样", "还好吗", "身体", "注意", "保重", "关心"],
    "鼓励": ["加油", "坚持", "厉害", "很好", "不错", "相信", "支持"],
    "询问过去": ["以前", "当年", "过去", "年轻", "记得", "那时候"],
    "深入话题": ["然后呢", "后来", "继续", "说说", "告诉我", "详细"],
    "分享记忆": ["我也", "我记得", "我想起", "有一次"],
    "安慰": ["别难过", "没事", "会好的", "没关系", "别担心"],
    "倾听": ["嗯", "我在听", "继续说", "我理解"],
    "道歉": ["对不起", "抱歉", "不好意思", "我不是故意"],
    "耐心": ["慢慢来", "不急", "等你", "没关系"],
    "建立信任": ["我在这里", "相信我", "我会帮", "不孤单"],
    "冷漠": ["不知道", "无所谓", "随便", "不想"],
    "冒犯": ["烦", "无聊", "废话", "闭嘴", "讨厌"],
    "打断": ["等一下", "停", "别说", "够了"],
    "施压": ["快点", "赶紧", "必须", "一定要"],
}


class EmotionStateMachine:
    """NPC情感状态机"""

    def __init__(self, npc_id: str, initial_emotion: str = "neutral"):
        self.npc_id = npc_id
        self.emotion = initial_emotion
        self.emotion_history = [(initial_emotion, datetime.now().isoformat())]
        self.transition_count = 0

    def analyze_input(self, player_input: str) -> str:
        """分析玩家输入，返回情感触发类型"""
        for trigger_type, keywords in EMOTION_KEYWORDS.items():
            for keyword in keywords:
                if keyword in player_input:
                    return trigger_type
        return "默认"

    def transition(self, trigger_type: str) -> dict:
        """
        执行情感转移

        Returns:
            {
                "previous": str,
                "current": str,
                "changed": bool,
                "trigger": str,
                "effect": str
            }
        """
        current_rules = EMOTION_TRANSITIONS.get(self.emotion, {})
        new_emotion = current_rules.get(trigger_type, current_rules.get("默认", self.emotion))

        changed = new_emotion != self.emotion
        previous = self.emotion

        if changed:
            self.emotion = new_emotion
            self.emotion_history.append((new_emotion, datetime.now().isoformat()))
            self.transition_count += 1

        return {
            "previous": previous,
            "current": self.emotion,
            "changed": changed,
            "trigger": trigger_type,
            "effect": self._get_transition_effect(previous, new_emotion),
        }

    def _get_transition_effect(self, old: str, new: str) -> str:
        """获取情感转移的描述效果"""
        effects = {
            ("neutral", "happy"): "他的表情放松了下来，嘴角微微上扬。",
            ("neutral", "nostalgic"): "他的眼神变得悠远，仿佛穿越了时光。",
            ("neutral", "annoyed"): "他皱了皱眉，似乎有些不悦。",
            ("happy", "touched"): "他的眼眶微微湿润，声音变得柔和。",
            ("happy", "sad"): "他的笑容消失了，沉默了下来。",
            ("touched", "nostalgic"): "他陷入了深深的回忆。",
            ("sad", "neutral"): "他深吸一口气，情绪渐渐平复。",
            ("annoyed", "neutral"): "他的表情缓和了下来。",
            ("worried", "happy"): "他露出了释然的笑容。",
        }
        return effects.get((old, new), "")

    def get_fragment_bonus(self) -> int:
        """获取当前情感对碎片揭露的加成"""
        return EMOTION_STATES.get(self.emotion, {}).get("fragment_bonus", 0)

    def get_trust_multiplier(self) -> float:
        """获取当前情感对信任度变化的乘数"""
        return EMOTION_STATES.get(self.emotion, {}).get("trust_multiplier", 1.0)

    def get_prompt_hint(self) -> str:
        """获取当前情感状态的Prompt提示"""
        state = EMOTION_STATES.get(self.emotion, {})
        if self.emotion == "neutral":
            return ""
        return f"[当前情感: {state['name']}] {state['description']}"

    def to_dict(self) -> dict:
        """序列化"""
        return {
            "npc_id": self.npc_id,
            "emotion": self.emotion,
            "transition_count": self.transition_count,
            "history_length": len(self.emotion_history),
        }


# ── 全局状态管理 ──

_emotion_machines: dict[str, EmotionStateMachine] = {}


def get_emotion_machine(npc_id: str) -> EmotionStateMachine:
    """获取或创建NPC的情感状态机"""
    if npc_id not in _emotion_machines:
        _emotion_machines[npc_id] = EmotionStateMachine(npc_id)
    return _emotion_machines[npc_id]


def process_emotion(npc_id: str, player_input: str, game_state: dict) -> dict:
    """
    处理玩家输入对NPC情感的影响

    Returns:
        {
            "emotion_change": {...},
            "fragment_bonus": int,
            "trust_multiplier": float,
            "prompt_hint": str
        }
    """
    machine = get_emotion_machine(npc_id)

    # 从游戏状态恢复情感
    saved_emotion = game_state.get("npc_emotions", {}).get(npc_id)
    if saved_emotion and machine.emotion == "neutral":
        machine.emotion = saved_emotion

    # 分析输入并执行转移
    trigger_type = machine.analyze_input(player_input)
    change = machine.transition(trigger_type)

    # 保存到游戏状态
    if "npc_emotions" not in game_state:
        game_state["npc_emotions"] = {}
    game_state["npc_emotions"][npc_id] = machine.emotion

    return {
        "emotion_change": change,
        "fragment_bonus": machine.get_fragment_bonus(),
        "trust_multiplier": machine.get_trust_multiplier(),
        "prompt_hint": machine.get_prompt_hint(),
    }
