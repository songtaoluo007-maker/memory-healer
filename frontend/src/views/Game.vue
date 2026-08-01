<script setup lang="ts">
import {
  computed,
  defineAsyncComponent,
  nextTick,
  onBeforeUnmount,
  onMounted,
  ref,
  watch,
} from 'vue'
import { evaluateEnding } from '../api'
import { useAudioMixer } from '../audio/mixer'
import { useGameState } from '../composables/useGameState'
import { useHotspots } from '../composables/useHotspots'
import { useI18n } from '../composables/useI18n'
import { useMusicBus } from '../composables/useMusicBus'
import {
  createSceneVoiceIntegration,
  useScene,
  useVoiceRouteLifecycle,
} from '../composables/useScene'
import { useSfxBus } from '../composables/useSfxBus'
import { useTypewriter } from '../composables/useTypewriter'
import { useVoicePlayback } from '../composables/useVoicePlayback'
import { useUiStore, type CinematicOverlay } from '../stores/ui'
import FragmentArtwork from '../components/FragmentArtwork.vue'
import VoiceControls from '../components/VoiceControls.vue'
import VoiceSubtitle from '../components/VoiceSubtitle.vue'
import { getFragmentPresentation } from '../stage/fragmentPresentation'
import {
  isChoiceUnlocked,
  isSceneDecisionUnlocked,
  resolveHypothesisSubmission,
  useMemoryReasoningSelection,
} from '../domain/memoryReasoning'
import type {
  ChatMessage,
  Choice,
  DialogueResponse,
  EndingType,
  Fragment,
  Hotspot,
  NpcSummary,
} from '../types/game'

const SceneIllustration = defineAsyncComponent(() => import('../components/SceneIllustration.vue'))
const CinematicStage = defineAsyncComponent(() => import('../components/CinematicStage.vue'))
const NpcAvatar = defineAsyncComponent(() => import('../components/NpcAvatar.vue'))
const HotspotOverlay = defineAsyncComponent(() => import('../components/HotspotOverlay.vue'))
const MemoryReasoningPanel = defineAsyncComponent(
  () => import('../components/MemoryReasoningPanel.vue'),
)
const SceneTransition = defineAsyncComponent(() => import('../components/SceneTransition.vue'))
const ButterflyPanel = defineAsyncComponent(() => import('../components/ButterflyPanel.vue'))
const StoryLog = defineAsyncComponent(() => import('../components/StoryLog.vue'))
const SceneTimeline = defineAsyncComponent(() => import('../components/SceneTimeline.vue'))
const MemoryPanel = defineAsyncComponent(() => import('../components/MemoryPanel.vue'))
const InventoryPanel = defineAsyncComponent(() => import('../components/InventoryPanel.vue'))
const ChatPanel = defineAsyncComponent(() => import('../components/ChatPanel.vue'))

const emit = defineEmits<{ ending: [type: EndingType] }>()
const props = defineProps<{ loadSlotId?: number | null }>()

const {
  gameState,
  initGame,
  loadFromSlot,
  saveToSlot,
  exploreHotspot,
  confirmHypothesis: confirmMemoryHypothesis,
  submitChoice,
  collectedCount,
  totalFragments,
} = useGameState()
const {
  sceneView,
  currentScene,
  currentNpcs,
  sceneFragments,
  choices,
  activeConsequence,
  narrativeText,
  sceneTransitioning,
  replaceSceneView,
  loadScene: loadSceneData,
} = useScene()
const {
  currentSceneHypotheses,
  activeHypothesis,
  selectedHypothesisId,
  selectedEvidenceIds,
  rejectedFeedback,
  selectHypothesis,
  toggleEvidence,
} = useMemoryReasoningSelection(sceneView)
const {
  displayText: typewriterText,
  isTyping,
  start: typeStart,
  skip: typeSkip,
} = useTypewriter(25)
const { playBGM } = useMusicBus()
const { playSFX } = useSfxBus()
const { isMuted, toggleMute, voiceVolume, setVoiceVolume } = useAudioMixer()
const voice = useVoicePlayback()
const sceneVoice = createSceneVoiceIntegration(voice)
useVoiceRouteLifecycle(voice, sceneVoice.cancelPending)
const { lang, toggleLang } = useI18n()
const ui = useUiStore()
const { hotspots, exploredIds, markExplored, explorationProgress } = useHotspots(
  computed(() => sceneView.value),
)

