"""NPC对话Prompt模板"""


def build_npc_prompt(npc: dict, scene: dict, game_state: dict, player_input: str) -> str:
    """构建NPC对话Prompt"""
    collected = game_state.get("collected_fragments", [])
    trust = game_state.get("npc_trust", {}).get(npc["id"], npc.get("initial_trust", 30))
    revealed = game_state.get("revealed_fragments", [])
    history = game_state.get("dialogue_history", [])[-6:]  # 最近6轮对话

    # 构建对话历史
    history_text = ""
    if history:
        lines = []
        for h in history:
            role = "玩家" if h["role"] == "player" else npc["name"]
            lines.append(f"{role}: {h['content']}")
        history_text = "\n".join(lines)

    # 构建可透露的碎片信息
    fragment_hints = []
    for fid in npc.get("fragments_to_reveal", []):
        if fid not in collected and fid not in revealed:
            fragment_hints.append(f"- {fid}: 尚未透露")
        elif fid in collected:
            fragment_hints.append(f"- {fid}: 已收集")
        else:
            fragment_hints.append(f"- {fid}: 已透露但未收集")

    fragments_text = "\n".join(fragment_hints) if fragment_hints else "无可透露的碎片"

    return f"""{npc['system_prompt']}

## 你的背景
{npc['background']}

## 当前场景
{scene['description']}

## 你与玩家的信任度: {trust}/100
- 0-30: 保持警惕，不会透露重要信息
- 30-60: 开始信任，愿意聊聊日常
- 60-80: 比较信任，愿意分享重要记忆
- 80-100: 完全信任，会主动透露关键信息

## 记忆碎片状态
{fragments_text}

## 已透露的信息
{', '.join(revealed) if revealed else '无'}

## 对话历史
{history_text if history else '这是第一次对话'}

## 对话规则
1. 始终保持角色，不要跳出设定
2. 根据信任度决定透露信息的深度
3. 如果玩家问到你不知道的事情，自然地回避
4. 如果信任度足够且相关碎片未透露，自然地引出记忆碎片
5. 回复末尾标注: [碎片:fragment_id] 或 [碎片:无] 和 [信任:+N] 或 [信任:0]

玩家说: {player_input}"""
