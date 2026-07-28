import { createApp, defineComponent, h, nextTick } from 'vue'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import type {
  ActionResult,
  DialogueResponse,
  GameState,
  NpcSummary,
  PresentationEvent,
  VoiceResponse,
} from '../types/game'

const apiMocks = vi.hoisted(() => ({
  exploreHotspot: vi.fn(),
  recordChoice: vi.fn(),
  chatWithNpc: vi.fn(),
  getNewGame: vi.fn(),
  loadGame: vi.fn(),
  requestNpcVoice: vi.fn(),
  saveGame: vi.fn(),
}))

vi.mock('../api', () => apiMocks)

const sfxMocks = vi.hoisted(() => ({
  playSFX: vi.fn(),
}))

vi.mock('../composables/useSfxBus', () => ({
  useSfxBus: () => sfxMocks,
}))

import { StateRevisionError, useGameState } from '../composables/useGameState'
import ChatPanel from '../components/ChatPanel.vue'

const makeState = (overrides: Partial<GameState> = {}): GameState => ({
  schema_version: 1,
  game_id: '00000000-0000-0000-0000-000000000001',
  revision: 0,
  current_scene: 'scene_1972',
  visited_scenes: ['scene_1972'],
  collected_fragments: [],
  revealed_fragments: [],
  fragment_states: {
    fragment_shadow_puppet: {
      id: 'fragment_shadow_puppet',
      name: '皮影戏幕',
      status: 'hidden',
      collected: false,
      revealed: false,
      scene: 'scene_1972',
    },
  },
  npc_trust: { chen_shouyi_young: 30 },
  npc_emotions: { chen_shouyi_young: 'neutral' },
  key_choices: [],
  butterfly_choices: {},
  dialogue_history: [],
  current_mood: 'warm',
  play_time_seconds: 0,
  started_at: '2026-07-26T12:00:00Z',
  chapter: 1,
  ending: null,
  ...overrides,
})

const action = (state: GameState, events: PresentationEvent[] = []): ActionResult => ({
  state,
  events,
})

describe('authoritative state writeback', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    useGameState().gameState.value = null
  })

  it('does not mutate exploration state before the server responds', async () => {
    const { gameState, exploreHotspot } = useGameState()
    gameState.value = makeState()
    let resolveResponse!: (value: { data: ActionResult }) => void
    apiMocks.exploreHotspot.mockReturnValue(
      new Promise((resolve) => {
        resolveResponse = resolve
      }),
    )

    const pending = exploreHotspot('hotspot_1972_shadow_stage')
    expect(gameState.value.collected_fragments).toEqual([])

    const next = makeState({
      revision: 1,
      collected_fragments: ['fragment_shadow_puppet'],
      revealed_fragments: ['fragment_shadow_puppet'],
      fragment_states: {
        fragment_shadow_puppet: {
          ...gameState.value.fragment_states.fragment_shadow_puppet,
          status: 'collected',
          collected: true,
          revealed: true,
        },
      },
    })
    resolveResponse({ data: action(next) })
    await pending

    expect(gameState.value).toEqual(next)
  })

  it('applies choice and dialogue responses as complete states', async () => {
    const { gameState, submitChoice, sendDialogue } = useGameState()
    gameState.value = makeState()
    const afterChoice = makeState({
      revision: 1,
      current_scene: 'scene_1990',
      visited_scenes: ['scene_1972', 'scene_1990'],
      butterfly_choices: { scene_1972: 'encourage_art' },
    })
    apiMocks.recordChoice.mockResolvedValue({ data: action(afterChoice) })

    await submitChoice('encourage_art')
    expect(gameState.value.butterfly_choices.scene_1972).toBe('encourage_art')
    expect(gameState.value.current_scene).toBe('scene_1990')

    const afterDialogue = makeState({
      ...afterChoice,
      revision: 2,
      dialogue_history: [
        { role: 'player', content: '你还记得吗？' },
        {
          role: 'npc',
          npc_id: 'chen_shouyi_1990',
          content: '记得那张南下的车票。',
          emotion: 'warm',
        },
      ],
    })
    const response: DialogueResponse = {
      state: afterDialogue,
      reply: '记得那张南下的车票。',
      fragment_revealed: null,
      fragment_data: null,
      trust_change: 0,
      npc_mood: 'warm',
      inner_thought: '',
      degraded: false,
    }
    apiMocks.chatWithNpc.mockResolvedValue({ data: response })

    await sendDialogue('chen_shouyi_1990', '你还记得吗？')

    expect(gameState.value.dialogue_history.map((message) => message.role)).toEqual([
      'player',
      'npc',
    ])
  })

  it('rejects an older response without overwriting newer local authority', async () => {
    const { gameState, exploreHotspot } = useGameState()
    gameState.value = makeState({ revision: 5 })
    apiMocks.exploreHotspot.mockResolvedValue({
      data: action(makeState({ revision: 4 })),
    })

    await expect(exploreHotspot('hotspot_1972_shadow_stage')).rejects.toBeInstanceOf(
      StateRevisionError,
    )
    expect(gameState.value.revision).toBe(5)
  })
})

