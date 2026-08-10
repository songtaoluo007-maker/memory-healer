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

const makeReasoningScene = (): SceneView => {
  const scene = makeScene()
  scene.hypotheses = [
    {
      id: 'station-departure-hypothesis',
      scene_id: 'scene_1990',
      question: '他为什么站在这里？',
      statement: '车票和时钟说明他准备南下。',
      evidence_ids: ['station_clock_fragment', 'train_ticket_fragment'],
      resolution: '他已经决定带着手艺离开。',
    },
  ]
  return scene
}

const makeCompleted1990Scene = (): SceneView => {
  const scene = makeScene()
  scene.scene.fragments = [
    'train_ticket_fragment',
    'farewell_letter_fragment',
    'puppet_trunk_fragment',
    'station_clock_fragment',
  ]
  scene.fragments = [
    {
      ...scene.fragments[1]!,
      is_revealed: true,
      is_collected: true,
    },
    {
      id: 'farewell_letter_fragment',
      name: '给师父的信',
      scene: 'scene_1990',
      description: '一封没有寄出的告别信。',
      unlock_method: 'explore',
      unlock_hint: '',
      memory_text: '',
      is_revealed: true,
      is_collected: true,
    },
    {
      id: 'puppet_trunk_fragment',
      name: '皮影木箱',
      scene: 'scene_1990',
      description: '箱中藏着一尊穿西装的皮影。',
      unlock_method: 'dialogue',
      unlock_hint: '',
      memory_text: '',
      unlock_npc_id: 'chen_shouyi_1990',
      dialogue_prompt: '箱子里为什么有一个穿西装的皮影？',
      is_revealed: true,
      is_collected: true,
    },
    {
      ...scene.fragments[0]!,
      is_revealed: true,
      is_collected: true,
    },
  ]
  scene.hotspots = scene.fragments.map((fragment, index) => ({
    id: `hotspot_1990_${fragment.id.replace('_fragment', '')}`,
    scene_id: 'scene_1990',
    label: fragment.name,
    x: [0.22, 0.34, 0.64, 0.78][index]!,
    y: [0.42, 0.62, 0.58, 0.3][index]!,
    radius: 0.06,
    fragment_id: fragment.id,
    npc_id: null,
    interaction: 'inspect',
    presentation_event: 'fragment.collected',
  }))
  scene.hypotheses = [
    {
      id: 'hypothesis_1990_survival',
      scene_id: 'scene_1990',
      question: '陈守义南下是否意味着他准备抛下皮影？',
      statement: '生存压力迫使他离开。',
      evidence_ids: ['train_ticket_fragment', 'farewell_letter_fragment'],
      resolution: '犹豫不能证明放弃。',
    },
    {
      id: 'hypothesis_1990_modern_story',
      scene_id: 'scene_1990',
      question: '陈守义为什么带着整箱皮影来到深圳？',
      statement: '他在为皮影寻找新讲法。',
      evidence_ids: ['puppet_trunk_fragment', 'station_clock_fragment'],
      resolution: '他带着皮影走进了新生活。',
    },
  ]
  scene.choices = [
    {
      id: 'open_puppet_trunk',
      scene_id: 'scene_1990',
      label: '打开木箱，让他看那个人偶',
      target_scene: 'scene_2024',
      is_key: true,
      effects: { trust_changes: {}, reveal_fragments: [], current_mood: null },
      requirements: [
        {
          kind: 'hypothesis_confirmed',
          hypothesis_id: 'hypothesis_1990_modern_story',
        },
      ],
    },
  ]
  return scene
}

