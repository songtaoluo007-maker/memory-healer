import { beforeEach, describe, expect, it } from 'vitest'
import { useGameState } from '../composables/useGameState'
import type { GameState } from '../types/game'

const createGameState = (overrides: Partial<GameState> = {}): GameState => ({
  current_scene: 'scene_1972',
  visited_scenes: ['scene_1972'],
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
  ...overrides,
})

describe('useGameState', () => {
  beforeEach(() => {
    const { gameState } = useGameState()
    gameState.value = null
  })

  it('initializes with null game state', () => {
    const { gameState } = useGameState()
    expect(gameState.value).toBeNull()
  })

  it('gameState can be set directly', () => {
    const { gameState } = useGameState()
    gameState.value = createGameState()

    expect(gameState.value.current_scene).toBe('scene_1972')
  })

  it('collectFragment adds fragment to collected list', () => {
    const { gameState, collectFragment } = useGameState()
    gameState.value = createGameState()

    collectFragment('f1')

    expect(gameState.value.collected_fragments).toContain('f1')
  })

  it('collectFragment does not add duplicate fragment', () => {
    const { gameState, collectFragment } = useGameState()
    gameState.value = createGameState({ collected_fragments: ['f1'] })

    collectFragment('f1')

    expect(gameState.value.collected_fragments).toHaveLength(1)
  })

  it('updateTrust updates NPC trust value', () => {
    const { gameState, updateTrust } = useGameState()
    gameState.value = createGameState()

    updateTrust('li_yun', 10)

    expect(gameState.value.npc_trust.li_yun).toBe(40)
  })

  it('changeScene changes current scene', () => {
    const { gameState, changeScene } = useGameState()
    gameState.value = createGameState()

    changeScene('scene_2024')

    expect(gameState.value.current_scene).toBe('scene_2024')
  })

  it('collectedCount returns correct count', () => {
    const { gameState, collectedCount } = useGameState()
    gameState.value = createGameState({ collected_fragments: ['f1', 'f2'] })

    expect(collectedCount.value).toBe(2)
  })

  it('totalFragments returns correct count', () => {
    const { gameState, totalFragments } = useGameState()
    gameState.value = createGameState({
      fragment_states: {
        f1: { id: 'f1', name: '一', scene: 'scene_1972', collected: false, revealed: false },
        f2: { id: 'f2', name: '二', scene: 'scene_1972', collected: false, revealed: false },
        f3: { id: 'f3', name: '三', scene: 'scene_1972', collected: false, revealed: false },
      },
    })

    expect(totalFragments.value).toBe(3)
  })
})
