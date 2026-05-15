import { ref, computed } from 'vue'
import * as api from '../api'
import type { GameState } from '../types/game'

const gameState = ref<GameState | null>(null)
const loading = ref(false)
const error = ref('')

export function useGameState() {
  const initGame = async () => {
    loading.value = true
    try {
      const res = await api.getInitialState()
      gameState.value = res.data
    } catch (e: unknown) {
      error.value = (e as Error).message || '初始化失败'
    } finally {
      loading.value = false
    }
  }

  const loadFromSlot = async (slotId: number) => {
    loading.value = true
    try {
      const res = await api.loadGame(slotId)
      gameState.value = res.data.game_state
    } catch {
      error.value = '存档加载失败'
    } finally {
      loading.value = false
    }
  }

  const saveToSlot = async (slotId: number, slotName: string) => {
    if (!gameState.value) return
    await api.saveGame(slotId, slotName, gameState.value, gameState.value.current_scene, gameState.value.play_time)
  }

  const updateTrust = (npcId: string, change: number) => {
    if (!gameState.value) return
    const current = gameState.value.npc_trust[npcId] || 30
    gameState.value.npc_trust[npcId] = Math.max(0, Math.min(100, current + change))
  }

  const collectFragment = (fragmentId: string) => {
    if (!gameState.value) return
    if (!gameState.value.collected_fragments.includes(fragmentId)) {
      gameState.value.collected_fragments.push(fragmentId)
    }
    if (gameState.value.fragment_states[fragmentId]) {
      gameState.value.fragment_states[fragmentId].collected = true
    }
  }

  const revealFragment = (fragmentId: string) => {
    if (!gameState.value) return
    if (!gameState.value.revealed_fragments.includes(fragmentId)) {
      gameState.value.revealed_fragments.push(fragmentId)
    }
    if (gameState.value.fragment_states[fragmentId]) {
      gameState.value.fragment_states[fragmentId].revealed = true
    }
  }

  const addDialogue = (role: string, content: string) => {
    if (!gameState.value) return
    gameState.value.dialogue_history.push({ role, content })
  }

  const changeScene = (sceneId: string) => {
    if (!gameState.value) return
    gameState.value.current_scene = sceneId
  }

  const collectedCount = computed(() => gameState.value?.collected_fragments.length || 0)
  const totalFragments = computed(() => Object.keys(gameState.value?.fragment_states || {}).length)

  return {
    gameState,
    loading,
    error,
    initGame,
    loadFromSlot,
    saveToSlot,
    updateTrust,
    collectFragment,
    revealFragment,
    addDialogue,
    changeScene,
    collectedCount,
    totalFragments,
  }
}
