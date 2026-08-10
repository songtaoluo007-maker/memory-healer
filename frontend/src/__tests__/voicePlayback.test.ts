import { createApp, defineComponent } from 'vue'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { VoicePlaybackRequest, VoiceResponse } from '../types/game'

const { mockGetFixedVoiceLine } = vi.hoisted(() => ({
  mockGetFixedVoiceLine: vi.fn(),
}))

vi.mock('../api', () => ({
  getFixedVoiceLine: mockGetFixedVoiceLine,
}))

import { createVoicePlayback } from '../composables/useVoicePlayback'

type FakeAudio = HTMLAudioElement & {
  emit: (event: string) => void
  play: ReturnType<typeof vi.fn>
  pause: ReturnType<typeof vi.fn>
}

const fakeAudio = (): FakeAudio => {
  const listeners = new Map<string, Set<EventListener>>()
  const audio = {
    currentTime: 0,
    pause: vi.fn(),
    play: vi.fn().mockResolvedValue(undefined),
    preload: '',
    src: '',
    addEventListener: vi.fn((event: string, listener: EventListener) => {
      const eventListeners = listeners.get(event) ?? new Set<EventListener>()
      eventListeners.add(listener)
      listeners.set(event, eventListeners)
    }),
    removeEventListener: vi.fn((event: string, listener: EventListener) => {
      listeners.get(event)?.delete(listener)
    }),
    emit(event: string) {
      listeners.get(event)?.forEach((listener) => listener(new Event(event)))
    },
  }

  return audio as unknown as FakeAudio
}

const sequenceAudioFactory = (...audios: FakeAudio[]) => {
  const factory = vi.fn(() => audios.shift())
  return factory as unknown as () => HTMLAudioElement
}

const request = (overrides: Partial<VoicePlaybackRequest> = {}): VoicePlaybackRequest => ({
  url: '/voice/narration.opus',
  priority: 'narration',
  lineId: 'n1',
  cues: [],
  ...overrides,
})

const response = (overrides: Partial<VoiceResponse> = {}): VoiceResponse => ({
  url: '/voice/fixed/line.opus',
  provider: 'fixed',
  cached: true,
  media_type: 'audio/ogg',
  duration_ms: 1000,
  line_id: 'fixed.line',
  cues: [],
  degraded: false,
  ...overrides,
})

