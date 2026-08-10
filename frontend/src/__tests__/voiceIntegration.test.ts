/* eslint-disable vue/one-component-per-file -- integration harnesses mount isolated route lifecycles */
import { createApp, defineComponent, h, nextTick, ref } from 'vue'
import { afterEach, describe, expect, it, vi } from 'vitest'
import VoiceSubtitle from '../components/VoiceSubtitle.vue'
import { createSceneVoiceIntegration, useVoiceRouteLifecycle } from '../composables/useScene'
import Ending from '../views/Ending.vue'
import type {
  Hypothesis,
  NpcSummary,
  Scene,
  SceneFragment,
  VoiceCue,
  VoiceResponse,
} from '../types/game'

const fixedResponse = (lineId: string): VoiceResponse => ({
  url: `/voice/fixed/${lineId}.opus`,
  provider: 'fixed',
  cached: true,
  media_type: 'audio/ogg; codecs=opus',
  duration_ms: 1200,
  line_id: lineId,
  cues: [{ start_ms: 0, end_ms: 1200, text: lineId }],
  degraded: false,
})

const scene: Scene = {
  id: 'scene_1972',
  title: '1972',
  description: '老巷',
  mood: 'warm',
  time_period: '1972',
  location: '西安',
  npcs: ['chen_shouyi_young'],
  fragments: ['fragment_grandpa_knife'],
  transition_in_voice_line_id: 'scene_1972.transition_in',
  fallback_asset: '/scene.webp',
}

const chen: NpcSummary = {
  id: 'chen_shouyi_young',
  name: '陈守义',
  title: '皮影匠人',
  avatar: '/chen.webp',
  initial_trust: 50,
  initial_voice_line_id: 'npc.chen_shouyi_young.intro',
}

const knife: SceneFragment = {
  id: 'fragment_grandpa_knife',
  name: '爷爷的刻刀',
  scene: 'scene_1972',
  description: '磨损的刻刀',
  unlock_method: 'explore',
  unlock_hint: '检查工具箱',
  memory_text: '刻刀从不离身。',
  is_revealed: true,
  is_collected: true,
  memory_voice_line_id: 'fragment_grandpa_knife.memory',
}

const shadowStage: SceneFragment = {
  ...knife,
  id: 'fragment_shadow_puppet',
  name: '皮影戏台',
  memory_voice_line_id: 'fragment_shadow_puppet.memory',
}

const threeKings: SceneFragment = {
  ...knife,
  id: 'fragment_three_kings',
  name: '三英战吕布',
  memory_voice_line_id: 'fragment_three_kings.memory',
}

const hypothesis: Hypothesis = {
  id: 'hypothesis_1972_legacy',
  scene_id: 'scene_1972',
  question: '为什么仍想传下去？',
  statement: '刻刀与戏幕共同指向传承。',
  evidence_ids: ['fragment_grandpa_knife', 'fragment_shadow_puppet'],
  resolution: '两条记忆互相印证。',
  resolution_voice_line_id: 'hypothesis_1972_legacy.resolution',
}

const createPlaybackDouble = () => ({
  playResponse: vi.fn().mockResolvedValue(true),
  stop: vi.fn(),
  waitingForUserGesture: ref(false),
  resumeAfterUserGesture: vi.fn().mockResolvedValue(true),
  activeCue: ref<VoiceCue | null>(null),
  currentLineId: ref<string | null>(null),
})

