<script setup lang="ts">
import { ref, onMounted, watch, defineAsyncComponent } from 'vue'
import { useGameState } from '../composables/useGameState'
import { useTypewriter } from '../composables/useTypewriter'
import { useAudio } from '../composables/useAudio'
import { useScene } from '../composables/useScene'
import { saveGame, recordChoice, evaluateEnding } from '../api'
import { useHotspots } from '../composables/useHotspots'
import { useI18n } from '../composables/useI18n'
import type { Hotspot } from '../composables/useHotspots'
import type { EndingType } from '../types/game'

// 懒加载组件
const SceneIllustration = defineAsyncComponent(() => import('../components/SceneIllustration.vue'))
const NpcAvatar = defineAsyncComponent(() => import('../components/NpcAvatar.vue'))
const HotspotOverlay = defineAsyncComponent(() => import('../components/HotspotOverlay.vue'))
const SceneTransition = defineAsyncComponent(() => import('../components/SceneTransition.vue'))
const ButterflyPanel = defineAsyncComponent(() => import('../components/ButterflyPanel.vue'))
const StoryLog = defineAsyncComponent(() => import('../components/StoryLog.vue'))
const SceneTimeline = defineAsyncComponent(() => import('../components/SceneTimeline.vue'))
const MemoryPanel = defineAsyncComponent(() => import('../components/MemoryPanel.vue'))
const InventoryPanel = defineAsyncComponent(() => import('../components/InventoryPanel.vue'))
const ShadowLighting = defineAsyncComponent(() => import('../components/ShadowLighting.vue'))
const InkParticles = defineAsyncComponent(() => import('../components/InkParticles.vue'))
const ParallaxBg = defineAsyncComponent(() => import('../components/ParallaxBg.vue'))
const ChatPanel = defineAsyncComponent(() => import('../components/ChatPanel.vue'))

const emit = defineEmits<{ ending: [type: EndingType] }>()
const props = defineProps<{ loadSlotId?: number | null }>()

// 核心状态
const { gameState, initGame, loadFromSlot, updateTrust, collectFragment, revealFragment, addDialogue, collectedCount, totalFragments } = useGameState()
const { currentScene, currentNpcs, sceneFragments, narrativeText, sceneTransitioning, loadScene: loadSceneData, switchScene: switchSceneBase } = useScene()
const { displayText: typewriterText, isTyping, start: typeStart, skip: typeSkip } = useTypewriter(25)
const { playBGM, playSFX, isMuted, toggleMute, speak, stopSpeak } = useAudio()
const { t, lang, toggleLang } = useI18n()
const { hotspots, exploredIds, exploreHotspot, explorationProgress } = useHotspots(gameState.value?.current_scene || 'scene_1972')

// UI 状态
const selectedNpc = ref<any>(null)
const showFragmentPopup = ref(false)
const popupFragment = ref<any>(null)
const showInventory = ref(false)
const showMemoryPanel = ref(false)
const showButterfly = ref(false)
const showStoryLog = ref(false)
const showTimeline = ref(false)
const chatPanelRef = ref<InstanceType<typeof ChatPanel> | null>(null)

// 游戏时间
const getPlayTime = () => {
  if (!gameState.value) return 0
  return Math.floor((Date.now() - (gameState.value.play_start_time || Date.now())) / 1000)
}

// 自动存档
const autoSave = async () => {
  if (!gameState.value) return
  try { await saveGame(0, '自动存档', gameState.value, gameState.value.current_scene, getPlayTime()) } catch {}
}

// 加载场景（包装useScene）
const loadScene = async () => {
  if (!gameState.value) return
  sceneTransitioning.value = true
  try {
    const desc = await loadSceneData(gameState.value)
    if (desc) typeStart(desc)
  } catch {
    narrativeText.value = currentScene.value?.description || '场景加载中...'
    typeStart(narrativeText.value)
  } finally {
    setTimeout(() => { sceneTransitioning.value = false }, 600)
    playBGM(gameState.value.current_scene)
  }
}

// 场景切换
const switchScene = async (targetScene: string) => {
  if (!gameState.value || sceneTransitioning.value) return
  playSFX('scene_transition')
  sceneTransitioning.value = true
  gameState.value.current_scene = targetScene
  selectedNpc.value = null
  chatPanelRef.value?.clearHistory()
  await autoSave()
  await loadScene()
}

// NPC选择
const selectNpc = (npc: any) => {
  stopSpeak()
  selectedNpc.value = npc
  playSFX('dialogue_start')
}

