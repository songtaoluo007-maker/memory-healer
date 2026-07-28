import { computed, ref } from 'vue'
import * as api from '../api'
import type { ActionResult, DialogueResponse, GameState, NewGameResponse } from '../types/game'

const gameState = ref<GameState | null>(null)
const loading = ref(false)
const error = ref('')
const saveRevisions = ref<Record<number, number>>({})

export class StateRevisionError extends Error {
  readonly incomingRevision: number
  readonly currentRevision: number

  constructor(incomingRevision: number, currentRevision: number) {
    super(`忽略过期游戏状态：响应版本 ${incomingRevision}，当前版本 ${currentRevision}`)
    this.name = 'StateRevisionError'
    this.incomingRevision = incomingRevision
    this.currentRevision = currentRevision
  }
}

function currentState(): GameState {
  if (!gameState.value) {
    throw new Error('游戏尚未初始化')
  }
  return gameState.value
}

export function useGameState() {
  const replaceAuthoritativeState = (nextState: GameState) => {
    const current = gameState.value
    if (current && nextState.game_id === current.game_id && nextState.revision < current.revision) {
      const revisionError = new StateRevisionError(nextState.revision, current.revision)
      error.value = revisionError.message
      throw revisionError
    }
    gameState.value = structuredClone(nextState)
  }

  const initGame = async (): Promise<NewGameResponse | null> => {
    loading.value = true
    error.value = ''
    try {
      const response = await api.getNewGame()
      replaceAuthoritativeState(response.data.state)
      return response.data
    } catch (caught: unknown) {
      error.value = (caught as Error).message || '初始化失败'
      return null
    } finally {
      loading.value = false
    }
  }

  const loadFromSlot = async (slotId: number): Promise<GameState | null> => {
    loading.value = true
    error.value = ''
    try {
      const response = await api.loadGame(slotId)
      replaceAuthoritativeState(response.data.game_state)
      saveRevisions.value[slotId] = response.data.save_revision
      return response.data.game_state
    } catch (caught: unknown) {
      error.value = (caught as Error).message || '存档加载失败'
      return null
    } finally {
      loading.value = false
    }
  }

  const saveToSlot = async (slotId: number, slotName: string) => {
    const state = currentState()
    if (saveRevisions.value[slotId] === undefined) {
      const response = await api.listSaves()
      const existing = response.data.saves.find((slot) => slot.slot_id === slotId)
      saveRevisions.value[slotId] = existing?.save_revision ?? 0
    }
    const response = await api.saveGame(slotId, slotName, state, saveRevisions.value[slotId] ?? 0)
    saveRevisions.value[slotId] = response.data.save_revision
    return response.data
  }

  const applyActionResult = (result: ActionResult): ActionResult => {
    replaceAuthoritativeState(result.state)
    return result
  }

  const exploreHotspot = async (hotspotId: string): Promise<ActionResult> => {
    const state = currentState()
    const response = await api.exploreHotspot(hotspotId, state, state.revision)
    return applyActionResult(response.data)
  }

  const submitChoice = async (choiceId: string): Promise<ActionResult> => {
    const state = currentState()
    const response = await api.recordChoice(choiceId, state, state.revision)
    return applyActionResult(response.data)
  }

  const confirmHypothesis = async (
    hypothesisId: string,
    evidenceIds: string[],
  ): Promise<ActionResult> => {
    const state = currentState()
    const response = await api.confirmHypothesis(
      hypothesisId,
      evidenceIds,
      state,
      state.revision,
    )
    return applyActionResult(response.data)
  }

  const sendDialogue = async (npcId: string, playerInput: string): Promise<DialogueResponse> => {
    const state = currentState()
    const response = await api.chatWithNpc({
      npc_id: npcId,
      player_input: playerInput,
      game_state: state,
      expected_revision: state.revision,
    })
    replaceAuthoritativeState(response.data.state)
    return response.data
  }

  const collectedCount = computed(() => gameState.value?.collected_fragments.length || 0)
  const totalFragments = computed(() => Object.keys(gameState.value?.fragment_states || {}).length)

  return {
    gameState,
    loading,
    error,
    saveRevisions,
    replaceAuthoritativeState,
    initGame,
    loadFromSlot,
    saveToSlot,
    exploreHotspot,
    confirmHypothesis,
    submitChoice,
    sendDialogue,
    collectedCount,
    totalFragments,
  }
}
