/**
 * useGameState 测试
 */

import { describe, it, expect, beforeEach } from 'vitest'
import { useGameState } from '../composables/useGameState'

describe('useGameState', () => {
  beforeEach(() => {
    // Reset game state before each test
    const { gameState } = useGameState()
    gameState.value = null
  })

  it('initializes with null game state', () => {
    const { gameState } = useGameState()
    expect(gameState.value).toBeNull()
  })

  it('gameState can be set directly', () => {
    const { gameState } = useGameState()
    const initialState = {
      current_scene: 'scene_1972',
      collected_fragments: [],
      revealed_fragments: [],
      fragment_states: {},
      npc_trust: {},
      key_choices: [],
      dialogue_history: [],
      current_mood: 'warm',
      play_time: 0,
      play_start_time: Date.now(),
      chapter: 1,
      ending: null,
    }
    gameState.value = initialState as any
    expect(gameState.value).not.toBeNull()
    expect(gameState.value?.current_scene).toBe('scene_1972')
  })

  it('collectFragment adds fragment to collected list', () => {
    const { gameState, collectFragment } = useGameState()
    const initialState = {
      current_scene: 'scene_1972',
      collected_fragments: [],
      revealed_fragments: [],
      fragment_states: {},
      npc_trust: {},
      key_choices: [],
      dialogue_history: [],
      current_mood: 'warm',
      play_time: 0,
      play_start_time: Date.now(),
      chapter: 1,
      ending: null,
    }
    gameState.value = initialState as any
    collectFragment('f1')
    expect(gameState.value?.collected_fragments).toContain('f1')
  })

  it('collectFragment does not add duplicate fragment', () => {
    const { gameState, collectFragment } = useGameState()
    const initialState = {
      current_scene: 'scene_1972',
      collected_fragments: ['f1'],
      revealed_fragments: [],
      fragment_states: {},
      npc_trust: {},
      key_choices: [],
      dialogue_history: [],
      current_mood: 'warm',
      play_time: 0,
      play_start_time: Date.now(),
      chapter: 1,
      ending: null,
    }
    gameState.value = initialState as any
    collectFragment('f1')
    expect(gameState.value?.collected_fragments).toHaveLength(1)
  })

  it('updateTrust updates NPC trust value', () => {
    const { gameState, updateTrust } = useGameState()
    const initialState = {
      current_scene: 'scene_1972',
      collected_fragments: [],
      revealed_fragments: [],
      fragment_states: {},
      npc_trust: {},
      key_choices: [],
      dialogue_history: [],
      current_mood: 'warm',
      play_time: 0,
      play_start_time: Date.now(),
      chapter: 1,
      ending: null,
    }
    gameState.value = initialState as any
    updateTrust('li_yun', 10)
    // Default trust is 30, so 30 + 10 = 40
    expect(gameState.value?.npc_trust['li_yun']).toBe(40)
  })

  it('changeScene changes current scene', () => {
    const { gameState, changeScene } = useGameState()
    const initialState = {
      current_scene: 'scene_1972',
      collected_fragments: [],
      revealed_fragments: [],
      fragment_states: {},
      npc_trust: {},
      key_choices: [],
      dialogue_history: [],
      current_mood: 'warm',
      play_time: 0,
      play_start_time: Date.now(),
      chapter: 1,
      ending: null,
    }
    gameState.value = initialState as any
    changeScene('scene_2024')
    expect(gameState.value?.current_scene).toBe('scene_2024')
  })

  it('collectedCount returns correct count', () => {
    const { gameState, collectedCount } = useGameState()
    const initialState = {
      current_scene: 'scene_1972',
      collected_fragments: ['f1', 'f2'],
      revealed_fragments: [],
      fragment_states: {},
      npc_trust: {},
      key_choices: [],
      dialogue_history: [],
      current_mood: 'warm',
      play_time: 0,
      play_start_time: Date.now(),
      chapter: 1,
      ending: null,
    }
    gameState.value = initialState as any
    expect(collectedCount.value).toBe(2)
  })

  it('totalFragments returns correct count', () => {
    const { gameState, totalFragments } = useGameState()
    const initialState = {
      current_scene: 'scene_1972',
      collected_fragments: [],
      revealed_fragments: [],
      fragment_states: {
        f1: { collected: false, revealed: false },
        f2: { collected: false, revealed: false },
        f3: { collected: false, revealed: false },
      },
      npc_trust: {},
      key_choices: [],
      dialogue_history: [],
      current_mood: 'warm',
      play_time: 0,
      play_start_time: Date.now(),
      chapter: 1,
      ending: null,
    }
    gameState.value = initialState as any
    expect(totalFragments.value).toBe(3)
  })
})
