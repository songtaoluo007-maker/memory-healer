/**
 * 音效/音乐管理组合式函数
 * 使用 Web Audio API 实现轻量级音频系统
 *
 * 设计原则:
 * - 1972年: 二胡+古筝，温暖怀旧
 * - 2024年: 钢琴+环境音，孤独感
 * - 2089年: 电子合成器+钢琴，科技+温情
 */

import { ref, onUnmounted } from 'vue'

// ── 音频上下文单例 ──
let audioCtx: AudioContext | null = null

function getAudioContext(): AudioContext {
  if (!audioCtx) {
    audioCtx = new AudioContext()
  }
  if (audioCtx.state === 'suspended') {
    audioCtx.resume()
  }
  return audioCtx
}

// ── 场景氛围音配置 ──
const sceneBgmConfig: Record<string, { frequencies: number[]; type: OscillatorType; volume: number }> = {
  scene_1972: {
    // 温暖的五声音阶，模拟古筝/二胡
    frequencies: [261.63, 293.66, 329.63, 392.00, 440.00],
    type: 'sine',
    volume: 0.06,
  },
  scene_2024: {
    // 小调和弦，钢琴感
    frequencies: [261.63, 311.13, 349.23, 415.30],
    type: 'triangle',
    volume: 0.05,
  },
  scene_2089: {
    // 电子合成器感，空灵
    frequencies: [220.00, 277.18, 329.63, 440.00, 554.37],
    type: 'sine',
    volume: 0.04,
  },
}

// ── 环境音配置 ──
const ambientConfig: Record<string, { noise: boolean; filterFreq: number; volume: number }> = {
  scene_1972: { noise: true, filterFreq: 800, volume: 0.015 },   // 温暖的巷子环境
  scene_2024: { noise: true, filterFreq: 400, volume: 0.02 },    // 雨声+车流
  scene_2089: { noise: true, filterFreq: 2000, volume: 0.008 },  // 实验室机器嗡鸣
}