// 热区探索
const handleExplore = async (hotspot: Hotspot) => {
  playSFX('explore')
  const result = exploreHotspot(hotspot.id)
  if (!result) return

  if (hotspot.fragment_id && gameState.value) {
    const fragStates = gameState.value.fragment_states
    if (fragStates?.[hotspot.fragment_id]) {
      const fragState = fragStates[hotspot.fragment_id]
      if (!fragState.revealed) { revealFragment(hotspot.fragment_id); fragState.revealed = true }
      if (!fragState.collected) {
        collectFragment(hotspot.fragment_id)
        playSFX('fragment_found')
        popupFragment.value = { id: hotspot.fragment_id, name: fragState.name || hotspot.hint, scene: hotspot.scene, description: hotspot.hint, unlock_method: '探索发现', unlock_hint: '', memory_text: '', collected: true, just_collected: true }
        showFragmentPopup.value = true
      }
    }
  }

  if (hotspot.npc_id) {
    const npc = currentNpcs.value.find((n: any) => n.id === hotspot.npc_id)
    if (npc) selectNpc(npc)
  }

  narrativeText.value = hotspot.hint
  typeStart(hotspot.hint)
}

// 蝴蝶效应: 检测关键选择
const detectAndRecordChoice = (playerMsg: string, npcId: string) => {
  if (!gameState.value) return
  const scene = gameState.value.current_scene
  if (scene === 'scene_1972' && npcId === 'chen_shouyi_young') {
    if (/坚持|继续|别放弃|加油|很好|厉害|手艺/.test(playerMsg)) recordChoice(scene, 'encourage_art', gameState.value)
    else if (/放弃|转行|没前途|别做了|算了/.test(playerMsg)) recordChoice(scene, 'discourage_art', gameState.value)
    if (/小雨|孙女|家人/.test(playerMsg)) recordChoice(scene, 'mention_xiaoyu', gameState.value)
  }
  if (scene === 'scene_2024') {
    if (npcId === 'chen_shouyi_old' && /帮你|照顾|陪伴|不孤单|我在这里/.test(playerMsg)) recordChoice(scene, 'help_elderly', gameState.value)
    if (npcId === 'xiaoyu' && /信|找到了|给你|爷爷的/.test(playerMsg)) recordChoice(scene, 'found_letter', gameState.value)
  }
}

// ChatPanel 事件处理
const onTrustChange = (npcId: string, change: number) => { updateTrust(npcId, change) }
const onFragmentReveal = (fragmentId: string, fragmentData: any) => {
  revealFragment(fragmentId)
  const trust = gameState.value?.npc_trust?.[selectedNpc.value?.id] || 30
  if (trust >= 60) {
    collectFragment(fragmentId)
    popupFragment.value = { ...fragmentData, just_collected: true }
    playSFX('fragment_found')
  } else {
    popupFragment.value = { ...fragmentData, just_collected: false }
  }
  showFragmentPopup.value = true
}
const onChoiceDetected = (msg: string, npcId: string) => {
  addDialogue('player', msg)
  detectAndRecordChoice(msg, npcId)
}

const collectCurrentFragment = (fragmentId: string) => { collectFragment(fragmentId); showFragmentPopup.value = false }
const getTrustLevel = (npcId: string) => {
  const trust = gameState.value?.npc_trust[npcId] || 30
  if (trust >= 80) return { label: '完全信任', color: '#4ade80' }
  if (trust >= 60) return { label: '比较信任', color: '#60a5fa' }
  if (trust >= 30) return { label: '初识', color: '#facc15' }
  return { label: '警惕', color: '#f87171' }
}

// 结局监控
watch(() => gameState.value?.collected_fragments?.length, async (newVal) => {
  if (!newVal || !gameState.value) return
  autoSave()
  if (gameState.value.current_scene === 'scene_2089') {
    try {
      const { data } = await evaluateEnding(gameState.value)
      const endingType = data.type as EndingType
      const endingTexts: Record<string, string> = {
        hope: '记忆修复程序启动……碎片正在聚合……那些消散的光影，重新聚合成完整的画面。',
        bittersweet: '记忆修复程序启动……部分碎片聚合了。虽然不完整，但温暖还在。',
        tragic: '记忆碎片太少了……修复程序难以启动……但也许还有希望。',
        legacy: '所有记忆碎片收集完毕，蝴蝶效应全部激活。跨越五个时代的记忆被完整修复——这不只是修复，是传承。',
      }
      narrativeText.value = endingTexts[endingType] || endingTexts.hope
      typeStart(narrativeText.value)
      setTimeout(() => { playSFX(`ending_${endingType}`); emit('ending', endingType) }, endingType === 'legacy' ? 6000 : 5000)
    } catch {
      const percent = totalFragments.value > 0 ? (newVal / totalFragments.value) * 100 : 0
      emit('ending', percent >= 80 ? 'hope' : percent >= 40 ? 'bittersweet' : 'tragic')
    }
  } else if (newVal >= totalFragments.value && totalFragments.value > 0) {
    narrativeText.value = '所有记忆碎片已经收集完毕……去最后一幕完成修复吧。'
    typeStart(narrativeText.value)
  }
})

