"""叙事引擎Prompt模板"""


def build_narrative_prompt(game_state: dict, action: str) -> str:
    """构建叙事推进Prompt — 增强版"""
    scene_id = game_state.get("current_scene", "scene_1972")
    collected = game_state.get("collected_fragments", [])
    choices = game_state.get("key_choices", [])
    mood = game_state.get("current_mood", "warm")
    play_time = game_state.get("play_time", 0)
    npc_trust = game_state.get("npc_trust", {})

    # 场景标题映射
    scene_titles = {
        "scene_1972": "1972年 西安老巷",
        "scene_2024": "2024年 深圳城中村",
        "scene_2089": "2089年 拾忆实验室",
    }
    scene_title = scene_titles.get(scene_id, scene_id)

    # 信任度摘要
    trust_summary = ""
    if npc_trust:
        lines = [f"  - {k}: {v}/100" for k, v in npc_trust.items()]
        trust_summary = "\n".join(lines)

    return f"""你是一位获奖的互动叙事设计师，负责为游戏「拾忆」撰写叙事文本。

## 世界观
2089年，阿尔茨海默症已不再是绝症。拾忆科技发明了一种技术——通过AI重建患者的记忆碎片，让他们在梦中重走一生。玩家扮演第一位记忆修复师。

## 当前状态
- 场景: {scene_title}
- 已收集碎片: {len(collected)}/9
- 关键选择: {', '.join(choices) if choices else '无'}
- NPC信任度:
{trust_summary if trust_summary else '  暂无'}
- 玩家游玩时长: {play_time}秒
- 当前氛围: {mood}

## 玩家行动
{action}

## 叙事原则
1. **展示而非告知**: 用细节描写，不说"他很悲伤"
2. **记忆的质感**: 1972年温暖模糊，2024年刺痛清晰，2089年冰冷数字
3. **玩家代理感**: 让玩家觉得自己在影响故事，而非旁观
4. **节奏控制**: 高潮后给喘息，平静中埋伏笔
5. **碎片呼应**: 已收集的碎片内容应该在叙事中自然回响

## 输出要求
1. 场景描述 80-120字，有画面感和情感
2. 根据已收集碎片和选择调整氛围
3. 如果触发了关键剧情，要自然过渡
4. 结尾暗示玩家可以做什么

请严格按JSON格式输出（不要输出其他内容）:
{{
  "scene_description": "场景描述文本（80-120字）",
  "available_actions": ["行动1", "行动2", "行动3"],
  "mood": "warm/tense/melancholy/hopeful/neutral/bittersweet",
  "hints": "给玩家的暗示（20字以内）",
  "trigger_event": null,
  "narrative_callback": "引用已收集碎片的隐喻，加深情感（30字以内，可为空）"
}}"""
