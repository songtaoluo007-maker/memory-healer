/* eslint-disable vue/one-component-per-file -- focused component harnesses keep state observable */
import { createApp, defineComponent, h, nextTick, ref } from 'vue'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { AUDIO_STORAGE_KEY, createAudioMixer } from '../audio/mixer'
import VoiceControls from '../components/VoiceControls.vue'
import voiceControlsSource from '../components/VoiceControls.vue?raw'
import type { VoicePlaybackRequest, VoiceResponse } from '../types/game'
import Ending from '../views/Ending.vue'
import endingSource from '../views/Ending.vue?raw'

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

const ruleBodies = (source: string, selector: string) =>
  [...source.matchAll(new RegExp(`\\${selector}\\s*\\{([^}]+)\\}`, 'g'))].map((match) => match[1]!)

const cssBlockBody = (source: string, header: string) => {
  const headerStart = source.indexOf(header)
  const blockStart = source.indexOf('{', headerStart)
  if (headerStart === -1 || blockStart === -1) throw new Error(`Missing CSS block: ${header}`)

  let depth = 0
  for (let index = blockStart; index < source.length; index += 1) {
    if (source[index] === '{') depth += 1
    if (source[index] !== '}') continue
    depth -= 1
    if (depth === 0) return source.slice(blockStart + 1, index)
  }

  throw new Error(`Unclosed CSS block: ${header}`)
}

const remValue = (body: string, property: string) => {
  const match = body.match(new RegExp(`${property}:\\s*([\\d.]+)rem`))
  if (!match) throw new Error(`Missing ${property} rem declaration`)
  return Number(match[1])
}

const hexToRgb = (hex: string) => {
  const value = Number.parseInt(hex.slice(1), 16)
  return [(value >> 16) & 255, (value >> 8) & 255, value & 255] as const
}

const relativeLuminance = (rgb: readonly number[]) => {
  const channels = rgb.map((channel) => {
    const normalized = channel / 255
    return normalized <= 0.04045 ? normalized / 12.92 : ((normalized + 0.055) / 1.055) ** 2.4
  })
  return 0.2126 * channels[0]! + 0.7152 * channels[1]! + 0.0722 * channels[2]!
}

const contrastRatio = (foreground: readonly number[], background: readonly number[]) => {
  const light = Math.max(relativeLuminance(foreground), relativeLuminance(background))
  const dark = Math.min(relativeLuminance(foreground), relativeLuminance(background))
  return (light + 0.05) / (dark + 0.05)
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

  it('keeps the narrow disclosure trigger at least 44px on both axes', () => {
    const narrowTriggerRule = ruleBodies(voiceControlsSource, '.voice-controls-trigger').find(
      (body) => body.includes('min-width'),
    )!

    expect(remValue(narrowTriggerRule, 'width') * 16).toBeGreaterThanOrEqual(44)
    expect(remValue(narrowTriggerRule, 'min-width') * 16).toBeGreaterThanOrEqual(44)
    expect(remValue(narrowTriggerRule, 'min-height') * 16).toBeGreaterThanOrEqual(44)
  })

  it.each([320, 360, 760, 900])(
    'keeps the open panel outside the active portrait safe-zone at %ipx',
    (viewportWidth) => {
      const panelRules = ruleBodies(voiceControlsSource, '.voice-controls-panel')
      const declaredWidths = panelRules
        .map((body) => body.match(/width:\s*([\d.]+)rem/)?.[1])
        .filter((width): width is string => width !== undefined)
        .map(Number)
      const panelLeft = (viewportWidth <= 760 ? 0.75 : 0.85) * 16
      const panelWidth =
        (viewportWidth <= 760 ? Math.min(...declaredWidths) : Math.max(...declaredWidths)) * 16
      const panelRight = panelLeft + panelWidth + 2
      const portraitWidth = Math.min(viewportWidth * 0.68, 24 * 16)
      const portraitLeft = viewportWidth + 3.5 * 16 - portraitWidth

      expect(panelRight).toBeLessThanOrEqual(portraitLeft)
      expect(voiceControlsSource).toContain('@media (max-width: 650px)')
      expect(voiceControlsSource).toMatch(
        /@media \(max-width: 650px\)[\s\S]*?:global\(\.game-cinema \.scene-info\)\s*\{[\s\S]*?display:\s*none/,
      )
    },
  )

  it('keeps muted trigger text above 4.5:1 while retaining its border state', () => {
    const mutedRule = ruleBodies(
      voiceControlsSource,
      '.voice-controls.muted .voice-controls-trigger',
    )[0]!

    expect(mutedRule).toContain('color: var(--paper-300)')
    expect(mutedRule).toContain('border-style: dashed')
    expect(contrastRatio(hexToRgb('#d7c4a2'), hexToRgb('#050606'))).toBeGreaterThanOrEqual(4.5)
  })

  it('allocates separate phone rows to skip/mute and the full-width volume control', () => {
    const phoneVolumeRule = ruleBodies(voiceControlsSource, '.voice-volume').find((body) =>
      body.includes('minmax(0, 1fr)'),
    )!
    const phoneMuteRule = ruleBodies(voiceControlsSource, '.voice-mute-secondary').find((body) =>
      body.includes('grid-row: 3'),
    )!

    expect(phoneMuteRule).toContain('grid-column: 2')
    expect(phoneVolumeRule).toContain('grid-row: 4')
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

  it('keeps the ending heading visual and aria state in sync at the 900x400 narrow boundary', async () => {
    installMatchMedia(true)
    const playback = {
      isSpeaking: ref(false),
      isPaused: ref(false),
      lastRequest: ref<VoicePlaybackRequest | null>(null),
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
    const host = document.createElement('div')
    document.body.append(host)
    const app = createApp(Ending, {
      endingType: 'hope',
      voicePlayback: playback,
    })
    app.mount(host)
    await nextTick()

    host.querySelector<HTMLButtonElement>('[aria-label="展开语音控制"]')!.click()
    await nextTick()

    expect(host.querySelector('.ending')?.classList.contains('voice-controls-open')).toBe(true)
    expect(host.querySelector('.ending-heading')?.getAttribute('aria-hidden')).toBe('true')
    expect(window.matchMedia).toHaveBeenCalledWith('(max-width: 900px), (max-aspect-ratio: 1/1)')
    expect(
      cssBlockBody(endingSource, '@media (max-width: 900px), (max-aspect-ratio: 1/1)'),
    ).toMatch(/\.ending\.voice-controls-open\s+\.ending-heading\s*\{[\s\S]*?visibility:\s*hidden/)
    app.unmount()
  })

  it('keeps the phone story below a four-row top sheet with a 59px safe-area inset', () => {
    const rootRem = 16
    const safeAreaInsetTop = 59
    const panelTop = safeAreaInsetTop + 3.35 * rootRem
    const panelBottom = panelTop + 4 * 2.75 * rootRem + 2
    const storyTop = Math.max(18 * rootRem, safeAreaInsetTop + 15 * rootRem)

    expect(endingSource).toContain(
      '--ending-story-top: max(18rem, calc(env(safe-area-inset-top) + 15rem));',
    )
    expect(endingSource).toMatch(/\.ending-story\s*\{[\s\S]*?top:\s*var\(--ending-story-top\)/)
    expect(panelBottom).toBeLessThan(storyTop)
  })
})
