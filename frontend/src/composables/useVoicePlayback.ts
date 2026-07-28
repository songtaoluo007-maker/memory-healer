import { getCurrentInstance, onUnmounted, ref, watch } from 'vue'
import { getFixedVoiceLine, requestNpcVoice } from '../api'
import { type AudioMixer, useAudioMixer } from '../audio/mixer'
import type { VoiceCue, VoicePlaybackRequest, VoicePriority, VoiceResponse } from '../types/game'

const priorityRank: Record<VoicePriority, number> = {
  system: 1,
  narration: 2,
  dialogue: 3,
  critical: 4,
  ending: 5,
}

type AudioFactory = (url: string) => HTMLAudioElement

interface VoicePlaybackOptions {
  audioFactory?: AudioFactory
  mixer?: AudioMixer
}

const defaultAudioFactory: AudioFactory = (url) => new Audio(url)

const errorFrom = (error: unknown, fallback: string) => {
  if (error instanceof Error) return error
  const normalized = new Error(fallback)
  if (typeof error === 'object' && error !== null && 'name' in error) {
    normalized.name = String(error.name)
  }
  return normalized
}

export function createVoicePlayback(options: VoicePlaybackOptions = {}) {
  const audioFactory = options.audioFactory ?? defaultAudioFactory
  const mixer = options.mixer ?? useAudioMixer()
  const isSpeaking = ref(false)
  const isPaused = ref(false)
  const currentLineId = ref<string | null>(null)
  const activeCue = ref<VoiceCue | null>(null)
  const waitingForUserGesture = ref(false)
  const lastRequest = ref<VoicePlaybackRequest | null>(null)
  const lastError = ref<Error | null>(null)
  const fixedLinePreloads = new Map<string, Promise<VoiceResponse>>()

  let currentAudio: HTMLAudioElement | null = null
  let currentPriority: VoicePriority | null = null
  let gestureRetryConsumed = false

  const applyVoiceVolume = (audio: HTMLAudioElement) => {
    audio.volume = mixer.effectiveVoiceVolume.value
  }

  const clearCurrent = (preserveLastRequest = true) => {
    const audio = currentAudio
    currentAudio = null
    currentPriority = null
    isSpeaking.value = false
    isPaused.value = false
    currentLineId.value = null
    activeCue.value = null
    waitingForUserGesture.value = false
    mixer.setVoiceDucking(false)
    if (!preserveLastRequest) lastRequest.value = null

    if (audio) {
      audio.pause()
      audio.src = ''
    }
  }

  const updateActiveCue = (audio: HTMLAudioElement, cues: VoiceCue[]) => {
    if (audio !== currentAudio) return
    const positionMs = audio.currentTime * 1000
    activeCue.value =
      cues.find((cue) => cue.start_ms <= positionMs && positionMs < cue.end_ms) ?? null
  }

  const startAudio = async (audio: HTMLAudioElement): Promise<boolean> => {
    applyVoiceVolume(audio)
    try {
      await audio.play()
      if (audio !== currentAudio) return false
      isSpeaking.value = true
      isPaused.value = false
      waitingForUserGesture.value = false
      lastError.value = null
      mixer.setVoiceDucking(true)
      return true
    } catch (error) {
      if (audio !== currentAudio) return false
      const audioError = errorFrom(error, 'Voice playback failed')
      lastError.value = audioError
      if (audioError.name === 'NotAllowedError') {
        isSpeaking.value = false
        isPaused.value = false
        waitingForUserGesture.value = true
        return false
      }
      clearCurrent()
      lastError.value = audioError
      return false
    }
  }

  const play = async (request: VoicePlaybackRequest): Promise<boolean> => {
    if (
      currentAudio &&
      currentPriority !== null &&
      priorityRank[request.priority] < priorityRank[currentPriority]
    ) {
      return false
    }

    if (currentAudio) clearCurrent()

    const audio = audioFactory(request.url)
    audio.src = request.url
    applyVoiceVolume(audio)
    currentAudio = audio
    currentPriority = request.priority
    currentLineId.value = request.lineId
    lastRequest.value = request
    lastError.value = null
    isSpeaking.value = true
    isPaused.value = false
    waitingForUserGesture.value = false
    gestureRetryConsumed = false

    audio.addEventListener('timeupdate', () => updateActiveCue(audio, request.cues))
    audio.addEventListener('ended', () => {
      if (audio === currentAudio) clearCurrent()
    })
    audio.addEventListener('error', () => {
      if (audio === currentAudio) {
        lastError.value = new Error('Voice media failed to load')
        clearCurrent()
      }
    })

    return startAudio(audio)
  }

  const playResponse = (response: VoiceResponse, priority: VoicePriority) => {
    if (!response.url) return Promise.resolve(false)
    return play({
      url: response.url,
      priority,
      lineId: response.line_id,
      cues: response.cues,
    })
  }

  const preloadFixedLine = (lineId: string) => {
    const existing = fixedLinePreloads.get(lineId)
    if (existing) return existing

    const preload = getFixedVoiceLine(lineId)
      .then(({ data }) => {
        if (data.url) {
          const audio = audioFactory(data.url)
          audio.src = data.url
          audio.preload = 'auto'
          applyVoiceVolume(audio)
        }
        return data
      })
      .catch((error: unknown) => {
        fixedLinePreloads.delete(lineId)
        throw error
      })
    fixedLinePreloads.set(lineId, preload)
    return preload
  }

  const stop = () => {
    gestureRetryConsumed = false
    clearCurrent()
  }

  const pause = () => {
    if (!currentAudio) return
    currentAudio.pause()
    isSpeaking.value = false
    isPaused.value = true
  }

  const resume = async () => {
    if (!currentAudio || !isPaused.value || waitingForUserGesture.value) return false
    return startAudio(currentAudio)
  }

  const replay = async () => {
    if (!lastRequest.value) return false
    return play(lastRequest.value)
  }

  const resumeAfterUserGesture = async () => {
    if (!waitingForUserGesture.value || gestureRetryConsumed || !currentAudio) return false
    gestureRetryConsumed = true
    return startAudio(currentAudio)
  }

  const speak = async (text: string, npcId: string) => {
    try {
      const response = await requestNpcVoice(text, npcId, 'neutral', 0.5)
      return playResponse(response.data, 'dialogue')
    } catch {
      return false
    }
  }

  watch(mixer.effectiveVoiceVolume, (volume) => {
    if (currentAudio) currentAudio.volume = volume
  })

  if (getCurrentInstance()) onUnmounted(stop)

  return {
    isSpeaking,
    isPaused,
    currentLineId,
    activeCue,
    waitingForUserGesture,
    lastRequest,
    lastError,
    play,
    playResponse,
    preloadFixedLine,
    stop,
    stopSpeak: stop,
    skip: stop,
    pause,
    resume,
    replay,
    resumeAfterUserGesture,
    speak,
  }
}

export function useVoicePlayback() {
  return createVoicePlayback()
}
