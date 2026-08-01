import { nextTick } from 'vue'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { createAudioMixer } from '../audio/mixer'
import { useSfxBus } from '../composables/useSfxBus'
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

const installFakeAudioContext = () => {
  const gains: Array<{
    gain: { value: number; linearRampToValueAtTime: ReturnType<typeof vi.fn> }
  }> = []

  class FakeAudioContext {
    currentTime = 0
    destination = {}
    state: AudioContextState = 'running'
    createGain() {
      const gain = {
        gain: {
          value: 0,
          cancelScheduledValues: vi.fn(),
          linearRampToValueAtTime: vi.fn((value: number) => {
            gain.gain.value = value
          }),
        },
        connect: vi.fn(),
        disconnect: vi.fn(),
      }
      gains.push(gain)
      return gain as unknown as GainNode
    }
    createOscillator() {
      return {
        type: 'sine',
        frequency: { value: 0, linearRampToValueAtTime: vi.fn() },
        connect: vi.fn(),
        disconnect: vi.fn(),
        start: vi.fn(),
        stop: vi.fn(),
      } as unknown as OscillatorNode
    }
    resume = vi.fn()
  }

  vi.stubGlobal('AudioContext', FakeAudioContext)
  return gains
}

describe('audio mixer', () => {
  afterEach(() => {
    vi.useRealTimers()
    vi.unstubAllGlobals()
  })

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

    mixer.setMusicVolume(Number.NaN)
    expect(mixer.musicVolume.value).toBe(1)
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

  it('updates the active SFX gain when volume changes and mute is enabled', async () => {
    const gains = installFakeAudioContext()
    const mixer = createAudioMixer({ storage: memoryStorage() })
    const sfx = useSfxBus(mixer)

    sfx.playSFX('ending_tragic')
    const outputGain = gains[0]!
    expect(outputGain.gain.value).toBe(0.15)

    mixer.setSfxVolume(0.8)
    await nextTick()
    expect(outputGain.gain.value).toBe(0.24)

    mixer.setMuted(true)
    await nextTick()
    expect(outputGain.gain.value).toBe(0)
  })

  it('keeps music ducked until every active voice playback owner stops', async () => {
    vi.useFakeTimers()
    const mixer = createAudioMixer({ storage: memoryStorage() })
    const first = createVoicePlayback({ audioFactory: () => fakeVoiceAudio(), mixer })
    const second = createVoicePlayback({ audioFactory: () => fakeVoiceAudio(), mixer })

    await first.play(voiceRequest())
    await second.play(voiceRequest())
    first.stop()
    vi.advanceTimersByTime(600)

    expect(mixer.musicDuckDb.value).toBe(-8)
    expect(mixer.ambienceDuckDb.value).toBe(-3)

    second.stop()
    vi.advanceTimersByTime(600)
    expect(mixer.musicDuckDb.value).toBe(0)
    expect(mixer.ambienceDuckDb.value).toBe(0)
  })
})
