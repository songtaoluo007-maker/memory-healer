/* eslint-disable vue/one-component-per-file -- focused component harnesses keep state observable */
import { createApp, defineComponent, h, nextTick, ref } from 'vue'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { AUDIO_STORAGE_KEY, createAudioMixer } from '../audio/mixer'
import VoiceControls from '../components/VoiceControls.vue'
import type { VoicePlaybackRequest, VoiceResponse } from '../types/game'
import Ending from '../views/Ending.vue'

const installMatchMedia = (matches: boolean) => {
  vi.stubGlobal(
    'matchMedia',
    vi.fn().mockImplementation((query: string) => ({
      matches,
      media: query,
      onchange: null,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      addListener: vi.fn(),
      removeListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })),
  )
}

const mountVoiceControls = (
  props: {
    isSpeaking?: boolean
    isPaused?: boolean
    voiceVolume?: number
    hasReplay?: boolean
    isMuted?: boolean
  } = {},
  listeners: Record<string, (...args: never[]) => void> = {},
) => {
  const host = document.createElement('div')
  document.body.append(host)
  const app = createApp(VoiceControls, {
    isSpeaking: props.isSpeaking ?? true,
    isPaused: props.isPaused ?? false,
    voiceVolume: props.voiceVolume ?? 0.85,
    hasReplay: props.hasReplay ?? true,
    isMuted: props.isMuted ?? false,
    ...listeners,
  })
  app.mount(host)
  return { app, host }
}

const memoryStorage = () => {
  const values = new Map<string, string>()
  return {
    getItem: (key: string) => values.get(key) ?? null,
    setItem: (key: string, value: string) => values.set(key, value),
  }
}

const replayRequest: VoicePlaybackRequest = {
  url: '/voice/fixed/ending.opus',
  priority: 'ending',
  lineId: 'ending.hope',
  cues: [],
}

const approvedEndingVoice: VoiceResponse = {
  url: '/voice/fixed/ending.opus',
  provider: 'fixed',
  cached: true,
  media_type: 'audio/ogg; codecs=opus',
  duration_ms: 1400,
  line_id: 'ending.hope',
  cues: [],
  degraded: false,
}

