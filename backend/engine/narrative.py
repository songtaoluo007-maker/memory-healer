"""叙事引擎"""
import json
from loguru import logger
from openai import OpenAI
from backend.config import settings
from backend.prompts.narrative import build_narrative_prompt

# ── OpenAI 客户端单例 ──
_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(
            api_key=settings.DEEPSEEK_API_KEY,
            base_url=settings.DEEPSEEK_BASE_URL,
            timeout=30,
        )
    return _client


def advance_narrative(game_state: dict, action: str) -> dict:
    """
    推进叙事，根据玩家行动生成场景描述

    Returns:
        {
            "scene_description": "...",
            "available_actions": [...],
            "mood": "...",
            "hints": "...",
            "trigger_event": None or "event_name"
        }
    """
    prompt = build_narrative_prompt(game_state, action)

    try:
        client = _get_client()

        response = client.chat.completions.create(
            model=settings.DEEPSEEK_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,
            max_tokens=500,
        )

        content = response.choices[0].message.content.strip()

        # 清理markdown代码块包裹
        if content.startswith("```json"):
            content = content[7:]
        elif content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

        try:
            result = json.loads(content)
            return {
                "scene_description": result.get("scene_description", ""),
                "available_actions": result.get("available_actions", []),
                "mood": result.get("mood", "neutral"),
                "hints": result.get("hints", ""),
                "trigger_event": result.get("trigger_event"),
                "narrative_callback": result.get("narrative_callback", ""),
            }
        except json.JSONDecodeError:
            # 如果JSON解析失败，返回纯文本
            return {
                "scene_description": content[:500],
                "available_actions": ["继续探索", "与人交谈", "查看周围"],
                "mood": "neutral",
                "hints": "",
                "trigger_event": None,
                "narrative_callback": "",
            }

    except Exception as e:
        logger.error(f"叙事引擎失败: {e}")
        return {
            "scene_description": "周围的场景变得模糊，记忆碎片在你眼前闪烁……",
            "available_actions": ["重新聚焦", "深呼吸", "继续前进"],
            "mood": "neutral",
            "hints": "尝试重新连接记忆通道",
            "trigger_event": None,
            "narrative_callback": "",
        }