describe('voice playback queue', () => {
  beforeEach(() => {
    mockGetFixedVoiceLine.mockReset()
  })

  it('higher priority voice stops lower priority voice', async () => {
    const first = fakeAudio()
    const second = fakeAudio()
    const queue = createVoicePlayback({
      audioFactory: sequenceAudioFactory(first, second),
    })

    await queue.play(request({ priority: 'narration', lineId: 'n1' }))
    await queue.play(request({ url: '/voice/critical.opus', priority: 'critical', lineId: 'c1' }))

    expect(first.pause).toHaveBeenCalledOnce()
    expect(second.play).toHaveBeenCalledOnce()
    expect(queue.currentLineId.value).toBe('c1')
  })

  it('replaces a voice at the same priority', async () => {
    const first = fakeAudio()
    const second = fakeAudio()
    const queue = createVoicePlayback({ audioFactory: sequenceAudioFactory(first, second) })

    await queue.play(request({ priority: 'dialogue' }))
    await queue.play(
      request({ url: '/voice/dialogue-next.opus', priority: 'dialogue', lineId: 'n2' }),
    )

    expect(first.pause).toHaveBeenCalledOnce()
    expect(queue.currentLineId.value).toBe('n2')
  })

  it('rejects a lower-priority voice while a higher-priority voice is active', async () => {
    const active = fakeAudio()
    const ignored = fakeAudio()
    const factory = sequenceAudioFactory(active, ignored)
    const queue = createVoicePlayback({ audioFactory: factory })

    await queue.play(request({ priority: 'critical', lineId: 'critical' }))
    await queue.play(request({ priority: 'narration', lineId: 'narration' }))

    expect(active.pause).not.toHaveBeenCalled()
    expect(factory).toHaveBeenCalledTimes(1)
    expect(queue.currentLineId.value).toBe('critical')
  })

  it('pauses and resumes the active voice', async () => {
    const audio = fakeAudio()
    const queue = createVoicePlayback({ audioFactory: sequenceAudioFactory(audio) })

    await queue.play(request())
    queue.pause()
    await queue.resume()

    expect(audio.pause).toHaveBeenCalledOnce()
    expect(audio.play).toHaveBeenCalledTimes(2)
    expect(queue.isPaused.value).toBe(false)
  })

  it('replays the last voice request after stopping', async () => {
    const first = fakeAudio()
    const second = fakeAudio()
    const queue = createVoicePlayback({ audioFactory: sequenceAudioFactory(first, second) })

    await queue.play(request({ lineId: 'remembered' }))
    queue.stop()
    await queue.replay()

    expect(first.pause).toHaveBeenCalledOnce()
    expect(second.play).toHaveBeenCalledOnce()
    expect(queue.currentLineId.value).toBe('remembered')
  })

  it('cleans up the active voice after a media error', async () => {
    const audio = fakeAudio()
    const queue = createVoicePlayback({ audioFactory: sequenceAudioFactory(audio) })

    await queue.play(request())
    audio.emit('error')

    expect(queue.isSpeaking.value).toBe(false)
    expect(queue.currentLineId.value).toBeNull()
    expect(queue.lastError.value).toBeInstanceOf(Error)
  })

  it('tracks the active phrase cue from time updates', async () => {
    const audio = fakeAudio()
    const queue = createVoicePlayback({ audioFactory: sequenceAudioFactory(audio) })

    await queue.play(
      request({
        cues: [
          { start_ms: 0, end_ms: 500, text: '第一句' },
          { start_ms: 500, end_ms: 1000, text: '第二句' },
        ],
      }),
    )
    audio.currentTime = 0.5
    audio.emit('timeupdate')

    expect(queue.activeCue.value?.text).toBe('第二句')
    audio.currentTime = 1
    audio.emit('timeupdate')
    expect(queue.activeCue.value).toBeNull()
  })

  it('preloads a fixed line once without starting playback', async () => {
    const audio = fakeAudio()
    const queue = createVoicePlayback({ audioFactory: sequenceAudioFactory(audio) })
    mockGetFixedVoiceLine.mockResolvedValue({ data: response() })

    await Promise.all([queue.preloadFixedLine('fixed.line'), queue.preloadFixedLine('fixed.line')])

    expect(mockGetFixedVoiceLine).toHaveBeenCalledTimes(1)
    expect(audio.preload).toBe('auto')
    expect(audio.play).not.toHaveBeenCalled()
  })

  it('does not play silent provider responses', async () => {
    const factory = sequenceAudioFactory(fakeAudio())
    const queue = createVoicePlayback({ audioFactory: factory })

    await queue.playResponse(response({ url: null, provider: 'silent', line_id: null }), 'system')

    expect(factory).not.toHaveBeenCalled()
    expect(queue.isSpeaking.value).toBe(false)
  })

  it('waits for a user gesture after autoplay is blocked and retries once', async () => {
    const audio = fakeAudio()
    const blocked = new DOMException('Gesture required', 'NotAllowedError')
    audio.play.mockRejectedValueOnce(blocked).mockResolvedValueOnce(undefined)
    const queue = createVoicePlayback({ audioFactory: sequenceAudioFactory(audio) })

    await queue.play(request())
    expect(queue.waitingForUserGesture.value).toBe(true)
    expect(queue.currentLineId.value).toBe('n1')

    expect(await queue.resume()).toBe(false)
    expect(audio.play).toHaveBeenCalledOnce()
    expect(queue.waitingForUserGesture.value).toBe(true)

    await queue.resumeAfterUserGesture()
    await queue.resumeAfterUserGesture()

    expect(audio.play).toHaveBeenCalledTimes(2)
    expect(queue.waitingForUserGesture.value).toBe(false)
    expect(queue.isSpeaking.value).toBe(true)
  })

  it('cleans up playback when its component unmounts', async () => {
    const audio = fakeAudio()
    let queue: ReturnType<typeof createVoicePlayback> | undefined
    const app = createApp(
      defineComponent({
        setup() {
          queue = createVoicePlayback({ audioFactory: sequenceAudioFactory(audio) })
          return () => null
        },
      }),
    )
    const host = document.createElement('div')
    app.mount(host)

    await queue!.play(request())
    app.unmount()

    expect(audio.pause).toHaveBeenCalledOnce()
    expect(queue!.isSpeaking.value).toBe(false)
  })
})
