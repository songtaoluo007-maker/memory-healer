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
        "rate": "-15%",       # 缓慢（老人）
        "pitch": "-10%",      # 低沉
        "style": "sad",       # 沧桑感
        "styledegree": "1.5",
    },
    "xiaoyu": {
        "voice": "zh-CN-XiaoxiaoNeural",
        "rate": "+5%",        # 略快（年轻）
        "pitch": "+5%",       # 明亮
        "style": "cheerful",  # 活泼
        "styledegree": "1.2",
    },
    "wang": {
        "voice": "zh-CN-shaanxi-XiaoniNeural",
        "rate": "-5%",        # 略慢
        "pitch": "+0%",
        "style": "friendly",  # 热心
        "styledegree": "1.0",
    },
    "zhao": {
        "voice": "zh-CN-YunyangNeural",
        "rate": "+0%",
        "pitch": "-15%",      # 低沉粗犷
        "style": "angry",     # 粗犷
        "styledegree": "1.0",
    },
    "li": {
        "voice": "zh-CN-YunxiNeural",
        "rate": "-10%",       # 沉稳
        "pitch": "-5%",
        "style": "serious",   # 严肃
        "styledegree": "1.0",
    },
    "liu": {
        "voice": "zh-CN-XiaoyiNeural",
        "rate": "+10%",       # 语速快（记者）
        "pitch": "+0%",
        "style": "chat",      # 健谈
        "styledegree": "1.0",
    },
    "chen": {
        "voice": "zh-CN-YunjianNeural",
        "rate": "-25%",       # 很慢（高龄）
        "pitch": "-20%",      # 很低
        "style": "sad",       # 虚弱
        "styledegree": "2.0",
    },
}

# 默认语音（兜底）
DEFAULT_VOICE = {
    "voice": "zh-CN-YunxiNeural",
    "rate": "+0%",
    "pitch": "+0%",
    "style": "chat",
    "styledegree": "1.0",
}


def _clean_text(text: str) -> str:
    """清洗文本，去除JSON残留和特殊字符"""
    import re
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

    filename = _make_filename(cleaned, npc_id)
    filepath = os.path.join(TTS_DIR, filename)

    # 如果已缓存，直接返回
    if os.path.exists(filepath):
        return f"tts/{filename}"

    config = NPC_VOICES.get(npc_id, DEFAULT_VOICE)

    # 构建SSML
    ssml = f"""
    <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis"
           xmlns:mstts="https://www.w3.org/2001/mstts" xml:lang="zh-CN">
        <voice name="{config['voice']}">
            <mstts:express-as style="{config['style']}" styledegree="{config['styledegree']}">
                <prosody rate="{config['rate']}" pitch="{config['pitch']}">
                    {cleaned}
                </prosody>
            </mstts:express-as>
        </voice>
    </speak>
    """

    try:
        communicate = edge_tts.Communicate(ssml, voice=config["voice"])
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
