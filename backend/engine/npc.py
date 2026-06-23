"""NPC对话引擎 — JSON输出解析"""
import json
import re
from typing import Optional
from loguru import logger
from openai import OpenAI
from backend.config import settings
from backend.engine.world import get_npc, get_scene
from backend.prompts.npc_dialogue import build_npc_prompt
from backend.engine.butterfly import get_npc_modifiers, get_fragment_boost
from backend.engine.emotion import process_emotion

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


def _parse_json_response(content: str) -> tuple:
    """
    解析NPC的JSON输出，返回 (reply, fragment, trust_delta, emotion, inner_thought)
    兼容旧版标签格式作为降级方案
    """
    # 尝试清理markdown包裹
    cleaned = content.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()

    # 尝试JSON解析
    try:
        data = json.loads(cleaned)
        # AI可能用reply/content/message字段
        reply = data.get("reply", "").strip()
        if not reply:
            reply = data.get("content", "").strip()
        if not reply:
            reply = data.get("message", "").strip()
        fragment = data.get("fragment")
        trust_delta = data.get("trust_delta", 0)
        emotion = data.get("emotion", "neutral")
        inner_thought = data.get("inner_thought", "")

        # 如果reply为空但有原始内容，尝试从content提取
        if not reply and "reply" not in data:
            # AI可能返回了非标准JSON，用正则提取
            m = re.search(r'"reply"\s*:\s*"((?:[^"\\]|\\.)*)"', cleaned)
            if m:
                reply = m.group(1).replace('\\"', '"').replace('\\n', '\n').strip()

        # 校验emotion枚举
        valid_emotions = {"neutral", "happy", "sad", "thinking", "touched", "nostalgic", "worried"}
        if emotion not in valid_emotions:
            emotion = "neutral"

        # 校验trust_delta范围
        if not isinstance(trust_delta, (int, float)):
            trust_delta = 0
        trust_delta = max(-20, min(20, int(trust_delta)))

        if reply:
            return reply, fragment, trust_delta, emotion, inner_thought
    except (json.JSONDecodeError, KeyError, TypeError):
        pass

    # 降级：用正则提取reply字段（支持reply/content/message）
    for field in ['reply', 'content', 'message']:
        m = re.search(rf'"{field}"\s*:\s*"((?:[^"\\]|\\.)*)"', cleaned)
        if m:
            reply = m.group(1).replace('\\"', '"').replace('\\n', '\n').strip()
            frag_match = re.search(r'"fragment"\s*:\s*"?([^",}]+)', cleaned)
            fragment = frag_match.group(1).strip() if frag_match and frag_match.group(1) != 'null' else None
            trust_match = re.search(r'"trust_delta"\s*:\s*(-?\d+)', cleaned)
            trust_change = int(trust_match.group(1)) if trust_match else 0
            emotion_match = re.search(r'"emotion"\s*:\s*"(\w+)"', cleaned)
            emotion = emotion_match.group(1) if emotion_match else "neutral"
            thought_match = re.search(r'"inner_thought"\s*:\s*"((?:[^"\\]|\\.)*)"', cleaned)
            inner_thought = thought_match.group(1) if thought_match else ""
            return reply, fragment, trust_change, emotion, inner_thought

    # 最终降级：旧版标签解析
    return _parse_legacy_tags(cleaned)


def _parse_legacy_tags(content: str) -> tuple:
    """兼容旧版 [碎片:xxx] [信任:+N] [心情:xxx] 标签格式"""
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

    return content, fragment_revealed, trust_change, npc_mood, ""


def chat_with_npc(npc_id: str, player_input: str, game_state: dict) -> dict:
    """
    与NPC对话，返回AI生成的回复和状态更新

    Returns:
        {
            "reply": "NPC回复文本",
            "fragment_revealed": "fragment_id" or None,
            "trust_change": int,
            "npc_mood": "happy/sad/neutral/thinking/touched/nostalgic/worried",
            "inner_thought": "NPC内心独白"
        }
    """
    npc = get_npc(npc_id)
    if not npc:
        return {"reply": "[系统] 找不到这个角色。", "fragment_revealed": None, "trust_change": 0, "npc_mood": "neutral", "inner_thought": ""}

    scene = get_scene(npc["scene"])
    if not scene:
        return {"reply": "[系统] 场景加载失败。", "fragment_revealed": None, "trust_change": 0, "npc_mood": "neutral", "inner_thought": ""}

    prompt = build_npc_prompt(npc, scene, game_state, player_input)

    # 蝴蝶效应: 添加NPC对话上下文修改
    butterfly_mods = get_npc_modifiers(game_state, npc["scene"], npc_id)
    if butterfly_mods:
        mods_text = "\n".join(butterfly_mods)
        prompt += f"\n\n【记忆回响】{mods_text}"

    # 情感状态机: 处理玩家输入对NPC情感的影响
    emotion_result = process_emotion(npc_id, player_input, game_state)
    if emotion_result["prompt_hint"]:
        prompt += f"\n\n{emotion_result['prompt_hint']}"

    try:
        client = _get_client()

        response = client.chat.completions.create(
            model=settings.DEEPSEEK_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=400,
        )

        content = response.choices[0].message.content.strip()

        # 解析JSON回复
        reply_text, fragment_revealed, trust_change, npc_mood, inner_thought = _parse_json_response(content)

        # 情感状态机: 应用信任度乘数
        trust_multiplier = emotion_result["trust_multiplier"]
        trust_change = int(trust_change * trust_multiplier)

        # 情感状态机: 碎片揭露加成
        fragment_bonus = emotion_result["fragment_bonus"]
        if fragment_revealed and fragment_bonus > 0:
            # 如果有碎片揭露且有情感加成，增加信任度
            trust_change += fragment_bonus // 5

        # 情感转移效果描述
        emotion_effect = emotion_result["emotion_change"]["effect"]
        if emotion_effect:
            reply_text = f"{reply_text}\n\n*{emotion_effect}*"

        return {
            "reply": reply_text,
            "fragment_revealed": fragment_revealed,
            "trust_change": trust_change,
            "npc_mood": npc_mood,
            "inner_thought": inner_thought,
            "emotion_state": emotion_result["emotion_change"]["current"],
        }

    except Exception as e:
        logger.error(f"NPC对话失败: {e}")
        return {
            "reply": f"[系统] 对话引擎暂时不可用，请稍后重试。",
            "fragment_revealed": None,
            "trust_change": 0,
            "npc_mood": "neutral",
            "inner_thought": "",
        }


