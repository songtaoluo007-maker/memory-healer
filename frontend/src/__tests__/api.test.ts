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
  getSceneDetail,
  getInitialState,
  saveGame,
  loadGame,
  listSaves,
  deleteSave,
  healthCheck,
  recordChoice,
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
    }
    mockPost.mockResolvedValue({ data: { reply: '你好！' } })

    const result = await chatWithNpc(requestData)

    expect(mockPost).toHaveBeenCalledWith('/dialogue/chat', requestData)
    expect(result.data.reply).toBe('你好！')
  })

  it('getSceneDetail sends correct request', async () => {
    const gameState = createGameState()
    mockPost.mockResolvedValue({ data: { scene: {} } })

    await getSceneDetail('scene_1972', gameState)

    expect(mockPost).toHaveBeenCalledWith('/scene/detail', {
      scene_id: 'scene_1972',
      game_state: gameState,
    })
  })

  it('getInitialState sends GET request', async () => {
    mockGet.mockResolvedValue({ data: { current_scene: 'scene_1972' } })

    await getInitialState()

    expect(mockGet).toHaveBeenCalledWith('/scene/initial-state')
  })

  it('saveGame sends correct request', async () => {
    mockPost.mockResolvedValue({ data: { success: true } })

    const gameState = createGameState()
    await saveGame(1, '测试存档', gameState, 'scene_1972', 120)

    expect(mockPost).toHaveBeenCalledWith('/save/save', {
      slot_id: 1,
      slot_name: '测试存档',
      game_state: gameState,
      scene_id: 'scene_1972',
      play_time: 120,
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

    const gameState = createGameState()
    await recordChoice('scene_1972', 'encourage', gameState)

    expect(mockPost).toHaveBeenCalledWith('/dialogue/choice', {
      scene: 'scene_1972',
      choice: 'encourage',
      game_state: gameState,
    })
  })
})
