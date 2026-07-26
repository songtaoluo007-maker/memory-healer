import { computed, ref } from 'vue'
import { getSceneView } from '../api'
import type { GameState, SceneView } from '../types/game'

const sceneView = ref<SceneView | null>(null)
const narrativeText = ref('')
const sceneTransitioning = ref(false)

export function useScene() {
  const currentScene = computed(() => sceneView.value?.scene ?? null)
  const currentNpcs = computed(() => sceneView.value?.npcs ?? [])
  const sceneFragments = computed(() => sceneView.value?.fragments ?? [])
  const choices = computed(() => sceneView.value?.choices ?? [])

  const replaceSceneView = (nextView: SceneView) => {
    sceneView.value = structuredClone(nextView)
    narrativeText.value = nextView.scene.description
  }

  async function loadScene(gameState: GameState | null): Promise<SceneView | null> {
    if (!gameState) return null
    const requestedScene = gameState.current_scene
    const response = await getSceneView(gameState)
    if (response.data.scene.id !== requestedScene) {
      throw new Error(`场景响应不匹配：请求 ${requestedScene}，收到 ${response.data.scene.id}`)
    }
    replaceSceneView(response.data)
    return response.data
  }

  return {
    sceneView,
    currentScene,
    currentNpcs,
    sceneFragments,
    choices,
    narrativeText,
    sceneTransitioning,
    replaceSceneView,
    loadScene,
  }
}