const selectedNpc = ref<NpcSummary | null>(null)
const showFragmentPopup = ref(false)
const popupFragment = ref<(Fragment & { just_collected: boolean }) | null>(null)
const popupPresentation = computed(() =>
  popupFragment.value ? getFragmentPresentation(popupFragment.value.id) : null,
)
const actionPending = ref(false)
const scanMode = ref(false)
const gameRoot = ref<HTMLElement | null>(null)
const scanReturnButton = ref<HTMLButtonElement | null>(null)
const voiceControlsOpen = ref(false)
const mounted = ref(false)
const endingPending = ref(false)
const dialogueTaskFeedback = ref<{ npcId: string; message: string } | null>(null)
const chatPanelRef = ref<{
  clearHistory: () => void
  stopVoice: () => void
  chatHistory: ChatMessage[]
} | null>(null)
const reasoningObscured = computed(
  () =>
    Boolean(selectedNpc.value) ||
    showFragmentPopup.value ||
    Boolean(ui.activeOverlay) ||
    actionPending.value ||
    sceneTransitioning.value,
)
const canEnterScanMode = computed(() => Boolean(activeHypothesis.value) && !reasoningObscured.value)
const hypothesisConfirmed = computed(() => {
  if (!activeHypothesis.value || !gameState.value) return false
  return (
    gameState.value.confirmed_hypotheses?.[gameState.value.current_scene] ===
    activeHypothesis.value.id
  )
})
const unlockedChoices = computed(() => {
  const state = gameState.value
  return state ? choices.value.filter((choice) => isChoiceUnlocked(choice, state)) : []
})
const decisionUnlocked = computed(() =>
  gameState.value
    ? isSceneDecisionUnlocked(gameState.value.current_scene, choices.value, gameState.value)
    : false,
)
const suggestedPrompts = computed(() => {
  if (!selectedNpc.value || !gameState.value) return []
  return sceneFragments.value
    .filter(
      (fragment) =>
        fragment.unlock_method === 'dialogue' &&
        fragment.unlock_npc_id === selectedNpc.value?.id &&
        Boolean(fragment.dialogue_prompt) &&
        !gameState.value?.collected_fragments.includes(fragment.id),
    )
    .map((fragment) => ({
      fragmentId: fragment.id,
      name: fragment.name,
      text: fragment.dialogue_prompt as string,
    }))
})

const autoSave = async () => {
  if (!gameState.value) return
  if (!localStorage.getItem('mh_user')) return
  try {
    await saveToSlot(0, '自动存档')
  } catch {
    // 自动存档属于增强能力，不阻断主流程。
  }
}

const restoreAuthoritativeReasoning = () => {
  const state = gameState.value
  if (!state) return
  const confirmedId = state.confirmed_hypotheses?.[state.current_scene]
  if (!confirmedId) return
  const confirmed = currentSceneHypotheses.value.find((candidate) => candidate.id === confirmedId)
  if (!confirmed) return
  selectHypothesis(confirmed.id)
  selectedEvidenceIds.value = confirmed.evidence_ids.filter((evidenceId) =>
    state.collected_fragments.includes(evidenceId),
  )
}

const presentScene = () => {
  if (!currentScene.value || !gameState.value) return
  restoreAuthoritativeReasoning()
  narrativeText.value = [currentScene.value.description, activeConsequence.value?.scene_text]
    .filter(Boolean)
    .join('\n\n')
  typeStart(narrativeText.value)
  playBGM(gameState.value.current_scene)
  void sceneVoice.playSceneEntry(currentScene.value)
}

