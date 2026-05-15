"""NPC对话引擎"""
import json
import re
from typing import Optional
from loguru import logger
from openai import OpenAI
from backend.config import settings
from backend.engine.world import get_npc, get_scene
from backend.prompts.npc_dialogue import build_npc_prompt


def chat_with_npc(npc_id: str, player_input: str, game_state: dict) -> dict:
    """
    与NPC对话，返回AI生成的回复和状态更新

    Returns:
        {
            "reply": "NPC回复文本",
            "fragment_revealed": "fragment_id" or None,
            "trust_change": int,
            "npc_mood": "happy/sad/neutral/thinking"
        }
    """
    npc = get_npc(npc_id)
    if not npc:
        return {"reply": "[系统] 找不到这个角色。", "fragment_revealed": None, "trust_change": 0, "npc_mood": "neutral"}

    scene = get_scene(npc["scene"])
    if not scene:
        return {"reply": "[系统] 场景加载失败。", "fragment_revealed": None, "trust_change": 0, "npc_mood": "neutral"}

    prompt = build_npc_prompt(npc, scene, game_state, player_input)

    try:
        client = OpenAI(
            api_key=settings.DEEPSEEK_API_KEY,
            base_url=settings.DEEPSEEK_BASE_URL,
            timeout=30,
        )

        response = client.chat.completions.create(
            model=settings.DEEPSEEK_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=300,
        )

        content = response.choices[0].message.content.strip()

        # 解析回复
        reply_text, fragment_revealed, trust_change, npc_mood = _parse_npc_response(content)

        return {
            "reply": reply_text,
            "fragment_revealed": fragment_revealed,
            "trust_change": trust_change,
            "npc_mood": npc_mood,
        }

    except Exception as e:
        logger.error(f"NPC对话失败: {e}")
        return {
            "reply": f"[系统] 对话引擎暂时不可用，请稍后重试。",
            "fragment_revealed": None,
            "trust_change": 0,
            "npc_mood": "neutral",
        }


def _parse_npc_response(content: str) -> tuple:
    """解析NPC回复中的标签"""
    fragment_revealed = None
    trust_change = 0
    npc_mood = "neutral"

    # 提取 [碎片:xxx]
    frag_match = re.search(r'\[碎片[:：](.+?)\]', content)
    if frag_match:
        frag_val = frag_match.group(1).strip()
        if frag_val and frag_val != "无":
            fragment_revealed = frag_val
        content = re.sub(r'\[碎片[:：].+?\]', '', content).strip()

    # 提取 [信任:+N]
    trust_match = re.search(r'\[信任[:：]([+-]?\d+)\]', content)
    if trust_match:
        trust_change = int(trust_match.group(1))
        content = re.sub(r'\[信任[:：].+?\]', '', content).strip()

    # 提取 [心情:xxx]
    mood_match = re.search(r'\[心情[:：](.+?)\]', content)
    if mood_match:
        npc_mood = mood_match.group(1).strip()
        content = re.sub(r'\[心情[:：].+?\]', '', content).strip()

    return content, fragment_revealed, trust_change, npc_mood
