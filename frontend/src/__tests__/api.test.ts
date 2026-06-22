/**
 * 前端API测试
 * 测试API层的基本功能
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

// Use vi.hoisted to define mock functions before vi.mock is hoisted
const { mockPost, mockGet, mockDelete } = vi.hoisted(() => ({
  mockPost: vi.fn(),
  mockGet: vi.fn(),
  mockDelete: vi.fn(),
}))

// Mock axios before importing the module
vi.mock('axios', () => ({
  default: {
    create: vi.fn(() => ({
      post: mockPost,
      get: mockGet,
      delete: mockDelete,
    })),
  },
}))

// Import after mocking
import {
  chatWithNpc,
  getSceneDetail,
  advanceNarrative,
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

  it('chatWithNpc sends correct request', async () => {
    const requestData = {
      npc_id: 'li_yun',
      player_input: '你好',
      game_state: {},
    }
    mockPost.mockResolvedValue({ data: { reply: '你好！' } })

    const result = await chatWithNpc(requestData as any)

    expect(mockPost).toHaveBeenCalledWith('/api/dialogue/chat', requestData)
    expect(result.data.reply).toBe('你好！')
  })

  it('getSceneDetail sends correct request', async () => {
    const gameState = { current_scene: 'scene_1972' }
    mockPost.mockResolvedValue({ data: { scene: {} } })

    await getSceneDetail('scene_1972', gameState as any)

    expect(mockPost).toHaveBeenCalledWith('/api/scene/detail', {
      scene_id: 'scene_1972',
      game_state: gameState,
    })
  })

  it('getInitialState sends GET request', async () => {
    mockGet.mockResolvedValue({ data: { current_scene: 'scene_1972' } })

    await getInitialState()

    expect(mockGet).toHaveBeenCalledWith('/api/scene/initial-state')
  })

  it('saveGame sends correct request', async () => {
    mockPost.mockResolvedValue({ data: { success: true } })

    await saveGame(1, '测试存档', {} as any, 'scene_1972', 120)

    expect(mockPost).toHaveBeenCalledWith('/api/save/save', {
      slot_id: 1,
      slot_name: '测试存档',
      game_state: {},
      scene_id: 'scene_1972',
      play_time: 120,
    })
  })

  it('loadGame sends correct request', async () => {
    mockPost.mockResolvedValue({ data: { game_state: {} } })

    await loadGame(1)

    expect(mockPost).toHaveBeenCalledWith('/api/save/load', { slot_id: 1 })
  })

  it('listSaves sends GET request', async () => {
    mockGet.mockResolvedValue({ data: { saves: [] } })

    await listSaves()

    expect(mockGet).toHaveBeenCalledWith('/api/save/list')
  })

  it('deleteSave sends DELETE request', async () => {
    mockDelete.mockResolvedValue({ data: { success: true } })

    await deleteSave(1)

    expect(mockDelete).toHaveBeenCalledWith('/api/save/delete/1')
  })

  it('healthCheck sends GET request', async () => {
    mockGet.mockResolvedValue({ data: { status: 'ok' } })

    await healthCheck()

    expect(mockGet).toHaveBeenCalledWith('/api/health')
  })

  it('recordChoice sends correct request', async () => {
    mockPost.mockResolvedValue({ data: { success: true } })

    await recordChoice('scene_1972', 'encourage', {} as any)

    expect(mockPost).toHaveBeenCalledWith('/api/dialogue/choice', {
      scene: 'scene_1972',
      choice: 'encourage',
      game_state: {},
    })
  })
})