const loadCurrentScene = async () => {
  if (!gameState.value) return
  sceneTransitioning.value = true
  try {
    await loadSceneData(gameState.value)
    presentScene()
  } catch (caught: unknown) {
    narrativeText.value = (caught as Error).message || '记忆场景暂时无法载入。'
    typeStart(narrativeText.value)
  } finally {
    window.setTimeout(() => {
      sceneTransitioning.value = false
    }, 450)
  }
}

const selectNpc = (npc: NpcSummary, playIntro = true, taskFeedback: string | null = null) => {
  dialogueTaskFeedback.value = taskFeedback ? { npcId: npc.id, message: taskFeedback } : null
  if (selectedNpc.value?.id === npc.id && playIntro) return
  if (chatPanelRef.value) {
    chatPanelRef.value.stopVoice()
  } else {
    sceneVoice.cancelPending()
  }
  selectedNpc.value = npc
  ui.setStageMode('dialogue')
  playSFX('dialogue_start')
  if (playIntro) void sceneVoice.playNpcIntro(npc)
}

const closeDialogue = () => {
  if (chatPanelRef.value) {
    chatPanelRef.value.stopVoice()
  } else {
    sceneVoice.cancelPending()
  }
  selectedNpc.value = null
  dialogueTaskFeedback.value = null
  ui.setStageMode('observe')
}

const toggleOverlay = (overlay: CinematicOverlay) => {
  if (ui.activeOverlay === overlay) {
    ui.closeOverlay(overlay)
  } else {
    ui.openOverlay(overlay)
  }
}

const closeFragment = () => {
  showFragmentPopup.value = false
  ui.setStageMode(selectedNpc.value ? 'dialogue' : 'observe')
}

const focusReasoningAction = () => {
  void nextTick(() => {
    gameRoot.value?.querySelector<HTMLButtonElement>('.scan-action')?.focus()
  })
}

const enterScanMode = () => {
  if (scanMode.value || !canEnterScanMode.value) return
  scanMode.value = true
  void nextTick(() => scanReturnButton.value?.focus())
}

const exitScanMode = (restoreReasoningFocus = false) => {
  if (!scanMode.value) return
  scanMode.value = false
  if (restoreReasoningFocus) focusReasoningAction()
}

const toggleScanMode = () => {
  if (scanMode.value) {
    exitScanMode(true)
  } else {
    enterScanMode()
  }
}

const handleScanKeydown = (event: KeyboardEvent) => {
  if (!scanMode.value || event.key !== 'Escape') return
  event.preventDefault()
  exitScanMode(true)
}

const fragmentForPopup = (fragmentId: string): Fragment | null => {
  const fragment = sceneFragments.value.find((candidate) => candidate.id === fragmentId)
  if (!fragment) return null
  return {
    id: fragment.id,
    name: fragment.name,
    scene: fragment.scene,
    description: fragment.description,
    unlock_method: fragment.unlock_method,
    unlock_hint: fragment.unlock_hint,
    memory_text: fragment.memory_text,
    collected: gameState.value?.collected_fragments.includes(fragment.id) ?? false,
  }
}