watch(() => gameState.value?.current_scene, async (newScene) => {
  if (newScene !== 'scene_2089' || !gameState.value) return
  if ((gameState.value.collected_fragments?.length || 0) === 0) return
  try {
    const { data } = await evaluateEnding(gameState.value)
    if (data.type === 'tragic') {
      narrativeText.value = '记忆碎片太少了……修复程序难以启动……'
      typeStart(narrativeText.value)
      setTimeout(() => { playSFX('ending_tragic'); emit('ending', 'tragic') }, 5000)
    }
  } catch {}
})

onMounted(async () => {
  if (props.loadSlotId != null) await loadFromSlot(props.loadSlotId)
  else await initGame()
  await loadScene()
})
</script>

<template>
  <div class="game" v-if="gameState">
    <!-- 加载遮罩 -->
    <Transition name="fade">
      <div v-if="sceneTransitioning" class="loading-overlay">
        <div class="loading-spinner"></div>
        <div class="loading-text">记忆碎片正在重组...</div>
      </div>
    </Transition>

    <!-- 全屏背景图 + 视差 + 光影 -->
    <div class="bg-layer">
      <ParallaxBg :scene-id="gameState.current_scene">
        <template #layer-0>
          <SceneIllustration :scene-id="gameState.current_scene" />
        </template>
      </ParallaxBg>
      <div class="bg-vignette"></div>
      <ShadowLighting :scene-id="gameState.current_scene" :intensity="0.6" />
      <InkParticles :scene-id="gameState.current_scene" trigger="idle" />
    </div>

    <!-- 热区叠加层（在背景之上） -->
    <HotspotOverlay
      :hotspots="hotspots"
      :explored-ids="exploredIds"
      :scene-id="gameState.current_scene"
      @explore="handleExplore"
    />

    <!-- 顶部状态栏（悬浮） -->
    <header class="top-bar" role="banner" aria-label="游戏状态栏">
      <div class="scene-info">
        <span class="scene-time">{{ currentScene?.time_period || '...' }}</span>
        <span class="scene-title">{{ currentScene?.title || '加载中...' }}</span>
        <span class="scene-location">{{ currentScene?.location || '' }}</span>
      </div>
      <div class="status-right">
        <button class="lang-btn" @click="toggleLang" :title="lang === 'zh' ? 'Switch to English' : '切换到中文'" aria-label="语言切换">{{ lang === 'zh' ? 'EN' : '中' }}</button>
        <button class="icon-btn" @click="showMemoryPanel = true" title="记忆档案" aria-label="打开记忆档案">📜</button>
        <button class="icon-btn" @click="toggleMute" :title="isMuted ? '取消静音' : '静音'" :aria-label="isMuted ? '取消静音' : '静音'">{{ isMuted ? '🔇' : '🔊' }}</button>
        <div class="scene-nav" v-if="currentScene?.exits">
          <button
            v-for="(target, dir) in currentScene.exits"
            :key="dir"
            class="nav-btn"
            @click="switchScene(target)"
            :disabled="sceneTransitioning"
          >{{ dir === 'back' ? '◂ 返回' : '前进 ▸' }}</button>
        </div>
        <div class="fragment-counter" @click="showInventory = !showInventory">🧩 {{ collectedCount }}/{{ totalFragments }}</div>
        <div class="butterfly-btn" @click="showButterfly = !showButterfly">🦋 蝴蝶效应</div>
        <div class="timeline-btn" @click="showTimeline = !showTimeline">🕰 时光地图</div>
        <div class="log-btn" @click="showStoryLog = !showStoryLog">📜 日志</div>
        <span class="explore-badge" v-if="explorationProgress < 100">探索 {{ explorationProgress }}%</span>
        <span class="explore-badge done" v-else>✦ 已完全探索</span>
      </div>
    </header>

    <!-- 叙事文本（左下悬浮） -->
    <div class="narrative-float" v-if="narrativeText" role="complementary" aria-label="叙事文本" aria-live="polite">
      <div class="narrative-text" @click="isTyping ? typeSkip() : null">
        {{ typewriterText }}<span v-if="isTyping" class="cursor">|</span>
      </div>
    </div>

    <!-- NPC选择条（底部悬浮） -->
    <div class="npc-dock" role="toolbar" aria-label="NPC角色选择">
      <div
        v-for="npc in currentNpcs"
        :key="npc.id"
        class="npc-chip"
        :class="{ active: selectedNpc?.id === npc.id }"
        @click="selectNpc(npc)"
      >
        <NpcAvatar :npc-id="npc.id" :emotion="getTrustLevel(npc.id).label === '完全信任' ? 'happy' : 'neutral'" :size="36" />
        <div class="npc-chip-info">
          <span class="npc-chip-name">{{ npc.name }}</span>
          <div class="trust-bar-container">
            <div class="trust-bar" :style="{ width: (gameState?.npc_trust?.[npc.id] || 0) + '%', background: getTrustLevel(npc.id).color }" />
          </div>
          <span class="npc-chip-trust" :style="{ color: getTrustLevel(npc.id).color }">{{ getTrustLevel(npc.id).label }}</span>
        </div>
      </div>
    </div>

    <!-- 对话面板（右侧悬浮） -->
    <!-- 对话面板（ChatPanel组件） -->
    <div class="dialogue-float" :class="{ open: selectedNpc }" role="dialog" aria-label="NPC对话面板" aria-modal="false">
      <div class="dialogue-glass">
        <div class="dialogue-header" v-if="selectedNpc">
          <span>与 {{ selectedNpc.name }} 对话</span>
          <button class="close-btn" @click="selectedNpc = null">✕</button>
        </div>
        <div class="dialogue-header" v-else>
          <span>选择下方角色开始对话</span>
        </div>
        <ChatPanel
          ref="chatPanelRef"
          :selected-npc="selectedNpc"
          :game-state="gameState"
          :total-fragments="totalFragments"
          @trust-change="onTrustChange"
          @fragment-reveal="onFragmentReveal"
          @choice-detected="onChoiceDetected"
        />
      </div>
    </div>