describe('first-act voice boundaries', () => {
  it('plays each canonical 1972 boundary once with its required priority', async () => {
    const playback = createPlaybackDouble()
    const getFixedLine = vi.fn(async (lineId: string) => ({ data: fixedResponse(lineId) }))
    const integration = createSceneVoiceIntegration(playback, getFixedLine)

    await integration.playSceneEntry(scene)
    await integration.playSceneEntry(scene)
    await integration.playNpcIntro(chen)
    await integration.playNpcIntro(chen)
    await integration.playFragmentMemory(knife)
    await integration.playFragmentMemory(knife)
    await integration.playHypothesisResolution(hypothesis)
    await integration.playHypothesisResolution(hypothesis)

    expect(getFixedLine.mock.calls.map(([lineId]) => lineId)).toEqual([
      'scene_1972.transition_in',
      'npc.chen_shouyi_young.intro',
      'fragment_grandpa_knife.memory',
      'hypothesis_1972_legacy.resolution',
    ])
    expect(playback.playResponse.mock.calls.map(([, priority]) => priority)).toEqual([
      'narration',
      'dialogue',
      'narration',
      'critical',
    ])
  })

  it('stops before a scene transition and discards an older fixed-line response', async () => {
    const playback = createPlaybackDouble()
    let resolveLine!: (value: { data: VoiceResponse }) => void
    const getFixedLine = vi.fn(
      () =>
        new Promise<{ data: VoiceResponse }>((resolve) => {
          resolveLine = resolve
        }),
    )
    const integration = createSceneVoiceIntegration(playback, getFixedLine)

    const pending = integration.playSceneEntry(scene)
    integration.stopForSceneTransition()
    resolveLine({ data: fixedResponse('scene_1972.transition_in') })
    await pending

    expect(playback.stop).toHaveBeenCalledOnce()
    expect(playback.playResponse).not.toHaveBeenCalled()
  })

  it('invalidates a pending fixed lookup when dialogue closes', async () => {
    const playback = createPlaybackDouble()
    let resolveLine!: (value: { data: VoiceResponse }) => void
    const getFixedLine = vi.fn(
      () =>
        new Promise<{ data: VoiceResponse }>((resolve) => {
          resolveLine = resolve
        }),
    )
    const integration = createSceneVoiceIntegration(playback, getFixedLine)

    const pending = integration.playNpcIntro(chen)
    integration.cancelPending()
    resolveLine({ data: fixedResponse('npc.chen_shouyi_young.intro') })
    await pending

    expect(playback.stop).toHaveBeenCalledOnce()
    expect(playback.playResponse).not.toHaveBeenCalled()
  })

  it('invalidates a pending fixed lookup when its route unmounts', async () => {
    const playback = createPlaybackDouble()
    let resolveLine!: (value: { data: VoiceResponse }) => void
    const getFixedLine = vi.fn(
      () =>
        new Promise<{ data: VoiceResponse }>((resolve) => {
          resolveLine = resolve
        }),
    )
    const integration = createSceneVoiceIntegration(playback, getFixedLine)
    const app = createApp(
      defineComponent({
        setup() {
          useVoiceRouteLifecycle(playback, integration.cancelPending)
          return () => null
        },
      }),
    )
    const host = document.createElement('div')
    app.mount(host)
    const pending = integration.playNpcIntro(chen)

    app.unmount()
    resolveLine({ data: fixedResponse('npc.chen_shouyi_young.intro') })
    await pending

    expect(playback.playResponse).not.toHaveBeenCalled()
  })

  it('discards an older fixed-line lookup after a newer state boundary wins', async () => {
    const playback = createPlaybackDouble()
    const resolvers = new Map<string, (value: { data: VoiceResponse }) => void>()
    const getFixedLine = vi.fn(
      (lineId: string) =>
        new Promise<{ data: VoiceResponse }>((resolve) => {
          resolvers.set(lineId, resolve)
        }),
    )
    const integration = createSceneVoiceIntegration(playback, getFixedLine)

    const scenePending = integration.playSceneEntry(scene)
    const npcPending = integration.playNpcIntro(chen)
    resolvers.get('npc.chen_shouyi_young.intro')!({
      data: fixedResponse('npc.chen_shouyi_young.intro'),
    })
    await npcPending
    resolvers.get('scene_1972.transition_in')!({
      data: fixedResponse('scene_1972.transition_in'),
    })
    await scenePending

    expect(playback.playResponse).toHaveBeenCalledOnce()
    expect(playback.playResponse).toHaveBeenCalledWith(
      fixedResponse('npc.chen_shouyi_young.intro'),
      'dialogue',
    )
  })

  it('lets the latest authoritative dynamic reply invalidate a delayed NPC intro', async () => {
    const playback = createPlaybackDouble()
    let resolveIntro!: (value: { data: VoiceResponse }) => void
    const getFixedLine = vi.fn(
      () =>
        new Promise<{ data: VoiceResponse }>((resolve) => {
          resolveIntro = resolve
        }),
    )
    const integration = createSceneVoiceIntegration(playback, getFixedLine)
    const introPending = integration.playNpcIntro(chen)

    const dialogueEpoch = integration.beginDialogueVoice()
    await integration.playDialogueResponse(dialogueEpoch, fixedResponse('runtime.dynamic.reply'))
    resolveIntro({ data: fixedResponse('npc.chen_shouyi_young.intro') })
    await introPending

    expect(playback.stop).toHaveBeenCalledOnce()
    expect(playback.playResponse).toHaveBeenCalledOnce()
    expect(playback.playResponse).toHaveBeenCalledWith(
      fixedResponse('runtime.dynamic.reply'),
      'dialogue',
    )
  })

  it.each([shadowStage, threeKings])(
    'gives $id memory authority over the NPC intro for one fragment-and-NPC interaction',
    async (fragment) => {
      const playback = createPlaybackDouble()
      const getFixedLine = vi.fn(async (lineId: string) => ({ data: fixedResponse(lineId) }))
      const integration = createSceneVoiceIntegration(playback, getFixedLine)

      await integration.playInteractionVoice(fragment, chen)

      expect(getFixedLine).toHaveBeenCalledOnce()
      expect(getFixedLine).toHaveBeenCalledWith(fragment.memory_voice_line_id)
      expect(playback.playResponse).toHaveBeenCalledWith(
        fixedResponse(fragment.memory_voice_line_id!),
        'narration',
      )
    },
  )

  it('plays a dialogue-revealed fragment at popup open and deduplicates its line ID', async () => {
    const playback = createPlaybackDouble()
    const getFixedLine = vi.fn(async (lineId: string) => ({ data: fixedResponse(lineId) }))
    const integration = createSceneVoiceIntegration(playback, getFixedLine)

    await integration.playDialogueFragment(threeKings)
    await integration.playDialogueFragment(threeKings)

    expect(getFixedLine).toHaveBeenCalledOnce()
    expect(getFixedLine).toHaveBeenCalledWith('fragment_three_kings.memory')
  })

  it('keeps fixed lookup failures silent and excludes dynamic cues from the overlay', async () => {
    const playback = createPlaybackDouble()
    playback.activeCue.value = { start_ms: 0, end_ms: 1000, text: '动态对白' }
    const getFixedLine = vi.fn().mockRejectedValue(new Error('voice unavailable'))
    const integration = createSceneVoiceIntegration(playback, getFixedLine)

    await expect(integration.playSceneEntry(scene)).resolves.toBe(false)
    expect(integration.subtitleCue.value).toBeNull()

    playback.currentLineId.value = 'scene_1972.transition_in'
    expect(integration.subtitleCue.value?.text).toBe('动态对白')
  })
})

