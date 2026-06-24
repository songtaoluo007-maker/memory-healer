import { ref } from 'vue'
import { getSceneDetail, advanceNarrative } from '../api'
import type { Scene, NpcSummary, Fragment } from '../types/game'

export function useScene() {
  const currentScene = ref<Scene | null>(null)
  const currentNpcs = ref<NpcSummary[]>([])
  const sceneFragments = ref<Array<Fragment & { is_collected: boolean }>>([])
  const narrativeText = ref('')
  const sceneTransitioning = ref(false)

  async function loadScene(gameState: any): Promise<string> {
    if (!gameState) return ''
    const res = await getSceneDetail(gameState.current_scene, gameState)
    currentScene.value = res.data.scene
    currentNpcs.value = res.data.npcs || []
    sceneFragments.value = (res.data.fragments || []).map((f: Fragment) => ({
      ...f,
      is_collected: gameState.collected_fragments?.includes(f.id),
    }))

    const narrRes = await advanceNarrative('进入场景', gameState)
    let sceneDesc = narrRes.data.scene_description

    const butterflyMods = res.data.butterfly_mods || []
    if (butterflyMods.length > 0) {
      const modDescs = butterflyMods
        .filter((m: any) => m.mod_type === 'scene_description')
        .map((m: any) => m.mod_value)
      if (modDescs.length > 0) {
        sceneDesc += '\n\n' + modDescs.join('\n')
      }
    }

    narrativeText.value = sceneDesc
    return sceneDesc
  }

  async function switchScene(
    targetScene: string,
    gameState: any,
    emit: (e: 'scene-change', v: string) => void,
    playSFX: (s: string) => void,
    playBGM: (m: string) => void,
    typeStart: (t: string) => void
  ) {
    if (!gameState || sceneTransitioning.value) return
    sceneTransitioning.value = true
    playSFX('scene_transition')

    const scenes = gameState.scenes_visited || []
    if (!scenes.includes(gameState.current_scene)) {
      scenes.push(gameState.current_scene)
    }

    emit('scene-change', targetScene)
    gameState.current_scene = targetScene

    await new Promise(r => setTimeout(r, 200))
    const desc = await loadScene(gameState)
    if (desc) typeStart(desc)
    playBGM(gameState.current_scene.replace('scene_', ''))
    sceneTransitioning.value = false
  }

  return {
    currentScene,
    currentNpcs,
    sceneFragments,
    narrativeText,
    sceneTransitioning,
    loadScene,
    switchScene,
  }
}
