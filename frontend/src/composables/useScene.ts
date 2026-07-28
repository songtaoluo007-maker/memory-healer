import { computed, onUnmounted, ref, watch } from 'vue'
import { getFixedVoiceLine, getSceneView } from '../api'
import type { useVoicePlayback } from './useVoicePlayback'
import type {
  GameState,
  Hypothesis,
  NpcSummary,
  Scene,
  SceneFragment,
  SceneView,
  VoiceResponse,
} from '../types/game'

const sceneView = ref<SceneView | null>(null)
const narrativeText = ref('')
const sceneTransitioning = ref(false)

type VoicePlayback = Pick<
  ReturnType<typeof useVoicePlayback>,
  | 'activeCue'
  | 'currentLineId'
  | 'playResponse'
  | 'resumeAfterUserGesture'
  | 'stop'
  | 'waitingForUserGesture'
>

type FixedLineLookup = (lineId: string) => Promise<{ data: VoiceResponse }>

export function createSceneVoiceIntegration(
  voice: VoicePlayback,
  getFixedLine: FixedLineLookup = getFixedVoiceLine,
) {
  const playedLines = new Set<string>()
  let requestGeneration = 0

  const playFixedVoice = async (
    lineId: string | null | undefined,
    priority: 'critical' | 'dialogue' | 'narration',
  ) => {
    if (!lineId || playedLines.has(lineId)) return false
    playedLines.add(lineId)
    const requestedGeneration = ++requestGeneration
    try {
      const response = await getFixedLine(lineId)
      if (requestedGeneration !== requestGeneration) return false
      return await voice.playResponse(response.data, priority)
    } catch {
      return false
    }
  }

  const stopForSceneTransition = () => {
    requestGeneration += 1
    voice.stop()
  }

  return {
    subtitleCue: computed(() => (voice.currentLineId.value ? voice.activeCue.value : null)),
    playSceneEntry: (scene: Scene) =>
      playFixedVoice(scene.transition_in_voice_line_id, 'narration'),
    playNpcIntro: (npc: NpcSummary) =>
      playFixedVoice(npc.initial_voice_line_id, 'dialogue'),
    playFragmentMemory: (fragment: SceneFragment) =>
      playFixedVoice(fragment.memory_voice_line_id, 'narration'),
    playHypothesisResolution: (hypothesis: Hypothesis) =>
      playFixedVoice(hypothesis.resolution_voice_line_id, 'critical'),
    stopForSceneTransition,
  }
}

export function useVoiceRouteLifecycle(voice: VoicePlayback) {
  const removeGestureListeners = () => {
    window.removeEventListener('pointerdown', resumePendingVoice, true)
    window.removeEventListener('keydown', resumePendingVoice, true)
  }
  const resumePendingVoice = () => {
    if (voice.waitingForUserGesture.value) {
      removeGestureListeners()
      void voice.resumeAfterUserGesture()
    }
  }

  watch(
    voice.waitingForUserGesture,
    (waiting) => {
      removeGestureListeners()
      if (waiting) {
        window.addEventListener('pointerdown', resumePendingVoice, true)
        window.addEventListener('keydown', resumePendingVoice, true)
      }
    },
    { flush: 'sync', immediate: true },
  )

  onUnmounted(() => {
    removeGestureListeners()
    voice.stop()
  })
}

export function useScene() {
  const currentScene = computed(() => sceneView.value?.scene ?? null)
  const currentNpcs = computed(() => sceneView.value?.npcs ?? [])
  const sceneFragments = computed(() => sceneView.value?.fragments ?? [])
  const choices = computed(() => sceneView.value?.choices ?? [])
  const hypotheses = computed(() => sceneView.value?.hypotheses ?? [])

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
    hypotheses,
    narrativeText,
    sceneTransitioning,
    replaceSceneView,
    loadScene,
  }
}
