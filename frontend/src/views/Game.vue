<script setup lang="ts">
import { computed, defineAsyncComponent, onMounted, ref, watch } from 'vue'
import { evaluateEnding } from '../api'
import { useAudio } from '../composables/useAudio'
import { useGameState } from '../composables/useGameState'
import { useHotspots } from '../composables/useHotspots'
import { useI18n } from '../composables/useI18n'
import { useScene } from '../composables/useScene'
import { useTypewriter } from '../composables/useTypewriter'
import { useUiStore, type CinematicOverlay } from '../stores/ui'
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
  narrativeText,
  sceneTransitioning,
  replaceSceneView,
  loadScene: loadSceneData,
} = useScene()
const {
  displayText: typewriterText,
  isTyping,
  start: typeStart,
  skip: typeSkip,
} = useTypewriter(25)
const { playBGM, playSFX, isMuted, toggleMute, stopSpeak } = useAudio()
const { lang, toggleLang } = useI18n()
const ui = useUiStore()
const { hotspots, exploredIds, markExplored, explorationProgress } = useHotspots(
  computed(() => sceneView.value),
)

const selectedNpc = ref<NpcSummary | null>(null)
const showFragmentPopup = ref(false)
const popupFragment = ref<(Fragment & { just_collected: boolean }) | null>(null)
const actionPending = ref(false)
const mounted = ref(false)
const endingPending = ref(false)
const chatPanelRef = ref<{ clearHistory: () => void; chatHistory: ChatMessage[] } | null>(null)

const autoSave = async () => {
  if (!gameState.value) return
  if (!localStorage.getItem('mh_user')) return
  try {
    await saveToSlot(0, '自动存档')
  } catch {
    // 自动存档属于增强能力，不阻断主流程。
  }
}

const presentScene = () => {
  if (!currentScene.value || !gameState.value) return
  narrativeText.value = currentScene.value.description
  typeStart(narrativeText.value)
  playBGM(gameState.value.current_scene)
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

const selectNpc = (npc: NpcSummary) => {
  stopSpeak()
  selectedNpc.value = npc
  ui.setStageMode('dialogue')
  playSFX('dialogue_start')
}

const closeDialogue = () => {
  selectedNpc.value = null
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
  if (actionPending.value) return
  actionPending.value = true
  try {
    const result = await exploreHotspot(hotspot.id)
    markExplored(hotspot.id)
    playSFX('explore')
    narrativeText.value = hotspot.label
    typeStart(hotspot.label)

    const collectedEvent = result.events.find((event) => event.type === 'fragment.collected')
    if (collectedEvent?.content_id) {
      const fragment = fragmentForPopup(collectedEvent.content_id)
      if (fragment) {
        playSFX('fragment_found')
        popupFragment.value = { ...fragment, just_collected: true }
        showFragmentPopup.value = true
        ui.setStageMode('fragment')
      }
    }
    if (hotspot.npc_id) {
      const npc = currentNpcs.value.find((candidate) => candidate.id === hotspot.npc_id)
      if (npc) selectNpc(npc)
    }
    void autoSave()
  } catch (caught: unknown) {
    narrativeText.value = (caught as Error).message || '这段记忆暂时无法触碰。'
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

const onDialogueComplete = (result: DialogueResponse) => {
  if (result.fragment_revealed && result.fragment_data) {
    popupFragment.value = {
      ...result.fragment_data,
      collected: gameState.value?.collected_fragments.includes(result.fragment_revealed) ?? false,
      just_collected: false,
    }
    showFragmentPopup.value = true
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
</script>

<template>
  <div v-if="gameState" class="game game-cinema" :data-stage-mode="ui.stageMode">
    <Transition name="fade">
      <div v-if="sceneTransitioning" class="loading-overlay">
        <span class="loading-code">MEMORY FIELD / {{ gameState.current_scene }}</span>
        <div class="loading-line"><i /></div>
        <div class="loading-text">正在重组记忆</div>
      </div>
    </Transition>

    <div class="bg-layer">
      <CinematicStage :scene-id="gameState.current_scene" :active-npc-id="selectedNpc?.id ?? null">
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
        @explore="handleExplore"
      />
    </div>

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
        <button
          class="hud-action compact"
          :title="isMuted ? '取消静音' : '静音'"
          :aria-label="isMuted ? '取消静音' : '静音'"
          @click="toggleMute"
        >
          {{ isMuted ? '静' : '声' }}
        </button>
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

    <div v-if="choices.length" class="scene-nav" aria-label="剧情选择">
      <span class="choice-kicker">CAUSAL DECISION</span>
      <button
        v-for="(choice, index) in choices"
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
          @dialogue-complete="onDialogueComplete"
        />
      </div>
    </div>

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
        <div class="popup-icon" aria-hidden="true"><i /></div>
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

    <div class="exploration-meter" aria-label="场景探索进度">
      <span>{{ explorationProgress === 100 ? '场景已校准' : '场景校准中' }}</span>
      <i><b :style="{ width: `${explorationProgress}%` }" /></i>
      <strong>{{ String(explorationProgress).padStart(2, '0') }}%</strong>
    </div>
  </div>
</template>

<style scoped>
@import '../styles/cinematic-game.css';
</style>