export function useAudio() {
  const isMuted = ref(false)
  const bgmVolume = ref(0.3)
  const sfxVolume = ref(0.5)
  const currentScene = ref('')

  // BGM相关
  let bgmOscillators: OscillatorNode[] = []
  let bgmGain: GainNode | null = null
  let ambientSource: AudioBufferSourceNode | null = null
  let ambientGain: GainNode | null = null

  /**
   * 播放场景BGM — 基于Web Audio API的轻量级氛围音乐
   */
  const playBGM = (sceneId: string) => {
    if (isMuted.value) return
    if (currentScene.value === sceneId && bgmOscillators.length > 0) return

    stopBGM()
    currentScene.value = sceneId

    const ctx = getAudioContext()
    const config = sceneBgmConfig[sceneId] || sceneBgmConfig.scene_1972

    // 主增益节点
    bgmGain = ctx.createGain()
    bgmGain.gain.value = 0
    bgmGain.connect(ctx.destination)

    // 淡入
    bgmGain.gain.linearRampToValueAtTime(
      config.volume * bgmVolume.value,
      ctx.currentTime + 2
    )

    // 创建多声部氛围音
    config.frequencies.forEach((freq, i) => {
      const osc = ctx.createOscillator()
      const oscGain = ctx.createGain()

      osc.type = config.type
      osc.frequency.value = freq

      // 每个声部略有不同的音量和相位
      oscGain.gain.value = 0.3 + (i * 0.1)
      osc.connect(oscGain)
      oscGain.connect(bgmGain!)

      // 缓慢的音量波动，营造呼吸感
      const lfo = ctx.createOscillator()
      const lfoGain = ctx.createGain()
      lfo.frequency.value = 0.1 + (i * 0.05)  // 每个声部不同频率
      lfoGain.gain.value = 0.15
      lfo.connect(lfoGain)
      lfoGain.connect(oscGain.gain)
      lfo.start()

      osc.start()
      bgmOscillators.push(osc)
    })

    // 播放环境音
    playAmbient(sceneId)
  }

  /**
   * 播放环境音 — 白噪声滤波
   */
  const playAmbient = (sceneId: string) => {
    const ctx = getAudioContext()
    const config = ambientConfig[sceneId] || ambientConfig.scene_1972

    // 创建白噪声缓冲
    const bufferSize = ctx.sampleRate * 2
    const buffer = ctx.createBuffer(1, bufferSize, ctx.sampleRate)
    const data = buffer.getChannelData(0)
    for (let i = 0; i < bufferSize; i++) {
      data[i] = (Math.random() * 2 - 1) * 0.5
    }

    ambientSource = ctx.createBufferSource()
    ambientSource.buffer = buffer
    ambientSource.loop = true

    // 低通滤波器
    const filter = ctx.createBiquadFilter()
    filter.type = 'lowpass'
    filter.frequency.value = config.filterFreq
    filter.Q.value = 1

    ambientGain = ctx.createGain()
    ambientGain.gain.value = config.volume * bgmVolume.value

    ambientSource.connect(filter)
    filter.connect(ambientGain)
    ambientGain.connect(ctx.destination)
    ambientSource.start()
  }

  /**
   * 停止BGM — 淡出
   */
  const stopBGM = () => {
    const ctx = getAudioContext()

    if (bgmGain) {
      bgmGain.gain.linearRampToValueAtTime(0, ctx.currentTime + 1)
    }

    setTimeout(() => {
      bgmOscillators.forEach(osc => {
        try { osc.stop() } catch (e) { /* ignore */ }
      })
      bgmOscillators = []
      bgmGain = null
    }, 1200)

    if (ambientSource) {
      try {
        if (ambientGain) {
          ambientGain.gain.linearRampToValueAtTime(0, ctx.currentTime + 1)
        }
        setTimeout(() => {
          try { ambientSource?.stop() } catch (e) { /* ignore */ }
          ambientSource = null
          ambientGain = null
        }, 1200)
      } catch (e) { /* ignore */ }
    }
  }

  /**
   * 播放音效 — 合成音效，无需外部文件
   */
  const playSFX = (name: string) => {
    if (isMuted.value) return

    const ctx = getAudioContext()
    const masterGain = ctx.createGain()
    masterGain.gain.value = sfxVolume.value * 0.3
    masterGain.connect(ctx.destination)

    switch (name) {
      case 'click':
        // 轻柔点击音
        _playTone(ctx, masterGain, 800, 0.08, 'sine', 0.3)
        break

      case 'fragment_found':
        // 碎片发现 — 玻璃碎裂→重组
        _playTone(ctx, masterGain, 1200, 0.15, 'sine', 0.4)
        setTimeout(() => _playTone(ctx, masterGain, 1600, 0.15, 'sine', 0.3), 100)
        setTimeout(() => _playTone(ctx, masterGain, 2000, 0.2, 'sine', 0.5), 200)
        setTimeout(() => _playTone(ctx, masterGain, 2400, 0.3, 'sine', 0.4), 350)
        break

      case 'trust_up':
        // 信任度提升 — 温暖和弦
        _playTone(ctx, masterGain, 523.25, 0.3, 'sine', 0.3)  // C5
        _playTone(ctx, masterGain, 659.25, 0.3, 'sine', 0.25) // E5
        _playTone(ctx, masterGain, 783.99, 0.3, 'sine', 0.2)  // G5
        break

      case 'trust_down':
        // 信任度下降 — 低沉音
        _playTone(ctx, masterGain, 200, 0.4, 'sawtooth', 0.2)
        setTimeout(() => _playTone(ctx, masterGain, 150, 0.5, 'sawtooth', 0.15), 200)
        break

      case 'scene_transition':
        // 场景切换 — 时间流转的呼啸声
        _playSweep(ctx, masterGain, 200, 2000, 1.5)
        break

      case 'typing':
        // 打字机效果 — 轻柔的滴答声
        _playTone(ctx, masterGain, 600 + Math.random() * 200, 0.03, 'square', 0.1)
        break

      case 'ending_hope':
        // 结局·光 — 渐强的和弦
        _playChord(ctx, masterGain, [261.63, 329.63, 392.00, 523.25], 2, 'sine')
        break

      case 'ending_bittersweet':
        // 结局·余温 — 钢琴独奏渐弱
        _playChord(ctx, masterGain, [261.63, 311.13, 392.00], 3, 'triangle')
        break

      case 'ending_tragic':
        // 结局·消散 — 寂静中的单音
        _playTone(ctx, masterGain, 220, 3, 'sine', 0.3)
        break

      case 'dialogue_start':
        // 对话开始
        _playTone(ctx, masterGain, 500, 0.1, 'sine', 0.2)
        setTimeout(() => _playTone(ctx, masterGain, 700, 0.1, 'sine', 0.15), 80)
        break

      case 'explore':
        // 探索热区
        _playSweep(ctx, masterGain, 400, 800, 0.3)
        break
    }
  }

  /**
   * 播放单音
   */
  const _playTone = (
    ctx: AudioContext,
    dest: GainNode,
    freq: number,
    duration: number,
    type: OscillatorType,
    volume: number
  ) => {
    const osc = ctx.createOscillator()
    const gain = ctx.createGain()

    osc.type = type
    osc.frequency.value = freq
    gain.gain.value = volume
    gain.gain.linearRampToValueAtTime(0, ctx.currentTime + duration)

    osc.connect(gain)
    gain.connect(dest)
    osc.start()
    osc.stop(ctx.currentTime + duration)
  }

  /**
   * 播放频率扫描
   */
  const _playSweep = (
    ctx: AudioContext,
    dest: GainNode,
    startFreq: number,
    endFreq: number,
    duration: number
  ) => {
    const osc = ctx.createOscillator()
    const gain = ctx.createGain()

    osc.type = 'sine'
    osc.frequency.value = startFreq
    osc.frequency.linearRampToValueAtTime(endFreq, ctx.currentTime + duration)
    gain.gain.value = 0.2
    gain.gain.linearRampToValueAtTime(0, ctx.currentTime + duration)

    osc.connect(gain)
    gain.connect(dest)
    osc.start()
    osc.stop(ctx.currentTime + duration)
  }

  /**
   * 播放和弦
   */
  const _playChord = (
    ctx: AudioContext,
    dest: GainNode,
    freqs: number[],
    duration: number,
    type: OscillatorType
  ) => {
    freqs.forEach(freq => {
      _playTone(ctx, dest, freq, duration, type, 0.15)
    })
  }

  /**
   * 切换静音
   */
  const toggleMute = () => {
    isMuted.value = !isMuted.value
    if (isMuted.value) {
      stopBGM()
    }
  }

  /**
   * 设置BGM音量
   */
  const setBgmVolume = (v: number) => {
    bgmVolume.value = Math.max(0, Math.min(1, v))
  }

  /**
   * 设置音效音量
   */
  const setSfxVolume = (v: number) => {
    sfxVolume.value = Math.max(0, Math.min(1, v))
  }

  // 清理
  onUnmounted(() => {
    stopBGM()
  })

  return {
    isMuted,
    bgmVolume,
    sfxVolume,
    playBGM,
    stopBGM,
    playSFX,
    toggleMute,
    setBgmVolume,
    setSfxVolume,
  }
}