describe('voice route lifecycle', () => {
  afterEach(() => {
    document.body.innerHTML = ''
  })

  it.each(['pointerdown', 'keydown'])(
    'retries a blocked line once after a %s event and removes listeners',
    async (eventName) => {
      const playback = createPlaybackDouble()
      playback.waitingForUserGesture.value = true
      playback.resumeAfterUserGesture.mockImplementation(async () => {
        playback.waitingForUserGesture.value = false
        return true
      })
      const app = createApp(
        defineComponent({
          setup() {
            useVoiceRouteLifecycle(playback)
            return () => null
          },
        }),
      )
      const host = document.createElement('div')
      document.body.append(host)
      app.mount(host)

      window.dispatchEvent(
        eventName === 'keydown' ? new KeyboardEvent(eventName) : new Event(eventName),
      )
      await nextTick()
      window.dispatchEvent(
        eventName === 'keydown' ? new KeyboardEvent(eventName) : new Event(eventName),
      )

      expect(playback.resumeAfterUserGesture).toHaveBeenCalledOnce()
      app.unmount()
      expect(playback.stop).toHaveBeenCalledOnce()
    },
  )

  it('removes gesture listeners after the one retry even when playback stays blocked', async () => {
    const playback = createPlaybackDouble()
    playback.waitingForUserGesture.value = true
    playback.resumeAfterUserGesture.mockResolvedValue(false)
    const app = createApp(
      defineComponent({
        setup() {
          useVoiceRouteLifecycle(playback)
          return () => null
        },
      }),
    )
    const host = document.createElement('div')
    app.mount(host)

    window.dispatchEvent(new Event('pointerdown'))
    await nextTick()
    window.dispatchEvent(new KeyboardEvent('keydown'))

    expect(playback.resumeAfterUserGesture).toHaveBeenCalledOnce()
    app.unmount()
  })

  it('stops the ending route voice queue when Ending unmounts', () => {
    const playback = createPlaybackDouble()
    const app = createApp(Ending, {
      endingType: 'hope',
      voicePlayback: playback,
    })
    const host = document.createElement('div')
    app.mount(host)

    app.unmount()

    expect(playback.stop).toHaveBeenCalledOnce()
  })
})

describe('VoiceSubtitle', () => {
  it('renders one active fixed cue and disappears completely between cues', async () => {
    const cue = ref<VoiceCue | null>({ start_ms: 0, end_ms: 700, text: '记忆正在归来。' })
    const app = createApp(
      defineComponent({
        setup() {
          return () => h(VoiceSubtitle, { cue: cue.value })
        },
      }),
    )
    const host = document.createElement('div')
    app.mount(host)

    expect(host.querySelectorAll('[data-voice-subtitle]')).toHaveLength(1)
    expect(host.textContent).toContain('记忆正在归来。')

    cue.value = null
    await nextTick()
    expect(host.querySelectorAll('[data-voice-subtitle]')).toHaveLength(0)
    app.unmount()
  })
})