const selectedNpc: NpcSummary = {
  id: 'chen_shouyi_young',
  name: '陈守义',
  title: '皮影匠人',
  avatar: '/chen.webp',
  initial_trust: 30,
  initial_voice_line_id: 'npc.chen_shouyi_young.intro',
}

const silentVoice: VoiceResponse = {
  url: null,
  provider: 'silent',
  cached: false,
  media_type: null,
  duration_ms: null,
  line_id: null,
  cues: [],
  degraded: true,
}

const flushUi = async () => {
  await Promise.resolve()
  await nextTick()
  await Promise.resolve()
  await nextTick()
}

describe('dynamic NPC voice', () => {
  let app: ReturnType<typeof createApp> | null = null
  let host: HTMLDivElement | null = null
  let panel: { stopVoice: () => void } | null = null

  beforeEach(() => {
    vi.clearAllMocks()
    useGameState().gameState.value = makeState()
    panel = null
  })

  afterEach(() => {
    app?.unmount()
    host?.remove()
    app = null
    host = null
    vi.unstubAllGlobals()
  })

  const mountChat = () => {
    const state = useGameState().gameState
    app = createApp(
      defineComponent({
        setup() {
          return () =>
            h(ChatPanel, {
              ref: (value: unknown) => {
                panel = value as typeof panel
              },
              selectedNpc,
              gameState: state.value,
            })
        },
      }),
    )
    host = document.createElement('div')
    document.body.append(host)
    app.mount(host)
    return host
  }

  const submitMessage = async (reply = '额还记得那方戏幕。') => {
    const nextState = makeState({
      revision: 1,
      dialogue_history: [
        { role: 'player', content: '你还记得吗？' },
        {
          role: 'npc',
          npc_id: selectedNpc.id,
          content: reply,
          emotion: 'warm',
        },
      ],
    })
    apiMocks.chatWithNpc.mockResolvedValue({
      data: {
        state: nextState,
        reply,
        fragment_revealed: null,
        fragment_data: null,
        trust_change: 0,
        npc_mood: 'warm',
        inner_thought: '',
        degraded: false,
      } satisfies DialogueResponse,
    })

    const input = host!.querySelector<HTMLInputElement>('.chat-input')!
    input.value = '你还记得吗？'
    input.dispatchEvent(new Event('input', { bubbles: true }))
    await nextTick()
    host!.querySelector<HTMLButtonElement>('.send-btn')!.click()
    await flushUi()
    return reply
  }

  it('shows authoritative text and re-enables input before a silent voice request settles', async () => {
    let resolveVoice!: (value: { data: VoiceResponse }) => void
    apiMocks.requestNpcVoice.mockReturnValue(
      new Promise((resolve) => {
        resolveVoice = resolve
      }),
    )
    mountChat()

    const reply = await submitMessage()

    expect(host!.textContent).toContain(reply)
    expect(host!.querySelector<HTMLInputElement>('.chat-input')!.disabled).toBe(false)
    expect(apiMocks.requestNpcVoice).toHaveBeenCalledWith(reply, selectedNpc.id, 'warm', 0.5)

    resolveVoice({ data: silentVoice })
    await flushUi()
    expect(host!.textContent).toContain(reply)
    expect(host!.querySelector<HTMLInputElement>('.chat-input')!.disabled).toBe(false)
  })

  it('does not play a delayed voice response after the dialogue has closed', async () => {
    let resolveVoice!: (value: { data: VoiceResponse }) => void
    apiMocks.requestNpcVoice.mockReturnValue(
      new Promise((resolve) => {
        resolveVoice = resolve
      }),
    )
    const audioFactory = vi.fn(() => ({
      addEventListener: vi.fn(),
      pause: vi.fn(),
      play: vi.fn().mockResolvedValue(undefined),
      preload: '',
      src: '',
      volume: 1,
    }))
    vi.stubGlobal('Audio', audioFactory)
    mountChat()
    await submitMessage()

    panel!.stopVoice()
    resolveVoice({
      data: {
        ...silentVoice,
        url: '/voice/runtime/reply.mp3',
        provider: 'edge',
        media_type: 'audio/mpeg',
        duration_ms: 900,
      },
    })
    await flushUi()

    expect(audioFactory).not.toHaveBeenCalled()
  })

  it('stops active dialogue audio when the dialogue closes', async () => {
    const audio = {
      addEventListener: vi.fn(),
      pause: vi.fn(),
      play: vi.fn().mockResolvedValue(undefined),
      preload: '',
      src: '',
      volume: 1,
    }
    vi.stubGlobal('Audio', vi.fn(() => audio))
    apiMocks.requestNpcVoice.mockResolvedValue({
      data: {
        ...silentVoice,
        url: '/voice/runtime/reply.mp3',
        provider: 'edge',
        media_type: 'audio/mpeg',
        duration_ms: 900,
      },
    })
    mountChat()
    await submitMessage()
    await flushUi()

    panel!.stopVoice()

    expect(audio.pause).toHaveBeenCalledOnce()
  })
})