const handleExplore = async (hotspot: Hotspot) => {
  exitScanMode()
  if (actionPending.value) return
  actionPending.value = true
  try {
    const result = await exploreHotspot(hotspot.id)
    const lockedEvent = result.events.find((event) => event.type === 'fragment.locked')
    if (lockedEvent) {
      const fragment = lockedEvent.content_id
        ? sceneFragments.value.find((candidate) => candidate.id === lockedEvent.content_id)
        : null
      const payload = lockedEvent.payload as {
        hint?: string
        method?: string
        minimum_trust?: number
        npc_id?: string
      }
      const hint = payload.hint ?? fragment?.unlock_hint ?? '这段记忆仍被防备遮住。'
      narrativeText.value = hint
      typeStart(hint)
      const npcId = payload.npc_id ?? fragment?.unlock_npc_id ?? hotspot.npc_id
      const minimumTrust = payload.minimum_trust ?? fragment?.minimum_trust
      const currentTrust = npcId ? gameState.value?.npc_trust[npcId] : undefined
      const method = payload.method === 'trust' ? '信任门槛' : (payload.method ?? '解锁条件')
      const feedback = [
        hint,
        method,
        typeof currentTrust === 'number' && typeof minimumTrust === 'number'
          ? `当前 ${currentTrust} / 需要 ${minimumTrust}`
          : typeof minimumTrust === 'number'
            ? `需要 ${minimumTrust}`
            : '',
      ]
        .filter(Boolean)
        .join(' · ')
      if (npcId) {
        const npc = currentNpcs.value.find((candidate) => candidate.id === npcId)
        if (npc) selectNpc(npc, true, feedback)
      }
      return
    }
    markExplored(hotspot.id)
    playSFX('explore')
    narrativeText.value = hotspot.label
    typeStart(hotspot.label)

    const collectedEvent = result.events.find((event) => event.type === 'fragment.collected')
    let collectedFragment: (typeof sceneFragments.value)[number] | null = null
    if (collectedEvent?.content_id) {
      if (
        activeHypothesis.value?.evidence_ids.includes(collectedEvent.content_id) &&
        !selectedEvidenceIds.value.includes(collectedEvent.content_id)
      ) {
        selectedEvidenceIds.value = [...selectedEvidenceIds.value, collectedEvent.content_id]
      }
      const fragment = fragmentForPopup(collectedEvent.content_id)
      if (fragment) {
        playSFX('fragment_found')
        popupFragment.value = { ...fragment, just_collected: true }
        showFragmentPopup.value = true
        ui.setStageMode('fragment')
        collectedFragment =
          sceneFragments.value.find((candidate) => candidate.id === fragment.id) ?? null
      }
    }
    let interactionNpc: NpcSummary | null = null
    if (hotspot.npc_id) {
      const npc = currentNpcs.value.find((candidate) => candidate.id === hotspot.npc_id)
      if (npc) {
        interactionNpc = npc
        selectNpc(npc, collectedFragment === null)
      }
    }
    if (collectedFragment) {
      void sceneVoice.playInteractionVoice(collectedFragment, interactionNpc)
    }
    void autoSave()
  } catch (caught: unknown) {
    narrativeText.value = (caught as Error).message || '这段记忆暂时无法触碰。'
    typeStart(narrativeText.value)
  } finally {
    actionPending.value = false
  }
}

const toggleReasoningEvidence = (evidenceId: string) => {
  if (!gameState.value) return
  toggleEvidence(evidenceId, gameState.value.collected_fragments, hypothesisConfirmed.value)
}

const handleConfirmHypothesis = async () => {
  if (!activeHypothesis.value || actionPending.value || hypothesisConfirmed.value) return
  const hypothesis = activeHypothesis.value
  actionPending.value = true
  try {
    const result = await confirmMemoryHypothesis(hypothesis.id, selectedEvidenceIds.value)
    const submission = resolveHypothesisSubmission(result.events, hypothesis.id)
    if (submission.status === 'rejected') {
      const feedback = submission.feedback ?? '这些证据还不能支持这项解释。'
      rejectedFeedback.value = feedback
      narrativeText.value = feedback
      typeStart(feedback)
      return
    }
    if (submission.status !== 'confirmed') return
    rejectedFeedback.value = null
    playSFX('fragment_found')
    narrativeText.value = hypothesis.resolution
    typeStart(hypothesis.resolution)
    void sceneVoice.playHypothesisResolution(hypothesis)
    void autoSave()
  } catch (caught: unknown) {
    narrativeText.value = (caught as Error).message || '这些证据还无法形成可靠的解释。'
    typeStart(narrativeText.value)
  } finally {
    actionPending.value = false
  }
}

const showEnding = async () => {
  if (!gameState.value || endingPending.value) return
  endingPending.value = true
  try {
    const { data } = await evaluateEnding(gameState.value)
    narrativeText.value = data.ending.description
    typeStart(narrativeText.value)
    playSFX(`ending_${data.ending.id}`)
    window.setTimeout(() => emit('ending', data.ending.id), 4200)
  } catch (caught: unknown) {
    narrativeText.value = (caught as Error).message || '结局仍在记忆雾中。'
    typeStart(narrativeText.value)
  } finally {
    endingPending.value = false
  }
}