def chat_with_npc_stream(npc_id: str, player_input: str, game_state: dict):
    """流式 NPC 对话，yield token 和最终元数据"""
    npc = get_npc(npc_id)
    if not npc:
        yield {"type": "error", "content": "找不到这个角色。"}
        return

    scene = get_scene(npc["scene"])
    if not scene:
        yield {"type": "error", "content": "场景加载失败。"}
        return

    prompt = build_npc_prompt(npc, scene, game_state, player_input)

    # 蝴蝶效应: 添加NPC对话上下文修改
    butterfly_mods = get_npc_modifiers(game_state, npc["scene"], npc_id)
    if butterfly_mods:
        mods_text = "\n".join(butterfly_mods)
        prompt += f"\n\n【记忆回响】{mods_text}"

    # 情感状态机: 处理玩家输入对NPC情感的影响
    emotion_result = process_emotion(npc_id, player_input, game_state)
    if emotion_result["prompt_hint"]:
        prompt += f"\n\n{emotion_result['prompt_hint']}"

    try:
        client = _get_client()
        stream = client.chat.completions.create(
            model=settings.DEEPSEEK_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=400,
            stream=True,
        )

        full_content = ""
        reply_buffer = ""
        # 状态机: 0=等待JSON 1=等待reply键 2=等待reply值引号 3=在reply值内 4=reply结束
        state = 0
        escape_next = False
        # AI可能用reply/content/message等字段名
        reply_keys = ['"reply"', '"content"', '"message"']
        found_key = None

        for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                full_content += delta.content
                for ch in delta.content:
                    if escape_next:
                        escape_next = False
                        if state == 3:
                            reply_buffer += ch
                            yield {"type": "token", "content": ch}
                        continue
                    if ch == '\\':
                        escape_next = True
                        if state == 3:
                            reply_buffer += ch
                            yield {"type": "token", "content": ch}
                        continue
                    if state == 0:
                        if ch == '{':
                            state = 1
                        continue
                    if state == 1:
                        # 查找任意reply键
                        if not found_key:
                            for key in reply_keys:
                                idx = full_content.find(key)
                                if idx >= 0:
                                    after_key = full_content[idx + len(key):].lstrip()
                                    if after_key.startswith(':'):
                                        after_colon = after_key[1:].lstrip()
                                        if after_colon.startswith('"'):
                                            state = 3
                                        elif after_colon:
                                            state = 2
                                        found_key = key
                                        break
                        continue
                    if state == 2:
                        if ch == '"':
                            state = 3
                        continue
                    if state == 3:
                        if ch == '"':
                            state = 4
                            continue
                        reply_buffer += ch
                        yield {"type": "token", "content": ch}
                        continue

        # 流结束，解析JSON元数据
        reply_text, fragment_revealed, trust_change, npc_mood, inner_thought = _parse_json_response(full_content)

        # 优先用流式解析器已提取的干净reply_buffer
        if reply_buffer:
            reply_text = reply_buffer

        # 情感状态机: 应用信任度乘数
        trust_multiplier = emotion_result["trust_multiplier"]
        trust_change = int(trust_change * trust_multiplier)

        # 情感转移效果描述
        emotion_effect = emotion_result["emotion_change"]["effect"]
        if emotion_effect:
            reply_text = f"{reply_text}\n\n*{emotion_effect}*"

        yield {
            "type": "done",
            "metadata": {
                "reply": reply_text,
                "fragment_revealed": fragment_revealed,
                "trust_change": trust_change,
                "npc_mood": npc_mood,
                "inner_thought": inner_thought,
                "emotion_state": emotion_result["emotion_change"]["current"],
            },
        }

    except Exception as e:
        logger.error(f"NPC流式对话失败: {e}")
        yield {"type": "error", "content": "对话引擎暂时不可用，请稍后重试。"}
