import { computed, ref } from 'vue'
import type { ComputedRef, Ref } from 'vue'

export const AUDIO_STORAGE_KEY = 'memory-healer.audio.v2'

export interface AudioPreferences {
  muted: boolean
  musicVolume: number
  sfxVolume: number
  voiceVolume: number
}

export interface AudioStorage {
  getItem(key: string): string | null
  setItem(key: string, value: string): void
}

export type VoiceDuckingOwner = symbol

export interface AudioMixer {
  isMuted: Ref<boolean>
  musicVolume: Ref<number>
  sfxVolume: Ref<number>
  voiceVolume: Ref<number>
  bgmVolume: Ref<number>
  effectiveMusicVolume: ComputedRef<number>
  effectiveSfxVolume: ComputedRef<number>
  effectiveVoiceVolume: ComputedRef<number>
  musicDuckDb: Ref<number>
  ambienceDuckDb: Ref<number>
  setMuted(muted: boolean): void
  toggleMute(): void
  setMusicVolume(volume: number): void
  setBgmVolume(volume: number): void
  setSfxVolume(volume: number): void
  setVoiceVolume(volume: number): void
  setVoiceDucking(active: boolean, owner?: VoiceDuckingOwner): void
}

interface AudioMixerOptions {
  storage?: AudioStorage | null
}

const defaults: AudioPreferences = {
  muted: false,
  musicVolume: 0.35,
  sfxVolume: 0.5,
  voiceVolume: 0.85,
}

const clamp = (value: number) => Math.max(0, Math.min(1, value))

const validNumber = (value: unknown, fallback: number) =>
  typeof value === 'number' && Number.isFinite(value) ? clamp(value) : fallback

const loadPreferences = (storage: AudioStorage | null | undefined): AudioPreferences => {
  if (!storage) return { ...defaults }

  try {
    const raw = storage.getItem(AUDIO_STORAGE_KEY)
    if (!raw) return { ...defaults }
    const parsed: unknown = JSON.parse(raw)
    if (typeof parsed !== 'object' || parsed === null || Array.isArray(parsed))
      return { ...defaults }
    const value = parsed as Partial<AudioPreferences>
    return {
      muted: typeof value.muted === 'boolean' ? value.muted : defaults.muted,
      musicVolume: validNumber(value.musicVolume, defaults.musicVolume),
      sfxVolume: validNumber(value.sfxVolume, defaults.sfxVolume),
      voiceVolume: validNumber(value.voiceVolume, defaults.voiceVolume),
    }
  } catch {
    return { ...defaults }
  }
}

const browserStorage = (): AudioStorage | null => {
  if (typeof window === 'undefined') return null
  try {
    return window.localStorage
  } catch {
    return null
  }
}

export function createAudioMixer(options: AudioMixerOptions = {}): AudioMixer {
  const storage = options.storage === undefined ? browserStorage() : options.storage
  const preferences = loadPreferences(storage)
  const isMuted = ref(preferences.muted)
  const musicVolume = ref(preferences.musicVolume)
  const sfxVolume = ref(preferences.sfxVolume)
  const voiceVolume = ref(preferences.voiceVolume)
  const musicDuckDb = ref(0)
  const ambienceDuckDb = ref(0)
  let restoreDuckingTimer: ReturnType<typeof setTimeout> | null = null
  const duckingOwners = new Set<VoiceDuckingOwner>()
  const defaultDuckingOwner = Symbol('default-voice-duck')

  const persist = () => {
    if (!storage) return
    try {
      storage.setItem(
        AUDIO_STORAGE_KEY,
        JSON.stringify({
          muted: isMuted.value,
          musicVolume: musicVolume.value,
          sfxVolume: sfxVolume.value,
          voiceVolume: voiceVolume.value,
        }),
      )
    } catch {
      // Preferences are optional when storage is unavailable or full.
    }
  }

  const clearRestoreTimer = () => {
    if (restoreDuckingTimer === null) return
    clearTimeout(restoreDuckingTimer)
    restoreDuckingTimer = null
  }

  const setMuted = (muted: boolean) => {
    isMuted.value = muted
    persist()
  }

  const setVolume = (target: Ref<number>, volume: number) => {
    if (!Number.isFinite(volume)) return
    target.value = clamp(volume)
    persist()
  }

  const setVoiceDucking = (active: boolean, owner = defaultDuckingOwner) => {
    clearRestoreTimer()
    if (active) {
      duckingOwners.add(owner)
      musicDuckDb.value = -8
      ambienceDuckDb.value = -3
      return
    }

    duckingOwners.delete(owner)
    if (duckingOwners.size > 0) return

    restoreDuckingTimer = setTimeout(() => {
      musicDuckDb.value = 0
      ambienceDuckDb.value = 0
      restoreDuckingTimer = null
    }, 600)
  }

  return {
    isMuted,
    musicVolume,
    sfxVolume,
    voiceVolume,
    bgmVolume: musicVolume,
    effectiveMusicVolume: computed(() => (isMuted.value ? 0 : musicVolume.value)),
    effectiveSfxVolume: computed(() => (isMuted.value ? 0 : sfxVolume.value)),
    effectiveVoiceVolume: computed(() => (isMuted.value ? 0 : voiceVolume.value)),
    musicDuckDb,
    ambienceDuckDb,
    setMuted,
    toggleMute: () => setMuted(!isMuted.value),
    setMusicVolume: (volume) => setVolume(musicVolume, volume),
    setBgmVolume: (volume) => setVolume(musicVolume, volume),
    setSfxVolume: (volume) => setVolume(sfxVolume, volume),
    setVoiceVolume: (volume) => setVolume(voiceVolume, volume),
    setVoiceDucking,
  }
}

let sharedMixer: AudioMixer | null = null

export function useAudioMixer(): AudioMixer {
  sharedMixer ??= createAudioMixer()
  return sharedMixer
}
