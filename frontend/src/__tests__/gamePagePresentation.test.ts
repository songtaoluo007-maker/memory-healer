import { createApp, defineComponent, h, nextTick, ref } from 'vue'
import { createPinia } from 'pinia'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import type { AppliedConsequence, Fragment, GameState, SceneView } from '../types/game'

const apiMocks = vi.hoisted(() => ({
  chatWithNpc: vi.fn(),
  confirmHypothesis: vi.fn(),
  evaluateEnding: vi.fn(),
  exploreHotspot: vi.fn(),
  getFixedVoiceLine: vi.fn(),
  getNewGame: vi.fn(),
  getSceneView: vi.fn(),
  listSaves: vi.fn(),
  loadGame: vi.fn(),
  recordChoice: vi.fn(),
  requestNpcVoice: vi.fn(),
  saveGame: vi.fn(),
}))

vi.mock('../api', () => apiMocks)
vi.mock('../composables/useMusicBus', () => ({ useMusicBus: () => ({ playBGM: vi.fn() }) }))
vi.mock('../composables/useSfxBus', () => ({ useSfxBus: () => ({ playSFX: vi.fn() }) }))
vi.mock('../composables/useVoicePlayback', () => ({
  useVoicePlayback: () => ({
    activeCue: ref(null),
    currentLineId: ref(null),
    isPaused: ref(false),
    isSpeaking: ref(false),
    lastRequest: ref(null),
    pause: vi.fn(),
    playResponse: vi.fn(),
    replay: vi.fn(),
    resume: vi.fn(),
    resumeAfterUserGesture: vi.fn(),
    skip: vi.fn(),
    stop: vi.fn(),
    waitingForUserGesture: ref(false),
  }),
}))
vi.mock('../components/CinematicStage.vue', () => ({
  __esModule: true,
  default: defineComponent({
    props: {
      activeNpcId: { type: String, default: null },
      consequence: { type: Object, default: null },
      sceneId: { type: String, required: true },
    },
    setup(props, { slots }) {
      return () =>
        h(
          'div',
          {
            class: 'cinematic-stage-mock',
            'data-consequence-variant': (props.consequence as AppliedConsequence | null)?.variant,
            'data-scene-id': props.sceneId,
          },
          slots.default?.(),
        )
    },
  }),
}))
vi.mock('../components/SceneIllustration.vue', () => ({
  __esModule: true,
  default: defineComponent({ setup: () => () => h('div') }),
}))

import Game from '../views/Game.vue'
import { useGameState } from '../composables/useGameState'

const makeState = (overrides: Partial<GameState> = {}): GameState => ({
  schema_version: 1,
  game_id: '00000000-0000-0000-0000-000000000004',
  revision: 4,
  current_scene: 'scene_1990',
  visited_scenes: ['scene_1990'],
  collected_fragments: [],
  revealed_fragments: [],
  fragment_states: {
    station_clock_fragment: {
      id: 'station_clock_fragment',
      name: '站台时钟',
      status: 'hidden',
      collected: false,
      revealed: false,
      scene: 'scene_1990',
    },
    train_ticket_fragment: {
      id: 'train_ticket_fragment',
      name: '南下车票',
      status: 'hidden',
      collected: false,
      revealed: false,
      scene: 'scene_1990',
    },
  },
  npc_trust: { chen_shouyi_1990: 20 },
  npc_emotions: { chen_shouyi_1990: 'guarded' },
  key_choices: [],
  butterfly_choices: {},
  dialogue_history: [],
  current_mood: 'guarded',
  play_time_seconds: 0,
  started_at: '2026-08-01T12:00:00Z',
  chapter: 1,
  ending: null,
  ...overrides,
})

