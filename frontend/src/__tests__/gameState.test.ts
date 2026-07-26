import { beforeEach, describe, expect, it } from 'vitest'
import { StateRevisionError, useGameState } from '../composables/useGameState'
import type { GameState } from '../types/game'

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

  it('replaces the complete authoritative state without sharing nested references', () => {
    const { gameState, replaceAuthoritativeState } = useGameState()
    const nextState = createGameState({
      revision: 7,
      visited_scenes: ['scene_1972', 'scene_1990'],
      dialogue_history: [
        { role: 'player', content: '你还记得吗？' },
        {
          role: 'npc',
          npc_id: 'chen_shouyi_1990',
          content: '记得那张南下的车票。',
        },
      ],
    })

    replaceAuthoritativeState(nextState)
    nextState.visited_scenes.push('scene_2024')

    expect(gameState.value?.revision).toBe(7)
    expect(gameState.value?.visited_scenes).toEqual(['scene_1972', 'scene_1990'])
    expect(gameState.value?.dialogue_history.map((message) => message.role)).toEqual([
      'player',
      'npc',
    ])
  })

  it('rejects an older same-game snapshot', () => {
    const { gameState, replaceAuthoritativeState } = useGameState()
    gameState.value = createGameState({ revision: 5 })

    expect(() => replaceAuthoritativeState(createGameState({ revision: 4 }))).toThrow(
      StateRevisionError,
    )
    expect(gameState.value.revision).toBe(5)
  })

  it('accepts a loaded snapshot from a different game', () => {
    const { gameState, replaceAuthoritativeState } = useGameState()
    gameState.value = createGameState({ revision: 5 })

    replaceAuthoritativeState(
      createGameState({
        game_id: '00000000-0000-0000-0000-000000000002',
        revision: 1,
        current_scene: 'scene_1990',
      }),
    )

    expect(gameState.value.game_id).toBe('00000000-0000-0000-0000-000000000002')
    expect(gameState.value.current_scene).toBe('scene_1990')
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
        f1: {
          id: 'f1',
          name: '一',
          scene: 'scene_1972',
          status: 'hidden',
          collected: false,
          revealed: false,
        },
        f2: {
          id: 'f2',
          name: '二',
          scene: 'scene_1972',
          status: 'hidden',
          collected: false,
          revealed: false,
        },
        f3: {
          id: 'f3',
          name: '三',
          scene: 'scene_1972',
          status: 'hidden',
          collected: false,
          revealed: false,
        },
      },
    })

    expect(totalFragments.value).toBe(3)
  })
})