<!-- 场景切换动画 -->
    <SceneTransition :active="sceneTransitioning" :scene-id="gameState?.current_scene || ''" />

    <!-- 碎片弹窗 -->
    <div class="popup-overlay" v-if="showFragmentPopup" @click.self="showFragmentPopup = false" role="dialog" aria-label="记忆碎片" aria-modal="true">
      <div class="fragment-popup">
        <div class="popup-icon">🧩</div>
        <h3>{{ popupFragment?.just_collected ? '获得记忆碎片！' : '发现记忆碎片线索' }}</h3>
        <h2>{{ popupFragment?.name }}</h2>
        <p class="fragment-desc">{{ popupFragment?.description }}</p>
        <p class="fragment-memory" v-if="popupFragment?.memory_text && popupFragment?.just_collected">
          「{{ popupFragment.memory_text }}」
        </p>
        <button class="btn-close" @click="popupFragment?.just_collected ? (showFragmentPopup = false) : collectCurrentFragment(popupFragment?.id || '')">
          {{ popupFragment?.just_collected ? '继续探索' : '收集碎片' }}
        </button>
      </div>
    </div>

    <!-- 背包面板 -->
    <InventoryPanel
      v-if="showInventory && gameState"
      :game-state="gameState"
      :collected-count="collectedCount"
      :total-fragments="totalFragments"
      @close="showInventory = false"
    />

    <!-- 记忆档案面板 -->
    <MemoryPanel
      v-if="showMemoryPanel && gameState"
      :fragment-states="gameState.fragment_states"
      :current-scene="gameState.current_scene"
      :collected-count="gameState.collected_fragments?.length || 0"
      :total-fragments="Object.keys(gameState.fragment_states || {}).length"
      @close="showMemoryPanel = false"
    />
    <!-- 剧情日志 -->
    <StoryLog
      v-if="showStoryLog"
      :game-state="gameState"
      :chat-history="chatPanelRef?.chatHistory || []"
      @close="showStoryLog = false"
    />

    <!-- 时光地图 -->
    <SceneTimeline
      v-if="showTimeline && gameState"
      :current-scene="gameState.current_scene"
      :visited-scenes="gameState.visited_scenes"
      @navigate="switchScene"
      @close="showTimeline = false"
    />

    <!-- 蝴蝶效应面板 -->
    <div class="butterfly-overlay" v-if="showButterfly" @click.self="showButterfly = false">
      <ButterflyPanel :game-state="gameState" />
    </div>
  </div>
</template>

<style scoped>
@import '../styles/game.css';
</style>