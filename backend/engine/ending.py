"""
结局引擎 — 根据碎片收集、蝴蝶效应、NPC信任度判定结局

结局类型:
- hope (光): 碎片≥80% 或 全部收集
- bittersweet (余温): 碎片40%-79%
- tragic (消散): 碎片<40% 且有碎片
- legacy (传承): 全部碎片 + 3个以上关键选择 + 关键NPC信任≥60
"""

from typing import Any
from .butterfly import get_butterfly_effects, BUTTERFLY_RULES


# 关键选择（每个场景最重要的选择）
KEY_CHOICES = {
    "scene_1972": ["encourage_art", "discourage_art"],
    "scene_1990": ["talk_to_stranger", "ignore_stranger"],
    "scene_2024": ["found_letter", "help_elderly"],
    "scene_2050": ["accept_award", "reject_award"],
}

KEY_TRUST_THRESHOLD = 60
KEY_NPCS = ["chen_shouyi_young", "chen_shouyi_old", "xiaoyu"]


def evaluate_ending(game_state: dict[str, Any]) -> dict[str, Any]:
    """
    评判结局，返回 { type, title, description, stats }
    """
    collected = game_state.get("collected_fragments", [])
    fragment_states = game_state.get("fragment_states", {})
    total = len(fragment_states) if fragment_states else 17
    percent = (len(collected) / total * 100) if total > 0 else 0
    npc_trust = game_state.get("npc_trust", {})
    butterfly_choices = game_state.get("butterfly_choices", {})

    # 计算蝴蝶效应触发情况
    triggered_effects = get_butterfly_effects(game_state)
    triggered_count = len(triggered_effects)

    # 计算关键选择数量
    key_choices_made = 0
    for scene, valid_choices in KEY_CHOICES.items():
        choice = butterfly_choices.get(scene)
        if choice and choice in valid_choices:
            key_choices_made += 1

    # 关键NPC信任度
    key_trust_met = all(
        npc_trust.get(npc_id, 0) >= KEY_TRUST_THRESHOLD
        for npc_id in KEY_NPCS
    )
    trust_count = sum(
        1 for npc_id in KEY_NPCS
        if npc_trust.get(npc_id, 0) >= KEY_TRUST_THRESHOLD
    )

    # 判定结局
    # legacy: 全碎片 + 3+关键选择 + 全关键NPC高信任
    if percent >= 100 and key_choices_made >= 3 and key_trust_met:
        ending_type = "legacy"
    elif percent >= 80:
        ending_type = "hope"
    elif percent >= 40:
        ending_type = "bittersweet"
    else:
        ending_type = "tragic"

    return {
        "type": ending_type,
        "collected": len(collected),
        "total": total,
        "percent": round(percent, 1),
        "butterfly_triggered": triggered_count,
        "butterfly_total": len(BUTTERFLY_RULES),
        "key_choices_made": key_choices_made,
        "key_trust_met": key_trust_met,
        "trust_count": trust_count,
        "npc_trust": npc_trust,
    }


def get_ending_hint(game_state: dict[str, Any]) -> str:
    """
    返回当前进度的结局提示（给前端展示）
    """
    result = evaluate_ending(game_state)
    ending_type = result["type"]
    percent = result["percent"]
    key_choices = result["key_choices_made"]
    trust_count = result["trust_count"]

    hints = {
        "hope": f"记忆修复进展良好（{percent}%）。继续收集碎片，也许能达到更好的结局。",
        "bittersweet": f"记忆修复进度中等（{percent}%）。试着多和NPC交流，收集更多碎片。",
        "tragic": f"记忆碎片不足（{percent}%）。回到之前的场景，多探索、多对话。",
        "legacy": "所有记忆碎片收集完毕，关键选择已完成，NPC信任度很高。完美的传承结局！",
    }

    base = hints.get(ending_type, "")

    # 提示差什么条件
    if ending_type != "legacy":
        if percent < 100:
            base += f"\n碎片: {result['collected']}/{result['total']}（{percent}%）"
        if key_choices < 3:
            base += f"\n关键选择: {key_choices}/3（需要更多关键对话选择）"
        if trust_count < 3:
            base += f"\nNPC信任: {trust_count}/3（需要与关键NPC建立更深信任）"

    return base