describe('VoiceControls', () => {
  afterEach(() => {
    document.body.innerHTML = ''
    vi.unstubAllGlobals()
  })

  it('exposes native pause, replay, skip, voice volume, and global mute controls', () => {
    installMatchMedia(false)
    const { app, host } = mountVoiceControls()

    const pause = host.querySelector<HTMLButtonElement>('[aria-label="暂停对白"]')
    const replay = host.querySelector<HTMLButtonElement>('[aria-label="重播上一句"]')
    const skip = host.querySelector<HTMLButtonElement>('[aria-label="跳过当前对白"]')
    const mute = host.querySelector<HTMLButtonElement>('[aria-label="静音"]')
    const volume = host.querySelector<HTMLInputElement>('[aria-label="对白音量"]')

    expect(pause?.tagName).toBe('BUTTON')
    expect(replay?.tagName).toBe('BUTTON')
    expect(skip?.tagName).toBe('BUTTON')
    expect(mute?.tagName).toBe('BUTTON')
    expect(volume?.type).toBe('range')
    expect(volume?.value).toBe('0.85')
    app.unmount()
  })

  it('keeps native playback buttons keyboard-focusable and changes pause to resume', async () => {
    installMatchMedia(false)
    const isSpeaking = ref(true)
    const isPaused = ref(false)
    const pause = vi.fn(() => {
      isSpeaking.value = false
      isPaused.value = true
    })
    const resume = vi.fn(() => {
      isSpeaking.value = true
      isPaused.value = false
    })
    const host = document.createElement('div')
    document.body.append(host)
    const app = createApp(
      defineComponent({
        setup() {
          return () =>
            h(VoiceControls, {
              isSpeaking: isSpeaking.value,
              isPaused: isPaused.value,
              voiceVolume: 0.85,
              hasReplay: true,
              isMuted: false,
              onPause: pause,
              onResume: resume,
            })
        },
      }),
    )
    app.mount(host)

    const pauseButton = host.querySelector<HTMLButtonElement>('[aria-label="暂停对白"]')!
    pauseButton.focus()
    expect(document.activeElement).toBe(pauseButton)
    expect(pauseButton.tabIndex).toBe(0)
    pauseButton.click()
    await nextTick()

    const resumeButton = host.querySelector<HTMLButtonElement>('[aria-label="继续对白"]')!
    expect(pause).toHaveBeenCalledOnce()
    resumeButton.click()
    await nextTick()
    expect(resume).toHaveBeenCalledOnce()
    expect(host.querySelector('[aria-label="暂停对白"]')).not.toBeNull()
    app.unmount()
  })

  it('disables replay before any line has entered the replay buffer', () => {
    installMatchMedia(false)
    const replay = vi.fn()
    const { app, host } = mountVoiceControls(
      { isSpeaking: false, hasReplay: false },
      { onReplay: replay },
    )

    const replayButton = host.querySelector<HTMLButtonElement>('[aria-label="重播上一句"]')!
    expect(replayButton.disabled).toBe(true)
    replayButton.click()
    expect(replay).not.toHaveBeenCalled()
    app.unmount()
  })

  it('routes voice volume changes through the persisted audio mixer', async () => {
    installMatchMedia(false)
    const storage = memoryStorage()
    const mixer = createAudioMixer({ storage })
    const host = document.createElement('div')
    document.body.append(host)
    const app = createApp(
      defineComponent({
        setup() {
          return () =>
            h(VoiceControls, {
              isSpeaking: false,
              isPaused: false,
              voiceVolume: mixer.voiceVolume.value,
              hasReplay: false,
              isMuted: mixer.isMuted.value,
              'onUpdate:voiceVolume': mixer.setVoiceVolume,
              onToggleMute: mixer.toggleMute,
            })
        },
      }),
    )
    app.mount(host)

    const volume = host.querySelector<HTMLInputElement>('[aria-label="对白音量"]')!
    volume.value = '0.42'
    volume.dispatchEvent(new Event('input', { bubbles: true }))
    await nextTick()

    expect(mixer.voiceVolume.value).toBe(0.42)
    expect(JSON.parse(storage.getItem(AUDIO_STORAGE_KEY)!)).toMatchObject({
      voiceVolume: 0.42,
    })
    app.unmount()
  })

  it('collapses secondary controls behind 声 on narrow screens without losing global mute', async () => {
    installMatchMedia(true)
    const toggleMute = vi.fn()
    const { app, host } = mountVoiceControls({}, { onToggleMute: toggleMute })
    await nextTick()

    const trigger = host.querySelector<HTMLButtonElement>('[aria-label="展开语音控制"]')!
    const panel = host.querySelector<HTMLElement>('[data-voice-controls-panel]')!
    expect(trigger.textContent?.trim()).toBe('声')
    expect(panel.hidden).toBe(true)

    trigger.click()
    await nextTick()
    expect(panel.hidden).toBe(false)
    expect(host.querySelector('[aria-label="收起语音控制"]')).not.toBeNull()

    host.querySelector<HTMLButtonElement>('[aria-label="静音"]')!.click()
    expect(toggleMute).toHaveBeenCalledOnce()
    app.unmount()
  })
})

describe('Ending voice controls', () => {
  afterEach(() => {
    document.body.innerHTML = ''
    vi.unstubAllGlobals()
  })

  it('uses ending priority for an approved line and clears replay before returning home', async () => {
    installMatchMedia(false)
    const playback = {
      isSpeaking: ref(false),
      isPaused: ref(false),
      lastRequest: ref<VoicePlaybackRequest | null>(replayRequest),
      playResponse: vi.fn().mockResolvedValue(true),
      pause: vi.fn(),
      resume: vi.fn().mockResolvedValue(true),
      replay: vi.fn().mockResolvedValue(true),
      skip: vi.fn(),
      stop: vi.fn(),
      waitingForUserGesture: ref(false),
      resumeAfterUserGesture: vi.fn().mockResolvedValue(true),
      activeCue: ref(null),
      currentLineId: ref<string | null>(null),
    }
    const restart = vi.fn()
    const host = document.createElement('div')
    document.body.append(host)
    const app = createApp(Ending, {
      endingType: 'hope',
      endingVoiceResponse: approvedEndingVoice,
      voicePlayback: playback,
      onRestart: restart,
    })
    app.mount(host)
    await nextTick()

    expect(playback.playResponse).toHaveBeenCalledWith(approvedEndingVoice, 'ending')

    const home = [...host.querySelectorAll<HTMLButtonElement>('button')].find((button) =>
      button.textContent?.includes('返回首页'),
    )!
    home.click()

    expect(playback.stop).toHaveBeenCalledOnce()
    expect(playback.lastRequest.value).toBeNull()
    expect(restart).toHaveBeenCalledOnce()
    app.unmount()
  })
})