const handleChoice = async (choice: Choice) => {
  if (actionPending.value) return
  actionPending.value = true
  const previousScene = gameState.value?.current_scene
  try {
    if (choice.target_scene) sceneVoice.stopForSceneTransition()
    await submitChoice(choice.id)
    playSFX('scene_transition')
    narrativeText.value = choice.label
    typeStart(choice.label)
    void autoSave()
    if (!choice.target_scene && gameState.value?.current_scene === 'scene_2089') {
      await showEnding()
    } else if (previousScene === gameState.value?.current_scene) {
      await loadCurrentScene()
    }
  } catch (caught: unknown) {
    narrativeText.value = (caught as Error).message || '这项选择没有被记忆接受。'
    typeStart(narrativeText.value)
  } finally {
    actionPending.value = false
  }
}

const navigateTimeline = (targetScene: string) => {
  if (targetScene === gameState.value?.current_scene) return
  const routeChoice = choices.value.find((choice) => choice.target_scene === targetScene)
  if (routeChoice) {
    void handleChoice(routeChoice)
    return
  }
  narrativeText.value = '记忆只能沿着当前因果继续，无法从这里直接跳转。'
  typeStart(narrativeText.value)
}

const onDialogueComplete = (
  result: DialogueResponse,
  newlyCollected: boolean,
  sourceNpcId: string,
) => {
  if (selectedNpc.value?.id !== sourceNpcId) return
  dialogueTaskFeedback.value = null
  if (
    newlyCollected &&
    result.fragment_revealed &&
    gameState.value?.collected_fragments.includes(result.fragment_revealed) &&
    activeHypothesis.value?.evidence_ids.includes(result.fragment_revealed) &&
    !selectedEvidenceIds.value.includes(result.fragment_revealed)
  ) {
    selectedEvidenceIds.value = [...selectedEvidenceIds.value, result.fragment_revealed]
  }
  if (newlyCollected && result.fragment_revealed && result.fragment_data) {
    popupFragment.value = {
      ...result.fragment_data,
      collected: gameState.value?.collected_fragments.includes(result.fragment_revealed) ?? false,
      just_collected: false,
    }
    showFragmentPopup.value = true
    void sceneVoice.playDialogueFragment(result.fragment_data)
  }
  void autoSave()
}

const getTrustLevel = (npcId: string) => {
  const trust = gameState.value?.npc_trust[npcId] ?? 30
  if (trust >= 80) return { label: '完全信任', color: '#4ade80' }
  if (trust >= 60) return { label: '比较信任', color: '#60a5fa' }
  if (trust >= 30) return { label: '初识', color: '#facc15' }
  return { label: '警惕', color: '#f87171' }
}

watch(
  () => gameState.value?.current_scene,
  async (nextScene, previousScene) => {
    if (!mounted.value || !nextScene || nextScene === previousScene) return
    closeDialogue()
    scanMode.value = false
    chatPanelRef.value?.clearHistory()
    await loadCurrentScene()
  },
)

watch(
  () => gameState.value?.collected_fragments.length,
  (count) => {
    if (!count) return
    void autoSave()
    if (count === totalFragments.value && gameState.value?.current_scene !== 'scene_2089') {
      narrativeText.value = '所有记忆碎片已经归位。沿着因果前往最后一幕吧。'
      typeStart(narrativeText.value)
    }
  },
)

onMounted(async () => {
  window.addEventListener('keydown', handleScanKeydown)
  ui.closeOverlay()
  ui.setStageMode('observe')
  sceneTransitioning.value = true
  if (props.loadSlotId != null) {
    await loadFromSlot(props.loadSlotId)
    await loadCurrentScene()
  } else {
    const initial = await initGame()
    if (initial) {
      replaceSceneView(initial.scene_view)
      presentScene()
    }
  }
  mounted.value = true
  sceneTransitioning.value = false
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', handleScanKeydown)
})
</script>