const makeScene = (): SceneView => ({
  scene: {
    id: 'scene_1990',
    title: '南站月台',
    description: '雨水敲着站台。',
    mood: 'guarded',
    time_period: '1990',
    location: '南站',
    npcs: ['chen_shouyi_1990'],
    fragments: ['station_clock_fragment', 'train_ticket_fragment'],
    fallback_asset: '',
  },
  npcs: [
    {
      id: 'chen_shouyi_1990',
      name: '陈守义',
      title: '年轻的皮影匠人',
      avatar: '',
      initial_trust: 20,
    },
  ],
  fragments: [
    {
      id: 'station_clock_fragment',
      name: '站台时钟',
      scene: 'scene_1990',
      description: '时针停在发车前。',
      unlock_method: 'trust',
      unlock_hint: '信任达到“初识”后再查看',
      memory_text: '',
      unlock_npc_id: 'chen_shouyi_1990',
      minimum_trust: 35,
      is_revealed: false,
      is_collected: false,
    },
    {
      id: 'train_ticket_fragment',
      name: '南下车票',
      scene: 'scene_1990',
      description: '一张揉皱的车票。',
      unlock_method: 'dialogue',
      unlock_hint: '问问陈守义。',
      memory_text: '',
      unlock_npc_id: 'chen_shouyi_1990',
      dialogue_prompt: '那张南下的车票，是谁替你买的？',
      is_revealed: false,
      is_collected: false,
    },
  ],
  hotspots: [
    {
      id: 'station-clock-hotspot',
      scene_id: 'scene_1990',
      label: '停摆的站台时钟',
      x: 0.5,
      y: 0.5,
      radius: 0.1,
      fragment_id: 'station_clock_fragment',
      npc_id: null,
      interaction: 'inspect',
      presentation_event: 'fragment.locked',
    },
  ],
  choices: [],
  hypotheses: [],
  applied_consequences: [],
  content_version: 1,
})

const makeConsequence = (variant: 'legacy_carried' | 'legacy_suppressed'): AppliedConsequence => ({
  id: `consequence_1972_${variant}`,
  source_choice_id: variant === 'legacy_carried' ? 'encourage_art' : 'discourage_art',
  target_scene_id: 'scene_1990',
  variant,
  scene_text:
    variant === 'legacy_carried'
      ? '旧木箱在脚边敞开着，现代皮影清楚可见。'
      : '旧木箱半合着，现代皮影被压在传统人偶下面。',
  npc_context: {},
})

const flushUi = async () => {
  await Promise.resolve()
  await nextTick()
  await Promise.resolve()
  await nextTick()
}

