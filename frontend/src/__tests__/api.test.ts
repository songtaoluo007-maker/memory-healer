/**
 * 前端API测试
 * 测试API层的基本功能
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import type { DialogueRequest, GameState } from '../types/game'

const createGameState = (overrides: Partial<GameState> = {}): GameState => ({
  schema_version: 1,
  game_id: '00000000-0000-0000-0000-000000000001',
  revision: 0,
  current_scene: 'scene_1972',
  visited_scenes: ['scene_1972'],
  collected_fragments: [],
  revealed_fragments: [],
  fragment_states: {},
  npc_trust: {},
  npc_emotions: {},
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

// Use vi.hoisted to define mock functions before vi.mock is hoisted
const { mockPost, mockGet, mockDelete, mockCreate, mockApi } = vi.hoisted(() => {
  const mockApi = {
    defaults: {
      withCredentials: true,
      headers: { common: {} as Record<string, string> },
    },
    interceptors: {
      request: { use: vi.fn() },
      response: { use: vi.fn() },
    },
    post: vi.fn(),
    get: vi.fn(),
    delete: vi.fn(),
  }

  return {
    mockPost: mockApi.post,
    mockGet: mockApi.get,
    mockDelete: mockApi.delete,
    mockCreate: vi.fn(() => mockApi),
    mockApi,
  }
})

// Mock axios before importing the module
vi.mock('axios', () => ({
  default: {
    create: mockCreate,
  },
}))

// Import after mocking
import {
  chatWithNpc,
  confirmHypothesis,
  exploreHotspot,
  getNewGame,
  getSceneView,
  saveGame,
  loadGame,
  listSaves,
  deleteSave,
  healthCheck,
  getFixedVoiceLine,
  recordChoice,
  requestNpcVoice,
} from '../api'

describe('API Layer', () => {
  beforeEach(() => {
    mockPost.mockReset()
    mockGet.mockReset()
    mockDelete.mockReset()
  })

  it('uses same-origin Cookie authentication without bearer headers', () => {
    expect(mockCreate).toHaveBeenCalledWith({
      baseURL: '/api',
      timeout: 60000,
      withCredentials: true,
    })
    expect(mockApi.interceptors.request.use).not.toHaveBeenCalled()
    expect(mockApi.defaults.headers.common.Authorization).toBeUndefined()
  })

  it('chatWithNpc sends correct request', async () => {
    const requestData: DialogueRequest = {
      npc_id: 'li_yun',
      player_input: '你好',
      game_state: createGameState(),
      expected_revision: 0,
    }
    mockPost.mockResolvedValue({ data: { reply: '你好！' } })

    const result = await chatWithNpc(requestData)

    expect(mockPost).toHaveBeenCalledWith('/dialogue/chat', requestData)
    expect(result.data.reply).toBe('你好！')
  })

  it('getSceneView sends the authoritative state', async () => {
    const gameState = createGameState()
    mockPost.mockResolvedValue({ data: { scene: {} } })

    await getSceneView(gameState)

    expect(mockPost).toHaveBeenCalledWith('/game/scene', { game_state: gameState })
  })

  it('getNewGame sends GET request', async () => {
    mockGet.mockResolvedValue({ data: { current_scene: 'scene_1972' } })

    await getNewGame()

    expect(mockGet).toHaveBeenCalledWith('/game/new')
  })

  it('exploreHotspot sends an expected revision', async () => {
    const gameState = createGameState({ revision: 4 })
    mockPost.mockResolvedValue({ data: { state: gameState, events: [] } })

    await exploreHotspot('hotspot_1972_shadow_stage', gameState, 4)

    expect(mockPost).toHaveBeenCalledWith('/game/explore', {
      hotspot_id: 'hotspot_1972_shadow_stage',
      game_state: gameState,
      expected_revision: 4,
    })
  })

  it('saveGame sends correct request', async () => {
    mockPost.mockResolvedValue({ data: { success: true } })

    const gameState = createGameState()
    await saveGame(1, '测试存档', gameState, 3)

    expect(mockPost).toHaveBeenCalledWith('/save/save', {
      slot_id: 1,
      slot_name: '测试存档',
      game_state: gameState,
      expected_revision: 3,
    })
  })

  it('loadGame sends correct request', async () => {
    mockPost.mockResolvedValue({ data: { game_state: {} } })

    await loadGame(1)

    expect(mockPost).toHaveBeenCalledWith('/save/load', { slot_id: 1 })
  })

  it('listSaves sends GET request', async () => {
    mockGet.mockResolvedValue({ data: { saves: [] } })

    await listSaves()

    expect(mockGet).toHaveBeenCalledWith('/save/list')
  })

  it('deleteSave sends DELETE request', async () => {
    mockDelete.mockResolvedValue({ data: { success: true } })

    await deleteSave(1)

    expect(mockDelete).toHaveBeenCalledWith('/save/delete/1')
  })

  it('healthCheck sends GET request', async () => {
    mockGet.mockResolvedValue({ data: { status: 'ok' } })

    await healthCheck()

    expect(mockGet).toHaveBeenCalledWith('/health')
  })

  it('recordChoice sends correct request', async () => {
    mockPost.mockResolvedValue({ data: { success: true } })

    const gameState = createGameState({ revision: 2 })
    await recordChoice('encourage_art', gameState, 2)

    expect(mockPost).toHaveBeenCalledWith('/game/choice', {
      choice_id: 'encourage_art',
      game_state: gameState,
      expected_revision: 2,
    })
  })

  it('confirmHypothesis sends evidence with the expected revision', async () => {
    mockPost.mockResolvedValue({ data: { success: true } })

    const gameState = createGameState({ revision: 3 })
    await confirmHypothesis(
      'hypothesis_1972_legacy',
      ['fragment_grandpa_knife', 'fragment_shadow_puppet'],
      gameState,
      3,
    )

    expect(mockPost).toHaveBeenCalledWith('/game/hypothesis', {
      hypothesis_id: 'hypothesis_1972_legacy',
      evidence_ids: ['fragment_grandpa_knife', 'fragment_shadow_puppet'],
      game_state: gameState,
      expected_revision: 3,
    })
  })

  it('requests provider-neutral NPC voice', async () => {
    mockPost.mockResolvedValue({
      data: {
        url: '/voice/cache/generated.wav',
        provider: 'cosyvoice',
        cached: false,
        media_type: 'audio/wav',
        duration_ms: null,
        line_id: null,
        cues: [],
        degraded: false,
      },
    })

    const response = await requestNpcVoice('台词', 'chen_shouyi_young', 'warm', 0.4)

    expect(response.data.provider).toBe('cosyvoice')
    expect(mockPost).toHaveBeenCalledWith('/voice/speak', {
      text: '台词',
      npc_id: 'chen_shouyi_young',
      emotion: 'warm',
      intensity: 0.4,
    })
  })

  it('requests fixed voice lines with an encoded ID', async () => {
    mockGet.mockResolvedValue({ data: { line_id: 'scene 1972/transition' } })

    await getFixedVoiceLine('scene 1972/transition')

    expect(mockGet).toHaveBeenCalledWith('/voice/lines/scene%201972%2Ftransition')
  })
})
