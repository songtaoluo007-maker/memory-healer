/**
 * NPC语音系统 — 基于后端Edge TTS (微软神经网络语音)
 * 比浏览器SpeechSynthesis自然得多，支持SSML感情控制
 */
import { ref } from 'vue'

// 全局状态
const voiceEnabled = ref(true)
const currentNpcId = ref<string | null>(null)
const isPlaying = ref(false)
let currentAudio: HTMLAudioElement | null = null

// TTS缓存（避免重复请求）
const ttsCache = new Map<string, string>()

// API base
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

/**
 * 清洗文本
 */
function cleanText(text: string): string {
  // 先检测是否是JSON/代码，如果是则不朗读
  const jsonKeys = ['reply', 'content', 'message', 'fragment', 'emotion', 'trust_delta', 'inner_thought', 'suggested_reaction']
  const lower = text.toLowerCase()
  if (jsonKeys.some(k => lower.includes(`"${k}"`))) {
    // 包含JSON键名，尝试提取reply字段值
    const m = text.match(/"(?:reply|content|message)"\s*:\s*"([^"]+)"/)
    if (m) text = m[1]
    else return ''  // 无法提取，不朗读
  }

  return text
    .replace(/\{[^}]*\}/g, '')
    .replace(/\[[^\]]*\]/g, '')
    .replace(/[{}"\[\]]/g, '')
    .replace(/[a-zA-Z_]{10,}/g, '')       // 去长英文单词（代码残留）
    .replace(/\s+/g, ' ')
    .replace(/。{2,}/g, '。')
    .trim()
    .substring(0, 300)
}

/**
 * 停止当前播放
 */
function stop() {
  if (currentAudio) {
    currentAudio.pause()
    currentAudio.src = ''
    currentAudio = null
  }
  currentNpcId.value = null
  isPlaying.value = false
}

/**
 * 播放NPC语音
 */
async function speak(text: string, npcId: string) {
  if (!voiceEnabled.value) return

  // 停止当前播放
  stop()

  const cleaned = cleanText(text)
  if (!cleaned || cleaned.length < 2) return

  const cacheKey = `${npcId}:${cleaned}`

  // 检查缓存
  let audioUrl = ttsCache.get(cacheKey)

  if (!audioUrl) {
    // 调用后端TTS API
    try {
      const res = await fetch(`${API_BASE}/api/tts/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: cleaned, npc_id: npcId }),
      })

      if (!res.ok) {
        console.warn('[TTS] 生成失败:', res.status)
        return
      }

      const data = await res.json()
      audioUrl = `${API_BASE}${data.audio_url}`
      ttsCache.set(cacheKey, audioUrl)
    } catch (err) {
      console.warn('[TTS] 请求失败:', err)
      return
    }
  }

  // 播放音频
  try {
    currentNpcId.value = npcId
    isPlaying.value = true

    const audio = new Audio(audioUrl)
    currentAudio = audio

    audio.onended = () => {
      currentNpcId.value = null
      isPlaying.value = false
      currentAudio = null
    }

    audio.onerror = () => {
      currentNpcId.value = null
      isPlaying.value = false
      currentAudio = null
      // 从缓存移除失败的URL
      ttsCache.delete(cacheKey)
    }

    await audio.play()
  } catch (err) {
    console.warn('[TTS] 播放失败:', err)
    currentNpcId.value = null
    isPlaying.value = false
  }
}

/**
 * 切换语音开关
 */
function toggleVoice() {
  voiceEnabled.value = !voiceEnabled.value
  if (!voiceEnabled.value) {
    stop()
  }
}

/**
 * 检查是否支持
 */
function isSupported(): boolean {
  return typeof Audio !== 'undefined'
}

/**
 * 清理缓存（释放内存）
 */
function clearCache() {
  ttsCache.clear()
}

export function useNpcVoice() {
  return {
    voiceEnabled,
    currentNpcId,
    isPlaying,
    speak,
    stop,
    toggleVoice,
    isSupported,
    clearCache,
  }
}
