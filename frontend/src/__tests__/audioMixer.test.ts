import { afterEach, describe, expect, it, vi } from 'vitest'
import { createAudioMixer } from '../audio/mixer'
import { createVoicePlayback } from '../composables/useVoicePlayback'
import type { VoicePlaybackRequest } from '../types/game'

const memoryStorage = (initial: Record<string, string> = {}) => {
  const values = new Map(Object.entries(initial))
  return {
    getItem: (key: string) => values.get(key) ?? null,
    setItem: (key: string, value: string) => values.set(key, value),
  }
}

const voiceRequest = (): VoicePlaybackRequest => ({
  url: '/voice/narration.opus',
  priority: 'narration',
  lineId: 'n1',
  cues: [],
})

const fakeVoiceAudio = () => {
  const listeners = new Map<string, Set<EventListener>>()
  return {
    currentTime: 0,
    pause: vi.fn(),
    play: vi.fn().mockResolvedValue(undefined),
    preload: '',
    src: '',
    volume: 1,
    addEventListener: vi.fn((event: string, listener: EventListener) => {
      const eventListeners = listeners.get(event) ?? new Set<EventListener>()
      eventListeners.add(listener)
      listeners.set(event, eventListeners)
    }),
    emit(event: string) {
      listeners.get(event)?.forEach((listener) => listener(new Event(event)))
    },
  } as unknown as HTMLAudioElement & { emit(event: string): void }
}

describe('audio mixer', () => {
  afterEach(() => vi.useRealTimers())

  it('ducks music by eight decibels while preserving ambience at minus three', () => {
    const mixer = createAudioMixer({ storage: memoryStorage() })

    mixer.setVoiceDucking(true)

    expect(mixer.musicDuckDb.value).toBe(-8)
    expect(mixer.ambienceDuckDb.value).toBe(-3)
  })

  it('restores music after six hundred milliseconds', () => {
    vi.useFakeTimers()
    const mixer = createAudioMixer({ storage: memoryStorage() })
    mixer.setVoiceDucking(true)
    mixer.setVoiceDucking(false)

    vi.advanceTimersByTime(599)
    expect(mixer.musicDuckDb.value).toBe(-8)
    vi.advanceTimersByTime(1)
    expect(mixer.musicDuckDb.value).toBe(0)
    expect(mixer.ambienceDuckDb.value).toBe(0)
  })

  it('clamps and persists independent music, effects, and voice volumes', () => {
    const storage = memoryStorage()
    const mixer = createAudioMixer({ storage })

    mixer.setMusicVolume(2)
    mixer.setSfxVolume(-1)
    mixer.setVoiceVolume(0.6)

    expect(mixer.musicVolume.value).toBe(1)
    expect(mixer.sfxVolume.value).toBe(0)
    expect(mixer.voiceVolume.value).toBe(0.6)
    expect(JSON.parse(storage.getItem('memory-healer.audio.v2')!)).toEqual({
      muted: false,
      musicVolume: 1,
      sfxVolume: 0,
      voiceVolume: 0.6,
    })
  })

  it('uses defaults when stored preferences are invalid', () => {
    const mixer = createAudioMixer({
      storage: memoryStorage({
        'memory-healer.audio.v2': '{not json',
      }),
    })

    expect(mixer.isMuted.value).toBe(false)
    expect(mixer.musicVolume.value).toBe(0.35)
    expect(mixer.sfxVolume.value).toBe(0.5)
    expect(mixer.voiceVolume.value).toBe(0.85)
  })

  it('normalizes invalid stored fields before using them', () => {
    const mixer = createAudioMixer({
      storage: memoryStorage({
        'memory-healer.audio.v2': JSON.stringify({
          muted: 'yes',
          musicVolume: Number.NaN,
          sfxVolume: 3,
          voiceVolume: null,
        }),
      }),
    })

    expect(mixer.isMuted.value).toBe(false)
    expect(mixer.musicVolume.value).toBe(0.35)
    expect(mixer.sfxVolume.value).toBe(1)
    expect(mixer.voiceVolume.value).toBe(0.85)
  })

  it('fully mutes every bus without overwriting saved volume preferences', () => {
    const mixer = createAudioMixer({ storage: memoryStorage() })
    mixer.setMusicVolume(0.2)
    mixer.setSfxVolume(0.4)
    mixer.setVoiceVolume(0.7)

    mixer.setMuted(true)

    expect(mixer.isMuted.value).toBe(true)
    expect(mixer.effectiveMusicVolume.value).toBe(0)
    expect(mixer.effectiveSfxVolume.value).toBe(0)
    expect(mixer.effectiveVoiceVolume.value).toBe(0)
    expect(mixer.musicVolume.value).toBe(0.2)
    expect(mixer.sfxVolume.value).toBe(0.4)
    expect(mixer.voiceVolume.value).toBe(0.7)
  })

  it('applies voice volume and releases music ducking when playback ends', async () => {
    vi.useFakeTimers()
    const audio = fakeVoiceAudio()
    const mixer = createAudioMixer({ storage: memoryStorage() })
    mixer.setVoiceVolume(0.6)
    const voice = createVoicePlayback({ audioFactory: () => audio, mixer })

    await voice.play(voiceRequest())

    expect(audio.volume).toBe(0.6)
    expect(mixer.musicDuckDb.value).toBe(-8)

    audio.emit('ended')
    vi.advanceTimersByTime(600)
    expect(mixer.musicDuckDb.value).toBe(0)
  })
})