<template>
  <div
    v-if="gameState"
    ref="gameRoot"
    class="game game-cinema"
    :class="{
      'has-choices': choices.length > 0,
      'scan-active': scanMode,
      'voice-controls-open': voiceControlsOpen,
    }"
    :data-scan-mode="scanMode ? 'active' : 'inactive'"
    :data-stage-mode="ui.stageMode"
  >
    <Transition name="fade">
      <div v-if="sceneTransitioning" class="loading-overlay">
        <span class="loading-code">MEMORY FIELD / {{ gameState.current_scene }}</span>
        <div class="loading-line"><i /></div>
        <div class="loading-text">正在重组记忆</div>
      </div>
    </Transition>

    <div class="bg-layer">
      <CinematicStage
        :scene-id="gameState.current_scene"
        :active-npc-id="selectedNpc?.id ?? null"
        :consequence="activeConsequence"
      >
        <template #default>
          <SceneIllustration :scene-id="gameState.current_scene" />
        </template>
      </CinematicStage>
    </div>

    <div class="interaction-plane" :class="{ obscured: selectedNpc }">
      <HotspotOverlay
        :hotspots="hotspots"
        :explored-ids="exploredIds"
        :scene-id="gameState.current_scene"
        :scan-mode="scanMode"
        @explore="handleExplore"
      />
    </div>

    <div
      v-show="!scanMode"
      class="analysis-chrome"
      :inert="scanMode ? true : undefined"
      :aria-hidden="scanMode ? 'true' : undefined"
    >
      <aside
        v-if="activeConsequence"
        class="causal-echo"
        :data-consequence-variant="activeConsequence.variant"
        aria-label="因果回声"
      >
        <span class="causal-echo-kicker">CAUSAL ECHO / 因果回声</span>
        <p>{{ activeConsequence.scene_text }}</p>
      </aside>

      <header class="top-bar cinematic-hud" role="banner" aria-label="记忆场状态">
        <div class="brand-lockup" aria-label="拾忆">
          <span class="brand-mark">拾</span>
          <span class="brand-name">拾忆</span>
          <span class="brand-index">MEMORY HEALER</span>
        </div>
        <div class="scene-info">
          <span class="scene-eyebrow">CHAPTER 01 · MEMORY FIELD</span>
          <strong class="scene-title">{{ currentScene?.title || '正在载入' }}</strong>
          <span class="scene-meta">
            {{ currentScene?.time_period || '····' }}
            <i />
            {{ currentScene?.location || '未知坐标' }}
          </span>
        </div>
        <div class="status-right">
          <button
            class="hud-action compact"
            :title="lang === 'zh' ? 'Switch to English' : '切换到中文'"
            aria-label="语言切换"
            @click="toggleLang"
          >
            {{ lang === 'zh' ? 'EN' : '中' }}
          </button>
          <VoiceControls
            :is-speaking="voice.isSpeaking.value"
            :is-paused="voice.isPaused.value"
            :voice-volume="voiceVolume"
            :has-replay="Boolean(voice.lastRequest.value)"
            :is-muted="isMuted"
            @pause="voice.pause"
            @resume="voice.resume"
            @replay="voice.replay"
            @skip="voice.skip"
            @toggle-mute="toggleMute"
            @update:voice-volume="setVoiceVolume"
            @expanded-change="voiceControlsOpen = $event"
          />
          <button
            class="fragment-counter"
            type="button"
            aria-label="打开记忆碎片"
            @click="toggleOverlay('inventory')"
          >
            <span>碎片</span>
            <strong>{{ String(collectedCount).padStart(2, '0') }}</strong>
            <i>/</i>
            <span>{{ String(totalFragments).padStart(2, '0') }}</span>
          </button>
        </div>
      </header>

      <aside class="tool-rail" aria-label="记忆工具">
        <button type="button" @click="toggleOverlay('memory')">
          <span class="rail-glyph">档</span><small>档案</small>
        </button>
        <button type="button" @click="toggleOverlay('timeline')">
          <span class="rail-glyph">时</span><small>时序</small>
        </button>
        <button type="button" @click="toggleOverlay('butterfly')">
          <span class="rail-glyph">因</span><small>因果</small>
        </button>
        <button type="button" @click="toggleOverlay('story')">
          <span class="rail-glyph">录</span><small>记录</small>
        </button>
      </aside>

      <div
        v-if="activeHypothesis"
        class="reasoning-panel-host"
        :class="{ obscured: reasoningObscured }"
        :inert="reasoningObscured ? true : undefined"
        :aria-hidden="reasoningObscured ? 'true' : undefined"
      >
        <MemoryReasoningPanel
          :hypotheses="currentSceneHypotheses"
          :selected-hypothesis-id="selectedHypothesisId"
          :fragments="sceneFragments"
          :collected-ids="gameState.collected_fragments"
          :selected-ids="selectedEvidenceIds"
          :confirmed="hypothesisConfirmed"
          :pending="actionPending"
          :scan-mode="scanMode"
          :rejected-feedback="rejectedFeedback"
          @select-hypothesis="selectHypothesis"
          @toggle-evidence="toggleReasoningEvidence"
          @confirm="handleConfirmHypothesis"
          @toggle-scan="toggleScanMode"
        />
      </div>

      <div
        v-if="narrativeText"
        class="narrative-float"
        role="complementary"
        aria-label="叙事文本"
        aria-live="polite"
      >
        <span class="narrative-kicker">MEMORY TRANSCRIPT</span>
        <div class="narrative-text" @click="isTyping ? typeSkip() : null">
          {{ typewriterText }}<span v-if="isTyping" class="cursor">|</span>
        </div>
        <span v-if="isTyping" class="skip-hint">单击显现全文</span>
      </div>

      <VoiceSubtitle :cue="sceneVoice.subtitleCue.value" />

      <div class="npc-dock" role="toolbar" aria-label="NPC角色选择">
        <button
          v-for="npc in currentNpcs"
          :key="npc.id"
          class="npc-chip"
          :class="{ active: selectedNpc?.id === npc.id }"
          type="button"
          @click="selectNpc(npc)"
        >
          <NpcAvatar
            :npc-id="npc.id"
            :emotion="getTrustLevel(npc.id).label === '完全信任' ? 'happy' : 'neutral'"
            :size="36"
          />
          <div class="npc-chip-info">
            <span class="npc-chip-role">{{ npc.title }}</span>
            <span class="npc-chip-name">{{ npc.name }}</span>
            <div class="trust-bar-container">
              <div
                class="trust-bar"
                :style="{
                  width: (gameState.npc_trust[npc.id] || 0) + '%',
                  background: getTrustLevel(npc.id).color,
                }"
              />
            </div>
            <span class="npc-chip-trust" :style="{ color: getTrustLevel(npc.id).color }">
              {{ getTrustLevel(npc.id).label }}
            </span>
          </div>
        </button>
      </div>

      <div v-if="choices.length && decisionUnlocked" class="scene-nav" aria-label="剧情选择">
        <span class="choice-kicker">CAUSAL DECISION</span>
        <button
          v-for="(choice, index) in unlockedChoices"
          :key="choice.id"
          class="nav-btn"
          :disabled="actionPending"
          @click="handleChoice(choice)"
        >
          <span class="choice-index">0{{ index + 1 }}</span>
          <span>{{ choice.label }}</span>
          <span aria-hidden="true">→</span>
        </button>
      </div>
      <div v-else-if="choices.length" class="scene-nav choice-lock" aria-live="polite">
        <span class="choice-kicker">CAUSAL DECISION / 尚未开放</span>
        <div class="choice-lock-plate">
          <strong>先建立一条能够承担后果的解释</strong>
          <span>取得并连接本幕证据后，因果选择才会显现。</span>
        </div>
      </div>

      <div
        class="dialogue-float"
        :class="{ open: selectedNpc }"
        role="dialog"
        aria-label="NPC对话面板"
        aria-modal="false"
      >
        <div class="dialogue-glass">
          <div v-if="selectedNpc" class="dialogue-header">
            <div>
              <span class="dialogue-kicker">LIVE MEMORY / {{ selectedNpc.title }}</span>
              <strong>{{ selectedNpc.name }}</strong>
            </div>
            <button class="close-btn" aria-label="结束对话" @click="closeDialogue">结束对话</button>
          </div>
          <div v-else class="dialogue-header">
            <span>选择人物，进入这段记忆</span>
          </div>
          <ChatPanel
            ref="chatPanelRef"
            :selected-npc="selectedNpc"
            :game-state="gameState"
            :suggested-prompts="suggestedPrompts"
            :task-feedback="dialogueTaskFeedback"
            :voice-playback="voice"
            :voice-coordinator="sceneVoice"
            @dialogue-complete="onDialogueComplete"
          />
        </div>
      </div>

      <div class="exploration-meter" aria-label="场景探索进度">
        <span>{{ explorationProgress === 100 ? '场景已校准' : '场景校准中' }}</span>
        <i><b :style="{ width: `${explorationProgress}%` }" /></i>
        <strong>{{ String(explorationProgress).padStart(2, '0') }}%</strong>
      </div>
    </div>

    <button
      v-if="scanMode"
      ref="scanReturnButton"
      class="scan-return"
      type="button"
      aria-label="返回推理模式"
      aria-keyshortcuts="Escape"
      @click="exitScanMode(true)"
    >
      <span class="scan-return-mark" aria-hidden="true">←</span>
      <strong>返回推理</strong>
      <small>ESC</small>
    </button>

    <SceneTransition :active="sceneTransitioning" :scene-id="gameState.current_scene" />

    <div
      v-if="showFragmentPopup"
      class="popup-overlay"
      role="dialog"
      aria-label="记忆碎片"
      aria-modal="true"
      @click.self="closeFragment"
    >
      <div class="fragment-popup">
        <span class="fragment-serial">ARCHIVE / {{ popupFragment?.id }}</span>
        <FragmentArtwork v-if="popupPresentation" :presentation="popupPresentation" />
        <div v-else class="popup-icon" aria-hidden="true"><i /></div>
        <h3>{{ popupFragment?.just_collected ? '记忆已归档' : '发现记忆线索' }}</h3>
        <h2>{{ popupFragment?.name }}</h2>
        <p class="fragment-desc">{{ popupFragment?.description }}</p>
        <p v-if="popupFragment?.memory_text" class="fragment-memory">
          「{{ popupFragment.memory_text }}」
        </p>
        <button class="btn-close" @click="closeFragment">
          {{ popupFragment?.just_collected ? '继续探索' : '记住这条线索' }}
        </button>
      </div>
    </div>

    <InventoryPanel
      v-if="ui.activeOverlay === 'inventory'"
      :game-state="gameState"
      :collected-count="collectedCount"
      :total-fragments="totalFragments"
      @close="ui.closeOverlay('inventory')"
    />
    <MemoryPanel
      v-if="ui.activeOverlay === 'memory'"
      :fragment-states="gameState.fragment_states"
      :current-scene="gameState.current_scene"
      :collected-count="gameState.collected_fragments.length"
      :total-fragments="Object.keys(gameState.fragment_states).length"
      @close="ui.closeOverlay('memory')"
    />
    <StoryLog
      v-if="ui.activeOverlay === 'story'"
      :game-state="gameState"
      :chat-history="chatPanelRef?.chatHistory || []"
      @close="ui.closeOverlay('story')"
    />
    <SceneTimeline
      v-if="ui.activeOverlay === 'timeline'"
      :current-scene="gameState.current_scene"
      :visited-scenes="gameState.visited_scenes"
      @navigate="navigateTimeline"
      @close="ui.closeOverlay('timeline')"
    />
    <div
      v-if="ui.activeOverlay === 'butterfly'"
      class="butterfly-overlay"
      @click.self="ui.closeOverlay('butterfly')"
    >
      <ButterflyPanel :game-state="gameState" />
    </div>
  </div>
</template>

<style scoped>
@import '../styles/cinematic-game.css';
</style>