describe('game page evidence task presentation', () => {
  let app: ReturnType<typeof createApp> | null = null
  let host: HTMLDivElement | null = null

  beforeEach(() => {
    vi.clearAllMocks()
    useGameState().gameState.value = null
    const state = makeState()
    const scene = makeScene()
    apiMocks.getNewGame.mockResolvedValue({
      data: { state, scene_view: scene, content_version: 1 },
    })
  })

  afterEach(() => {
    app?.unmount()
    host?.remove()
    app = null
    host = null
  })

  it('presents the carried 1972 consequence in the 1990 stage and opening narration', async () => {
    const scene = makeScene()
    scene.applied_consequences = [makeConsequence('legacy_carried')]
    apiMocks.getNewGame.mockResolvedValue({
      data: { state: makeState(), scene_view: scene, content_version: 1 },
    })

    app = createApp(Game)
    app.use(createPinia())
    host = document.createElement('div')
    document.body.append(host)
    app.mount(host)
    await flushUi()
    await vi.dynamicImportSettled()
    await flushUi()

    expect(
      host.querySelector('.cinematic-stage-mock')?.getAttribute('data-consequence-variant'),
    ).toBe('legacy_carried')
    const echo = host.querySelector<HTMLElement>('.causal-echo')
    expect(echo?.getAttribute('aria-label')).toBe('因果回声')
    expect(echo?.textContent).toContain('旧木箱在脚边敞开着，现代皮影清楚可见。')

    host.querySelector<HTMLElement>('.narrative-text')?.click()
    await flushUi()
    expect(host.querySelector('.narrative-text')?.textContent).toContain('雨水敲着站台。')
    expect(host.querySelector('.narrative-text')?.textContent).toContain(
      '旧木箱在脚边敞开着，现代皮影清楚可见。',
    )
  })

  it('presents the suppressed consequence without leaking carried-branch copy', async () => {
    const scene = makeScene()
    scene.applied_consequences = [makeConsequence('legacy_suppressed')]
    apiMocks.getNewGame.mockResolvedValue({
      data: { state: makeState(), scene_view: scene, content_version: 1 },
    })

    app = createApp(Game)
    app.use(createPinia())
    host = document.createElement('div')
    document.body.append(host)
    app.mount(host)
    await flushUi()
    await vi.dynamicImportSettled()
    await flushUi()

    expect(
      host.querySelector('.cinematic-stage-mock')?.getAttribute('data-consequence-variant'),
    ).toBe('legacy_suppressed')
    expect(host.querySelector('.causal-echo')?.textContent).toContain(
      '旧木箱半合着，现代皮影被压在传统人偶下面。',
    )
    expect(host.textContent).not.toContain('现代皮影清楚可见')

    host.querySelector<HTMLElement>('.narrative-text')?.click()
    await flushUi()
    expect(host.querySelector('.narrative-text')?.textContent).toContain(
      '旧木箱半合着，现代皮影被压在传统人偶下面。',
    )
  })

  it('ignores a consequence that does not target the active scene', async () => {
    const scene = makeScene()
    scene.applied_consequences = [
      {
        ...makeConsequence('legacy_carried'),
        target_scene_id: 'scene_2050',
        scene_text: '不应进入当前场景的未来回声。',
      },
    ]
    apiMocks.getNewGame.mockResolvedValue({
      data: { state: makeState(), scene_view: scene, content_version: 1 },
    })

    app = createApp(Game)
    app.use(createPinia())
    host = document.createElement('div')
    document.body.append(host)
    app.mount(host)
    await flushUi()
    await vi.dynamicImportSettled()
    await flushUi()

    expect(
      host.querySelector('.cinematic-stage-mock')?.getAttribute('data-consequence-variant'),
    ).toBeNull()
    expect(host.querySelector('.causal-echo')).toBeNull()
    expect(host.textContent).not.toContain('不应进入当前场景的未来回声')

    host.querySelector<HTMLElement>('.narrative-text')?.click()
    await flushUi()
    expect(host.querySelector('.narrative-text')?.textContent).toContain('雨水敲着站台。')
  })

  it('leaves the full base page unchanged for an unsupported consequence variant', async () => {
    const scene = makeScene()
    scene.applied_consequences = [
      {
        ...makeConsequence('legacy_carried'),
        variant: 'future_variant',
        scene_text: '未知后果不应进入当前页面。',
      },
    ]
    apiMocks.getNewGame.mockResolvedValue({
      data: { state: makeState(), scene_view: scene, content_version: 1 },
    })

    app = createApp(Game)
    app.use(createPinia())
    host = document.createElement('div')
    document.body.append(host)
    app.mount(host)
    await flushUi()
    await vi.dynamicImportSettled()
    await flushUi()

    expect(
      host.querySelector('.cinematic-stage-mock')?.getAttribute('data-consequence-variant'),
    ).toBeNull()
    expect(host.querySelector('.causal-echo')).toBeNull()
    expect(host.textContent).not.toContain('未知后果不应进入当前页面。')

    host.querySelector<HTMLElement>('.narrative-text')?.click()
    await flushUi()
    expect(host.querySelector('.narrative-text')?.textContent).toContain('雨水敲着站台。')
    expect(host.querySelector('.narrative-text')?.textContent).not.toContain(
      '未知后果不应进入当前页面。',
    )
  })

  it('leaves the full base page unchanged when no consequence is present', async () => {
    const scene = makeScene()
    scene.applied_consequences = []
    apiMocks.getNewGame.mockResolvedValue({
      data: { state: makeState(), scene_view: scene, content_version: 1 },
    })

    app = createApp(Game)
    app.use(createPinia())
    host = document.createElement('div')
    document.body.append(host)
    app.mount(host)
    await flushUi()
    await vi.dynamicImportSettled()
    await flushUi()

    expect(
      host.querySelector('.cinematic-stage-mock')?.getAttribute('data-consequence-variant'),
    ).toBeNull()
    expect(host.querySelector('.causal-echo')).toBeNull()

    host.querySelector<HTMLElement>('.narrative-text')?.click()
    await flushUi()
    expect(host.querySelector('.narrative-text')?.textContent).toContain('雨水敲着站台。')
  })

  it('keeps a trust-locked hotspot available while showing its canonical hint and NPC task', async () => {
    const state = makeState()
    apiMocks.exploreHotspot.mockResolvedValue({
      data: {
        state,
        events: [
          {
            type: 'fragment.locked',
            content_id: 'station_clock_fragment',
            payload: {
              method: 'trust',
              hint: '信任达到“初识”后再查看',
              npc_id: 'chen_shouyi_1990',
              minimum_trust: 35,
            },
          },
        ],
      },
    })
    app = createApp(Game)
    app.use(createPinia())
    host = document.createElement('div')
    document.body.append(host)
    app.mount(host)
    await flushUi()
    await vi.dynamicImportSettled()
    await flushUi()

    const hotspot = host.querySelector<HTMLButtonElement>('.perception-cue')!
    hotspot.click()
    await flushUi()

    expect(useGameState().gameState.value?.revision).toBe(4)
    expect(host.querySelector<HTMLButtonElement>('.perception-cue')?.disabled).toBe(false)
    expect(host.textContent).toContain('陈守义')
    const status = host.querySelector<HTMLElement>('[role="status"]')?.textContent
    expect(status).toContain('信任达到“初识”后再查看')
    expect(status).toContain('当前 20 / 需要 35')
  })

  it('opens the payload NPC task for a locked dialogue hotspot without marking it explored', async () => {
    const state = makeState()
    const scene = makeScene()
    scene.npcs.push({
      id: 'stranger_1990',
      name: '陌生人',
      title: '候车旅客',
      avatar: '',
      initial_trust: 40,
    })
    apiMocks.getNewGame.mockResolvedValue({
      data: { state, scene_view: scene, content_version: 1 },
    })
    apiMocks.exploreHotspot.mockResolvedValue({
      data: {
        state,
        events: [
          {
            type: 'fragment.locked',
            content_id: 'train_ticket_fragment',
            payload: {
              method: 'dialogue',
              hint: '先问问候车的陌生人。',
              npc_id: 'stranger_1990',
              prompt: '你见过这张车票吗？',
            },
          },
        ],
      },
    })
    app = createApp(Game)
    app.use(createPinia())
    host = document.createElement('div')
    document.body.append(host)
    app.mount(host)
    await flushUi()
    await vi.dynamicImportSettled()
    await flushUi()

    host.querySelector<HTMLButtonElement>('.perception-cue')!.click()
    await flushUi()

    expect(host.querySelector<HTMLButtonElement>('.perception-cue')?.disabled).toBe(false)
    expect(host.querySelector('.dialogue-header')?.textContent).toContain('陌生人')
    expect(host.querySelector('[role="status"]')?.textContent).toContain('先问问候车的陌生人')
  })

  it('collects the same hotspot normally after the trust requirement is met', async () => {
    const initialState = makeState({ npc_trust: { chen_shouyi_1990: 35 } })
    const state = makeState({
      revision: 5,
      collected_fragments: ['station_clock_fragment'],
      revealed_fragments: ['station_clock_fragment'],
      fragment_states: {
        ...makeState().fragment_states,
        station_clock_fragment: {
          ...makeState().fragment_states.station_clock_fragment,
          status: 'collected',
          collected: true,
          revealed: true,
        },
      },
      npc_trust: { chen_shouyi_1990: 35 },
    })
    const scene = makeScene()
    apiMocks.getNewGame.mockResolvedValue({
      data: { state: initialState, scene_view: scene, content_version: 1 },
    })
    apiMocks.exploreHotspot.mockResolvedValue({
      data: {
        state,
        events: [
          {
            type: 'fragment.collected',
            content_id: 'station_clock_fragment',
            payload: {},
          },
        ],
      },
    })
    app = createApp(Game)
    app.use(createPinia())
    host = document.createElement('div')
    document.body.append(host)
    app.mount(host)
    await flushUi()
    await vi.dynamicImportSettled()
    await flushUi()

    host.querySelector<HTMLButtonElement>('.perception-cue')!.click()
    await flushUi()

    expect(apiMocks.exploreHotspot).toHaveBeenCalledWith(
      'station-clock-hotspot',
      expect.objectContaining({ revision: 4, npc_trust: { chen_shouyi_1990: 35 } }),
      4,
    )
    expect(useGameState().gameState.value?.revision).toBe(5)
    expect(useGameState().gameState.value?.collected_fragments).toContain('station_clock_fragment')
    expect(host.querySelector<HTMLButtonElement>('.perception-cue')?.disabled).toBe(true)
  })

  it('derives prompts only from uncollected dialogue fragments for the selected NPC', async () => {
    const state = makeState({ collected_fragments: ['already_collected'] })
    const scene = makeScene()
    scene.npcs.push({
      id: 'stranger_1990',
      name: '陌生人',
      title: '候车旅客',
      avatar: '',
      initial_trust: 40,
    })
    scene.fragments.push(
      {
        id: 'already_collected',
        name: '已归档车票',
        scene: 'scene_1990',
        description: '',
        unlock_method: 'dialogue',
        unlock_hint: '',
        memory_text: '',
        unlock_npc_id: 'chen_shouyi_1990',
        dialogue_prompt: '这条已经归档，不该继续出现。',
        is_revealed: true,
        is_collected: true,
      },
      {
        id: 'stranger_prompt',
        name: '陌生人的纸条',
        scene: 'scene_1990',
        description: '',
        unlock_method: 'dialogue',
        unlock_hint: '',
        memory_text: '',
        unlock_npc_id: 'stranger_1990',
        dialogue_prompt: '这是陌生人的问题。',
        is_revealed: false,
        is_collected: false,
      },
    )
    apiMocks.getNewGame.mockResolvedValue({
      data: { state, scene_view: scene, content_version: 1 },
    })
    app = createApp(Game)
    app.use(createPinia())
    host = document.createElement('div')
    document.body.append(host)
    app.mount(host)
    await flushUi()
    await vi.dynamicImportSettled()
    await flushUi()

    host.querySelectorAll<HTMLButtonElement>('.npc-chip')[0].click()
    await flushUi()

    const prompts = Array.from(host.querySelectorAll<HTMLButtonElement>('.suggested-prompt')).map(
      (prompt) => prompt.textContent,
    )
    expect(prompts).toHaveLength(1)
    expect(prompts[0]).toContain('那张南下的车票，是谁替你买的？')
    expect(prompts.join('')).not.toContain('已经归档')
    expect(prompts.join('')).not.toContain('陌生人的问题')
  })

  it('immediately selects newly collected dialogue evidence for the active hypothesis', async () => {
    const state = makeState()
    const scene = makeScene()
    scene.hypotheses = [
      {
        id: 'ticket-hypothesis',
        scene_id: 'scene_1990',
        question: '车票说明了什么？',
        statement: '它说明师父支持他南下。',
        evidence_ids: ['train_ticket_fragment'],
        resolution: '他带着师父的支持离开。',
      },
    ]
    const fragment: Fragment = {
      id: 'train_ticket_fragment',
      name: '南下车票',
      scene: 'scene_1990',
      description: '一张揉皱的车票。',
      unlock_method: 'dialogue',
      unlock_hint: '问问陈守义。',
      memory_text: '',
      collected: true,
    }
    apiMocks.getNewGame.mockResolvedValue({
      data: { state, scene_view: scene, content_version: 1 },
    })
    apiMocks.chatWithNpc.mockResolvedValue({
      data: {
        state: makeState({ revision: 5, collected_fragments: [fragment.id] }),
        reply: '车票是师父替我买的。',
        fragment_revealed: fragment.id,
        fragment_data: fragment,
        trust_change: 0,
        npc_mood: 'warm',
        inner_thought: '',
        degraded: false,
      },
    })
    apiMocks.requestNpcVoice.mockResolvedValue({
      data: {
        url: null,
        provider: 'silent',
        cached: false,
        media_type: null,
        duration_ms: null,
        line_id: null,
        cues: [],
        degraded: true,
      },
    })
    app = createApp(Game)
    app.use(createPinia())
    host = document.createElement('div')
    document.body.append(host)
    app.mount(host)
    await flushUi()
    await vi.dynamicImportSettled()
    await flushUi()

    host.querySelector<HTMLButtonElement>('.npc-chip')!.click()
    await flushUi()
    host.querySelector<HTMLButtonElement>('.suggested-prompt')!.click()
    await flushUi()
    await vi.dynamicImportSettled()
    await flushUi()

    const selectedEvidence = host.querySelector<HTMLButtonElement>(
      '.evidence-card[aria-pressed="true"]',
    )
    expect(selectedEvidence?.textContent).toContain('南下车票')
    expect(host.querySelector('.popup-overlay')).not.toBeNull()

    host.querySelector<HTMLButtonElement>('.btn-close')!.click()
    await flushUi()
    const input = host.querySelector<HTMLInputElement>('.chat-input')!
    input.value = '车票是谁买的？'
    input.dispatchEvent(new Event('input', { bubbles: true }))
    await nextTick()
    host.querySelector<HTMLButtonElement>('.send-btn')!.click()
    await flushUi()

    expect(host.querySelector('.popup-overlay')).toBeNull()
  })
})
