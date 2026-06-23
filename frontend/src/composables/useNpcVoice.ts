/**
 * NPC语音系统 — 基于浏览器SpeechSynthesis API
 * 每个NPC有独立的声线特征
 */
import { ref } from 'vue'

// NPC语音配置
interface VoiceConfig {
  name: string           // 优先使用的语音名称关键词
  pitch: number          // 0.1-2.0
  rate: number           // 0.1-10.0
  volume: number         // 0-1
  gender: 'male' | 'female' | 'elder'
}

const npcVoiceConfigs: Record<string, VoiceConfig> = {
  zhou: {
    name: '',
    pitch: 0.7,      // 低沉
    rate: 0.75,       // 缓慢
    volume: 0.9,
    gender: 'elder',
  },
  xiaoyu: {
    name: '',
    pitch: 1.4,       // 高亮
    rate: 1.0,        // 正常
    volume: 0.85,
    gender: 'female',
  },
  wang: {
    name: '',
    pitch: 1.0,
    rate: 0.9,
    volume: 0.85,
    gender: 'female',
  },
  zhao: {
    name: '',
    pitch: 0.65,      // 很低
    rate: 1.05,       // 略快
    volume: 0.95,
    gender: 'male',
  },
  li: {
    name: '',
    pitch: 0.85,
    rate: 0.8,        // 沉稳
    volume: 0.9,
    gender: 'male',
  },
  liu: {
    name: '',
    pitch: 1.1,
    rate: 1.1,        // 语速快（记者）
    volume: 0.85,
    gender: 'female',
  },
  chen: {
    name: '',
    pitch: 0.55,      // 极低沉
    rate: 0.6,        // 很慢
    volume: 0.8,
    gender: 'elder',
  },
}

// 全局状态
const voiceEnabled = ref(true)
const currentNpcId = ref<string | null>(null)
let currentUtterance: SpeechSynthesisUtterance | null = null

// 缓存中文语音
let zhVoices: SpeechSynthesisVoice[] = []
let voicesLoaded = false

function loadVoices() {
  if (voicesLoaded) return
  const allVoices = speechSynthesis.getVoices()
  zhVoices = allVoices.filter(v =>
    v.lang.startsWith('zh') ||
    v.lang.startsWith('cmn') ||
    v.name.includes('Chinese') ||
    v.name.includes('中文')
  )
  voicesLoaded = zhVoices.length > 0
}

// 尝试加载语音（Chrome异步加载）
if (typeof speechSynthesis !== 'undefined') {
  speechSynthesis.onvoiceschanged = loadVoices
  loadVoices()
}

/**
 * 选择最佳匹配的中文语音
 */
function selectVoice(config: VoiceConfig): SpeechSynthesisVoice | null {
  if (zhVoices.length === 0) return null

  // 按性别筛选
  const genderKeywords: Record<string, string[]> = {
    male: ['male', '男', 'hui', 'liang'],
    female: ['female', '女', 'xiaoxiao', 'xiaomo', 'yaoyao'],
    elder: ['male', '男', 'hui'],
  }

  const keywords = genderKeywords[config.gender] || []

  // 先按关键词匹配
  for (const kw of keywords) {
    const match = zhVoices.find(v => v.name.toLowerCase().includes(kw))
    if (match) return match
  }

  // 退而求其次，用第一个中文语音
  return zhVoices[0] || null
}

/**
 * 清洗文本 — 去除JSON残留、特殊字符
 */
function cleanText(text: string): string {
  return text
    .replace(/\{[^}]*\}/g, '')           // 去JSON块
    .replace(/\[[^\]]*\]/g, '')          // 去方括号标签
    .replace(/[{}"\[\]]/g, '')           // 去残留符号
    .replace(/\s+/g, ' ')               // 压缩空白
    .replace(/。{2,}/g, '。')            // 去重复句号
    .trim()
    .substring(0, 300)                   // 限制长度
}

/**
 * 播放NPC语音
 */
function speak(text: string, npcId: string) {
  if (!voiceEnabled.value) return
  if (typeof speechSynthesis === 'undefined') return

  // 停止当前朗读
  stop()

  const cleaned = cleanText(text)
  if (!cleaned || cleaned.length < 2) return

  const config = npcVoiceConfigs[npcId] || npcVoiceConfigs.zhou

  const utterance = new SpeechSynthesisUtterance(cleaned)
  const voice = selectVoice(config)

  if (voice) utterance.voice = voice
  utterance.pitch = config.pitch
  utterance.rate = config.rate
  utterance.volume = config.volume
  utterance.lang = 'zh-CN'

  currentNpcId.value = npcId
  currentUtterance = utterance

  utterance.onend = () => {
    currentNpcId.value = null
    currentUtterance = null
  }

  utterance.onerror = () => {
    currentNpcId.value = null
    currentUtterance = null
  }

  speechSynthesis.speak(utterance)
}

/**
 * 停止朗读
 */
function stop() {
  if (speechSynthesis.speaking) {
    speechSynthesis.cancel()
  }
  currentNpcId.value = null
  currentUtterance = null
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
 * 检查浏览器是否支持语音合成
 */
function isSupported(): boolean {
  return typeof speechSynthesis !== 'undefined'
}

export function useNpcVoice() {
  return {
    voiceEnabled,
    currentNpcId,
    speak,
    stop,
    toggleVoice,
    isSupported,
  }
}
