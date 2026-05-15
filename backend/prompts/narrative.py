"""叙事引擎Prompt模板"""


def build_narrative_prompt(game_state: dict, action: str) -> str:
    """构建叙事推进Prompt"""
    scene_id = game_state.get("current_scene", "scene_1972")
    collected = game_state.get("collected_fragments", [])
    choices = game_state.get("key_choices", [])
    mood = game_state.get("current_mood", "warm")

    return f"""你是一位游戏叙事AI，负责推进游戏剧情和场景描述。

## 当前状态
- 当前场景: {scene_id}
- 已收集记忆碎片: {', '.join(collected) if collected else '无'}
- 关键选择: {', '.join(choices) if choices else '无'}
- 当前氛围: {mood}

## 玩家行动
{action}

## 输出要求
1. 场景描述 80-120字，要有画面感和情感
2. 根据已收集碎片和选择调整氛围
3. 如果触发了关键剧情，要自然过渡
4. 结尾暗示玩家可以做什么

请严格按JSON格式输出:
{{
  "scene_description": "场景描述文本",
  "available_actions": ["行动1", "行动2", "行动3"],
  "mood": "warm/tense/melancholy/hopeful/neutral",
  "hints": "给玩家的暗示",
  "trigger_event": null
}}"""
