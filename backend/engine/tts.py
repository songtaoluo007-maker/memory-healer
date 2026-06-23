"""NPC语音生成 — 基于Edge TTS (微软神经网络语音)

每个NPC有独立声线 + SSML感情控制
"""
import asyncio
import hashlib
import os
import edge_tts

# 静态文件目录
TTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "tts")
os.makedirs(TTS_DIR, exist_ok=True)

# NPC语音配置
# 可用中文语音:
#   zh-CN-YunjianNeural   (男, 沉稳有力)
#   zh-CN-YunxiNeural     (男, 年轻温和)
#   zh-CN-YunyangNeural   (男, 新闻播音)
#   zh-CN-YunxiaNeural    (男, 少年)
#   zh-CN-XiaoxiaoNeural  (女, 温暖自然)
#   zh-CN-XiaoyiNeural    (女, 温柔知性)
#   zh-CN-liaoning-XiaobeiNeural (女, 东北口音)
#   zh-CN-shaanxi-XiaoniNeural  (女, 陕西口音)

NPC_VOICES = {
    "zhou": {
        "voice": "zh-CN-YunjianNeural",
        "rate": "-15%",
        "pitch": "-10Hz",
    },
    "xiaoyu": {
        "voice": "zh-CN-XiaoxiaoNeural",
        "rate": "+5%",
        "pitch": "+5Hz",
    },
    "wang": {
        "voice": "zh-CN-shaanxi-XiaoniNeural",
        "rate": "-5%",
        "pitch": "+0Hz",
    },
    "zhao": {
        "voice": "zh-CN-YunyangNeural",
        "rate": "+0%",
        "pitch": "-15Hz",
    },
    "li": {
        "voice": "zh-CN-YunxiNeural",
        "rate": "-10%",
        "pitch": "-5Hz",
    },
    "liu": {
        "voice": "zh-CN-XiaoyiNeural",
        "rate": "+10%",
        "pitch": "+0Hz",
    },
    "chen": {
        "voice": "zh-CN-YunjianNeural",
        "rate": "-25%",
        "pitch": "-20Hz",
    },
}

# 默认语音（兜底）
DEFAULT_VOICE = {
    "voice": "zh-CN-YunxiNeural",
    "rate": "+0%",
    "pitch": "+0Hz",
}


def _clean_text(text: str) -> str:
    """清洗文本，去除JSON残留和特殊字符"""
    import re
    # 如果文本包含JSON结构，先提取reply/content/message字段的值
    if '{' in text and '"' in text:
        for field in ['reply', 'content', 'message']:
            m = re.search(rf'"{field}"\s*:\s*"((?:[^"\\]|\\.)*)"', text)
            if m:
                text = m.group(1).replace('\\"', '"').replace('\\n', '\n')
                break
    text = re.sub(r'\{[^}]*\}', '', text)
    text = re.sub(r'\[[^\]]*\]', '', text)
    text = re.sub(r'[{}"\[\]]', '', text)
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'。{2,}', '。', text)
    return text.strip()[:500]  # 限制500字


def _make_filename(text: str, npc_id: str) -> str:
    """根据文本内容生成唯一文件名"""
    h = hashlib.md5(f"{npc_id}:{text}".encode()).hexdigest()[:12]
    return f"{npc_id}_{h}.mp3"


async def generate_tts(text: str, npc_id: str) -> str | None:
    """
    生成NPC语音MP3文件
    返回: 文件名（相对路径），失败返回None
    """
    cleaned = _clean_text(text)
    if not cleaned or len(cleaned) < 2:
        return None

    # 最终校验：如果还包含JSON键名，不生成
    json_keys = ['reply', 'content', 'message', 'fragment', 'emotion', 'trust_delta', 'inner_thought']
    lower = cleaned.lower()
    if any(f'"{k}"' in lower for k in json_keys):
        print(f"[TTS] 拒绝朗读（含JSON键名）: {cleaned[:80]}")
        return None

    filename = _make_filename(cleaned, npc_id)
    filepath = os.path.join(TTS_DIR, filename)

    # 如果已缓存，直接返回
    if os.path.exists(filepath):
        return f"tts/{filename}"

    config = NPC_VOICES.get(npc_id, DEFAULT_VOICE)

    # 直接用纯文本 + Communicate参数（不用SSML，避免标签被当文本朗读）
    try:
        communicate = edge_tts.Communicate(
            cleaned,
            voice=config["voice"],
            rate=config["rate"],
            pitch=config["pitch"]
        )
        await communicate.save(filepath)
        return f"tts/{filename}"
    except Exception as e:
        print(f"[TTS] 生成失败: {e}")
        return None


def generate_tts_sync(text: str, npc_id: str) -> str | None:
    """同步版本（用于非async上下文）"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # 如果事件循环已在运行，用线程池
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, generate_tts(text, npc_id))
                return future.result(timeout=15)
        else:
            return loop.run_until_complete(generate_tts(text, npc_id))
    except Exception:
        try:
            return asyncio.run(generate_tts(text, npc_id))
        except Exception:
            return None


def cleanup_old_tts(max_files: int = 500):
    """清理旧的TTS文件（保留最新的max_files个）"""
    files = sorted(TTS_DIR.glob("*.mp3"), key=lambda f: f.stat().st_mtime, reverse=True)
    for f in files[max_files:]:
        f.unlink(missing_ok=True)