const makeCompleted1990State = (): GameState => {
  const collected = [
    'fragment_grandpa_knife',
    'fragment_shadow_puppet',
    'train_ticket_fragment',
    'farewell_letter_fragment',
    'puppet_trunk_fragment',
    'station_clock_fragment',
  ]
  return makeState({
    revision: 18,
    collected_fragments: collected,
    revealed_fragments: collected,
    fragment_states: Object.fromEntries(
      collected.map((id) => [
        id,
        {
          id,
          name: id,
          status: 'collected',
          collected: true,
          revealed: true,
          scene: id.startsWith('fragment_') ? 'scene_1972' : 'scene_1990',
        },
      ]),
    ) as GameState['fragment_states'],
    npc_trust: { chen_shouyi_1990: 35 },
    confirmed_hypotheses: { scene_1990: 'hypothesis_1990_modern_story' },
  })
}

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

const installNarrowMatchMedia = () => {
  vi.stubGlobal(
    'matchMedia',
    vi.fn().mockImplementation((query: string) => ({
      matches: true,
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
    vi.unstubAllGlobals()
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

  it('enters an exclusive scan state that removes analysis chrome from focus and hit testing', async () => {
    const scene = makeReasoningScene()
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

    host.querySelector<HTMLButtonElement>('.scan-action')!.click()
    await flushUi()

    const root = host.querySelector<HTMLElement>('.game-cinema')!
    const analysisChrome = host.querySelector<HTMLElement>('.analysis-chrome')!
    const hotspot = host.querySelector<HTMLButtonElement>('.perception-cue')!
    const returnButton = host.querySelector<HTMLButtonElement>('.scan-return')!

    expect(root.classList.contains('scan-active')).toBe(true)
    expect(root.dataset.scanMode).toBe('active')
    expect(analysisChrome.getAttribute('aria-hidden')).toBe('true')
    expect(analysisChrome.hasAttribute('inert')).toBe(true)
    expect(analysisChrome.style.display).toBe('none')
    expect(analysisChrome.querySelector('.reasoning-panel-host')).not.toBeNull()
    expect(analysisChrome.querySelector('.narrative-float')).not.toBeNull()
    expect(analysisChrome.querySelector('.npc-dock')).not.toBeNull()
    expect(analysisChrome.querySelector('.tool-rail')).not.toBeNull()
    expect(analysisChrome.querySelector('.dialogue-float')).not.toBeNull()
    expect(analysisChrome.querySelector('.exploration-meter')).not.toBeNull()
    expect(analysisChrome.contains(hotspot)).toBe(false)
    expect(hotspot.disabled).toBe(false)
    expect(returnButton.textContent).toContain('返回推理')
    expect(document.activeElement).toBe(returnButton)
  })

  it('returns from scan mode with the fixed control and restores the reasoning action', async () => {
    const scene = makeReasoningScene()
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

    host.querySelector<HTMLButtonElement>('.scan-action')!.click()
    await flushUi()
    host.querySelector<HTMLButtonElement>('.scan-return')!.click()
    await flushUi()

    expect(host.querySelector('.game-cinema')?.classList.contains('scan-active')).toBe(false)
    expect(host.querySelector<HTMLElement>('.analysis-chrome')?.style.display).not.toBe('none')
    expect(host.querySelector('.scan-return')).toBeNull()
    expect(document.activeElement).toBe(host.querySelector('.scan-action'))
  })

  it('returns from scan mode when Escape is pressed', async () => {
    const scene = makeReasoningScene()
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

    host.querySelector<HTMLButtonElement>('.scan-action')!.click()
    await flushUi()
    expect(host.querySelector('.hotspot-overlay')?.classList.contains('scan-active')).toBe(true)
    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', cancelable: true }))
    await flushUi()

    expect(host.querySelector('.game-cinema')?.classList.contains('scan-active')).toBe(false)
    expect(host.querySelector('.hotspot-overlay')?.classList.contains('scan-active')).toBe(false)
    expect(host.querySelector('.scan-return')).toBeNull()
    expect(document.activeElement).toBe(host.querySelector('.scan-action'))
  })

  it('makes obscured reasoning inert and refuses hidden scan activation during dialogue', async () => {
    const scene = makeReasoningScene()
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

    host.querySelector<HTMLButtonElement>('.npc-chip')!.click()
    await flushUi()

    const reasoningHost = host.querySelector<HTMLElement>('.reasoning-panel-host')!
    expect(reasoningHost.classList.contains('obscured')).toBe(true)
    expect(reasoningHost.hasAttribute('inert')).toBe(true)
    expect(reasoningHost.getAttribute('aria-hidden')).toBe('true')

    reasoningHost.querySelector<HTMLButtonElement>('.scan-action')!.click()
    await flushUi()

    expect(host.querySelector('.game-cinema')?.classList.contains('scan-active')).toBe(false)
    expect(host.querySelector('.dialogue-float')?.classList.contains('open')).toBe(true)
  })

  it('keeps the archive overlay open when its hidden scan action is triggered programmatically', async () => {
    const scene = makeReasoningScene()
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

    host.querySelector<HTMLButtonElement>('.tool-rail button')!.click()
    await vi.dynamicImportSettled()
    await flushUi()

    const reasoningHost = host.querySelector<HTMLElement>('.reasoning-panel-host')!
    expect(host.querySelector('.memory-panel')).not.toBeNull()
    expect(reasoningHost.hasAttribute('inert')).toBe(true)
    expect(reasoningHost.getAttribute('aria-hidden')).toBe('true')

    reasoningHost.querySelector<HTMLButtonElement>('.scan-action')!.click()
    await flushUi()

    expect(host.querySelector('.game-cinema')?.classList.contains('scan-active')).toBe(false)
    expect(host.querySelector('.memory-panel')).not.toBeNull()
  })

  it('makes reasoning inert and refuses scan activation while a hypothesis request is pending', async () => {
    const scene = makeReasoningScene()
    const state = makeState({
      collected_fragments: ['station_clock_fragment', 'train_ticket_fragment'],
      revealed_fragments: ['station_clock_fragment', 'train_ticket_fragment'],
    })
    let resolveConfirmation:
      | ((value: { data: { state: GameState; events: never[] } }) => void)
      | undefined
    apiMocks.getNewGame.mockResolvedValue({
      data: { state, scene_view: scene, content_version: 1 },
    })
    apiMocks.confirmHypothesis.mockImplementation(
      () =>
        new Promise((resolve) => {
          resolveConfirmation = resolve
        }),
    )

    app = createApp(Game)
    app.use(createPinia())
    host = document.createElement('div')
    document.body.append(host)
    app.mount(host)
    await flushUi()
    await vi.dynamicImportSettled()
    await flushUi()

    for (const card of host.querySelectorAll<HTMLButtonElement>('.evidence-card')) card.click()
    await flushUi()
    host.querySelector<HTMLButtonElement>('.weave-action')!.click()
    await flushUi()

    const reasoningHost = host.querySelector<HTMLElement>('.reasoning-panel-host')!
    expect(reasoningHost.hasAttribute('inert')).toBe(true)
    expect(reasoningHost.getAttribute('aria-hidden')).toBe('true')
    reasoningHost.querySelector<HTMLButtonElement>('.scan-action')!.click()
    await flushUi()
    expect(host.querySelector('.game-cinema')?.classList.contains('scan-active')).toBe(false)

    resolveConfirmation?.({ data: { state, events: [] } })
    await flushUi()
  })

  it('refuses scan activation while a scene transition is rebuilding the view', async () => {
    const scene = makeReasoningScene()
    scene.choices = [
      {
        id: 'continue_to_2024',
        scene_id: 'scene_1990',
        label: '沿着记忆继续',
        target_scene: 'scene_2024',
        is_key: false,
        effects: { trust_changes: {}, reveal_fragments: [], current_mood: null },
        requirements: [],
      },
    ]
    const transitionedState = makeState({
      revision: 5,
      current_scene: 'scene_2024',
      visited_scenes: ['scene_1990', 'scene_2024'],
    })
    const nextScene = makeScene()
    nextScene.scene = {
      ...nextScene.scene,
      id: 'scene_2024',
      title: '城中村旧屋',
      time_period: '2024',
      fragments: [],
    }
    nextScene.fragments = []
    nextScene.hotspots = []
    nextScene.hypotheses = []
    nextScene.choices = []
    let resolveScene: ((value: { data: SceneView }) => void) | undefined
    apiMocks.getNewGame.mockResolvedValue({
      data: { state: makeState(), scene_view: scene, content_version: 1 },
    })
    apiMocks.recordChoice.mockResolvedValue({
      data: { state: transitionedState, events: [] },
    })
    apiMocks.getSceneView.mockImplementation(
      () =>
        new Promise((resolve) => {
          resolveScene = resolve
        }),
    )

    app = createApp(Game)
    app.use(createPinia())
    host = document.createElement('div')
    document.body.append(host)
    app.mount(host)
    await flushUi()
    await vi.dynamicImportSettled()
    await flushUi()

    host.querySelector<HTMLButtonElement>('.nav-btn')!.click()
    await flushUi()

    expect(apiMocks.getSceneView).toHaveBeenCalledOnce()
    expect(host.querySelector('.loading-overlay')).not.toBeNull()
    const reasoningHost = host.querySelector<HTMLElement>('.reasoning-panel-host')!
    expect(reasoningHost.hasAttribute('inert')).toBe(true)
    expect(reasoningHost.getAttribute('aria-hidden')).toBe('true')
    reasoningHost.querySelector<HTMLButtonElement>('.scan-action')!.click()
    await flushUi()
    expect(host.querySelector('.game-cinema')?.classList.contains('scan-active')).toBe(false)

    resolveScene?.({ data: nextScene })
    await flushUi()
  })

  it('preserves expanded voice controls across a scan round trip', async () => {
    installNarrowMatchMedia()
    const scene = makeReasoningScene()
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

    const voiceTrigger = host.querySelector<HTMLButtonElement>('[aria-label="展开语音控制"]')!
    voiceTrigger.click()
    await flushUi()

    expect(host.querySelector('.game-cinema')?.classList.contains('voice-controls-open')).toBe(true)
    expect(voiceTrigger.getAttribute('aria-expanded')).toBe('true')
    expect(host.querySelector<HTMLDivElement>('[data-voice-controls-panel]')?.hidden).toBe(false)

    host.querySelector<HTMLButtonElement>('.scan-action')!.click()
    await flushUi()
    host.querySelector<HTMLButtonElement>('.scan-return')!.click()
    await flushUi()

    expect(host.querySelector('.game-cinema')?.classList.contains('voice-controls-open')).toBe(true)
    expect(voiceTrigger.getAttribute('aria-expanded')).toBe('true')
    expect(host.querySelector<HTMLDivElement>('[data-voice-controls-panel]')?.hidden).toBe(false)
  })

  it('rebuilds completed reasoning and exploration from an authoritative loaded save', async () => {
    const state = makeCompleted1990State()
    const scene = makeCompleted1990Scene()
    apiMocks.loadGame.mockResolvedValue({
      data: { game_state: state, save_revision: 7 },
    })
    apiMocks.getSceneView.mockResolvedValue({ data: scene })

    app = createApp(Game, { loadSlotId: 0 })
    app.use(createPinia())
    host = document.createElement('div')
    document.body.append(host)
    app.mount(host)
    await flushUi()
    await vi.dynamicImportSettled()
    await flushUi()

    expect(apiMocks.loadGame).toHaveBeenCalledWith(0)
    expect(apiMocks.getSceneView).toHaveBeenCalledWith(
      expect.objectContaining({ revision: 18, collected_fragments: state.collected_fragments }),
    )
    expect(
      host
        .querySelector('[data-hypothesis-id="hypothesis_1990_modern_story"]')
        ?.getAttribute('aria-pressed'),
    ).toBe('true')
    expect(host.querySelector('.reasoning-header')?.textContent).toContain('推理完成')

    const evidenceCards = [...host.querySelectorAll<HTMLButtonElement>('.evidence-card')]
    expect(evidenceCards).toHaveLength(2)
    expect(evidenceCards.every((card) => card.disabled)).toBe(true)
    expect(evidenceCards.every((card) => card.getAttribute('aria-pressed') === 'true')).toBe(true)
    expect(host.querySelector('.scene-nav.choice-lock')).toBeNull()
    expect(host.querySelector('.scene-nav')?.textContent).toContain('打开木箱，让他看那个人偶')

    const hotspots = [...host.querySelectorAll<HTMLButtonElement>('.perception-cue')]
    expect(hotspots).toHaveLength(4)
    expect(hotspots.every((hotspot) => hotspot.disabled)).toBe(true)
    expect(host.querySelector('.exploration-meter')?.textContent).toContain('100%')
  })

  it('keeps the authoritative hotspot path available in scan mode and exits into its fragment', async () => {
    const initialState = makeState({ npc_trust: { chen_shouyi_1990: 35 } })
    const collectedState = makeState({
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
    const scene = makeReasoningScene()
    apiMocks.getNewGame.mockResolvedValue({
      data: { state: initialState, scene_view: scene, content_version: 1 },
    })
    apiMocks.exploreHotspot.mockResolvedValue({
      data: {
        state: collectedState,
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

    host.querySelector<HTMLButtonElement>('.scan-action')!.click()
    await flushUi()
    expect(host.querySelector('.hotspot-overlay')?.classList.contains('scan-active')).toBe(true)
    host.querySelector<HTMLButtonElement>('.perception-cue')!.click()
    await flushUi()

    expect(apiMocks.exploreHotspot).toHaveBeenCalledWith(
      'station-clock-hotspot',
      expect.objectContaining({ revision: 4, npc_trust: { chen_shouyi_1990: 35 } }),
      4,
    )
    expect(host.querySelector('.game-cinema')?.classList.contains('scan-active')).toBe(false)
    expect(host.querySelector('.hotspot-overlay')?.classList.contains('scan-active')).toBe(false)
    expect(host.querySelector('.popup-overlay')).not.toBeNull()

    const reasoningHost = host.querySelector<HTMLElement>('.reasoning-panel-host')!
    expect(reasoningHost.hasAttribute('inert')).toBe(true)
    expect(reasoningHost.getAttribute('aria-hidden')).toBe('true')
    reasoningHost.querySelector<HTMLButtonElement>('.scan-action')!.click()
    await flushUi()

    expect(host.querySelector('.game-cinema')?.classList.contains('scan-active')).toBe(false)
    expect(host.querySelector('.popup-overlay')).not.toBeNull()
  })

  it('exits scan mode into the canonical NPC task when a hotspot is still locked', async () => {
    const scene = makeReasoningScene()
    apiMocks.getNewGame.mockResolvedValue({
      data: { state: makeState(), scene_view: scene, content_version: 1 },
    })
    apiMocks.exploreHotspot.mockResolvedValue({
      data: {
        state: makeState(),
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

    host.querySelector<HTMLButtonElement>('.scan-action')!.click()
    await flushUi()
    expect(host.querySelector('.hotspot-overlay')?.classList.contains('scan-active')).toBe(true)
    host.querySelector<HTMLButtonElement>('.perception-cue')!.click()
    await flushUi()

    expect(apiMocks.exploreHotspot).toHaveBeenCalledTimes(1)
    expect(host.querySelector('.game-cinema')?.classList.contains('scan-active')).toBe(false)
    expect(host.querySelector('.hotspot-overlay')?.classList.contains('scan-active')).toBe(false)
    expect(host.querySelector<HTMLButtonElement>('.perception-cue')?.disabled).toBe(false)
    expect(host.querySelector('.dialogue-header')?.textContent).toContain('陈守义')
    expect(host.querySelector('[role="status"]')?.textContent).toContain('当前 20 / 需要 35')
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
