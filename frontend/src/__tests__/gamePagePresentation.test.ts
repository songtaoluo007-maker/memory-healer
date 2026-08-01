import { createApp, defineComponent, h, nextTick, ref } from 'vue'
import { createPinia } from 'pinia'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import type { GameState, SceneView } from '../types/game'

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
    setup(_, { slots }) {
      return () => h('div', slots.default?.())
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
      minimum_trust: 30,
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
    apiMocks.getNewGame.mockResolvedValue({ data: { state, scene_view: scene, content_version: 1 } })
  })

  afterEach(() => {
    app?.unmount()
    host?.remove()
    app = null
    host = null
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
              minimum_trust: 30,
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
  })

  it('collects the same hotspot normally after the trust requirement is met', async () => {
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
      npc_trust: { chen_shouyi_1990: 30 },
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

    expect(useGameState().gameState.value?.revision).toBe(5)
    expect(useGameState().gameState.value?.collected_fragments).toContain('station_clock_fragment')
    expect(host.querySelector<HTMLButtonElement>('.perception-cue')?.disabled).toBe(true)
  })
})
