<script setup lang="ts">
import { ref, onMounted, watch, nextTick, defineAsyncComponent } from 'vue'
import { useGameState } from '../composables/useGameState'
import { useTypewriter } from '../composables/useTypewriter'
import { useAudio } from '../composables/useAudio'
import { chatWithNpcStream, getSceneDetail, advanceNarrative, saveGame, recordChoice, evaluateEnding } from '../api'
import { useHotspots } from '../composables/useHotspots'
import { useI18n } from '../composables/useI18n'
import type { Hotspot } from '../composables/useHotspots'
import type { Scene, NpcSummary, Fragment, ChatMessage, EndingType } from '../types/game'

// 懒加载重量级组件
const SceneIllustration = defineAsyncComponent(() => import('../components/SceneIllustration.vue'))
const MemoryProgress = defineAsyncComponent(() => import('../components/MemoryProgress.vue'))
const NpcAvatar = defineAsyncComponent(() => import('../components/NpcAvatar.vue'))
const HotspotOverlay = defineAsyncComponent(() => import('../components/HotspotOverlay.vue'))
const SceneTransition = defineAsyncComponent(() => import('../components/SceneTransition.vue'))
const ButterflyPanel = defineAsyncComponent(() => import('../components/ButterflyPanel.vue'))
const StoryLog = defineAsyncComponent(() => import('../components/StoryLog.vue'))
const SceneTimeline = defineAsyncComponent(() => import('../components/SceneTimeline.vue'))
const MemoryPanel = defineAsyncComponent(() => import('../components/MemoryPanel.vue'))
const ShadowLighting = defineAsyncComponent(() => import('../components/ShadowLighting.vue'))
const InkParticles = defineAsyncComponent(() => import('../components/InkParticles.vue'))
const ParallaxBg = defineAsyncComponent(() => import('../components/ParallaxBg.vue'))

const emit = defineEmits<{
  ending: [type: EndingType]
}>()

const props = defineProps<{
  loadSlotId?: number | null
}>()

const { gameState, initGame, loadFromSlot, updateTrust, collectFragment, revealFragment, addDialogue, collectedCount, totalFragments } = useGameState()

const currentScene = ref<Scene | null>(null)
const currentNpcs = ref<NpcSummary[]>([])
const sceneFragments = ref<Array<Fragment & { is_collected: boolean }>>([])
const narrativeText = ref('')
const playerInput = ref('')
const presetOptions = ref<string[]>([])
const selectedNpc = ref<NpcSummary | null>(null)
const showFragmentPopup = ref(false)
const popupFragment = ref<(Fragment & { just_collected?: boolean }) | null>(null)
const chatLoading = ref(false)
const showInventory = ref(false)

const { displayText: typewriterText, isTyping, start: typeStart, skip: typeSkip } = useTypewriter(25)

// 音频系统
const { playBGM, playSFX, isMuted, toggleMute, speak, stopSpeak } = useAudio()
const { t, lang, toggleLang } = useI18n()

// 热区探索（初始场景，loadScene时会更新）
const { hotspots, exploredIds, exploreHotspot, explorationProgress } = useHotspots(gameState.value?.current_scene || 'scene_1972')

// 记忆档案面板
const showMemoryPanel = ref(false)
const showButterfly = ref(false)
const showStoryLog = ref(false)
const showTimeline = ref(false)

const chatHistory = ref<ChatMessage[]>([])
const chatContainer = ref<HTMLElement | null>(null)

// 场景切换
const sceneTransitioning = ref(false)

// 游戏时间（持久化到gameState，避免页面切换重置）
const getPlayTime = () => {
  if (!gameState.value) return 0
  const startTime = gameState.value.play_start_time || Date.now()
  return Math.floor((Date.now() - startTime) / 1000)
}

// 自动存档
const autoSave = async () => {
  if (!gameState.value) return
  try {
    await saveGame(0, '自动存档', gameState.value, gameState.value.current_scene, getPlayTime())
  } catch {}
}

onMounted(async () => {
  if (props.loadSlotId != null) {
    await loadFromSlot(props.loadSlotId)
  } else {
    await initGame()
  }
  await loadScene()
})

const loadScene = async () => {
  if (!gameState.value) return
  sceneTransitioning.value = true
  try {
    const res = await getSceneDetail(gameState.value.current_scene, gameState.value)
    currentScene.value = res.data.scene
    currentNpcs.value = res.data.npcs
    sceneFragments.value = res.data.fragments

    // 叙事推进
    const narrRes = await advanceNarrative('进入场景', gameState.value)
    let sceneDesc = narrRes.data.scene_description

    // 蝴蝶效应: 追加场景修改描述
    const butterflyMods = res.data.butterfly_mods || []
    if (butterflyMods.length > 0) {
      sceneDesc += '\n\n' + butterflyMods.join('\n')
    }

    narrativeText.value = sceneDesc
    presetOptions.value = narrRes.data.available_actions
    typeStart(sceneDesc)
  } catch {
    narrativeText.value = currentScene.value?.description || '场景加载中...'
    typeStart(narrativeText.value)
  } finally {
    setTimeout(() => { sceneTransitioning.value = false }, 600)
    // 播放场景BGM
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
  chatHistory.value = []
  await autoSave()
  await loadScene()
}

const selectNpc = (npc: NpcSummary) => {
  stopSpeak()
  selectedNpc.value = npc
  playerInput.value = ''
  playSFX('dialogue_start')
}

// 热区探索处理
const handleExplore = async (hotspot: Hotspot) => {
  playSFX('explore')
  const result = exploreHotspot(hotspot.id)
  if (!result) return

  // 如果热区关联碎片，检查是否可以收集
  if (hotspot.fragment_id && gameState.value) {
    const fragStates = gameState.value.fragment_states
    if (fragStates && fragStates[hotspot.fragment_id]) {
      const fragState = fragStates[hotspot.fragment_id]
      if (!fragState.revealed) {
        revealFragment(hotspot.fragment_id)
        fragState.revealed = true
      }
      // 热区发现的碎片直接收集
      if (!fragState.collected) {
        collectFragment(hotspot.fragment_id)
        playSFX('fragment_found')
        popupFragment.value = {
          id: hotspot.fragment_id,
          name: fragState.name || hotspot.hint,
          scene: hotspot.scene,
          description: hotspot.hint,
          unlock_method: '探索发现',
          unlock_hint: '',
          memory_text: '',
          collected: true,
          just_collected: true,
        }
        showFragmentPopup.value = true
      }
    }
  }

  // 如果关联NPC，自动选中
  if (hotspot.npc_id) {
    const npc = currentNpcs.value.find(n => n.id === hotspot.npc_id)
    if (npc) selectNpc(npc)
  }

  // 显示探索描述
  narrativeText.value = hotspot.hint
  typeStart(hotspot.hint)
}

// 蝴蝶效应: 检测玩家对话中的关键选择
const detectAndRecordChoice = (playerMsg: string, npcId: string) => {
  if (!gameState.value) return
  const scene = gameState.value.current_scene

  // 1972年: 鼓励/劝阻皮影戏
  if (scene === 'scene_1972' && npcId === 'chen_shouyi_young') {
    if (/坚持|继续|别放弃|加油|很好|厉害|手艺/.test(playerMsg)) {
      recordChoice(scene, 'encourage_art', gameState.value)
    } else if (/放弃|转行|没前途|别做了|算了/.test(playerMsg)) {
      recordChoice(scene, 'discourage_art', gameState.value)
    }
    if (/小雨|孙女|家人/.test(playerMsg)) {
      recordChoice(scene, 'mention_xiaoyu', gameState.value)
    }
  }

  // 2024年: 帮助老人/找到信件
  if (scene === 'scene_2024') {
    if (npcId === 'chen_shouyi_old' && /帮你|照顾|陪伴|不孤单|我在这里/.test(playerMsg)) {
      recordChoice(scene, 'help_elderly', gameState.value)
    }
    if (npcId === 'xiaoyu' && /信|找到了|给你|爷爷的/.test(playerMsg)) {
      recordChoice(scene, 'found_letter', gameState.value)
    }
  }
}

const sendMessage = async (text?: string) => {
  const msg = text || playerInput.value.trim()
  if (!msg || !selectedNpc.value || !gameState.value || chatLoading.value) return

  playerInput.value = ''
  chatLoading.value = true

  // 添加玩家消息
  chatHistory.value.push({ role: 'player', content: msg })
  addDialogue('player', msg)
  detectAndRecordChoice(msg, selectedNpc.value.id)
  scrollToBottom()

  // 添加 NPC 占位消息
  const npcMsgIndex = chatHistory.value.length
  chatHistory.value.push({ role: 'npc', content: '', npcName: selectedNpc.value.name, npcId: selectedNpc.value.id, emotion: 'neutral' })

  try {
    // 优先用 SSE 流式
    chatWithNpcStream(
      { npc_id: selectedNpc.value.id, player_input: msg, game_state: gameState.value },
      // onToken
      (token) => {
        chatHistory.value[npcMsgIndex].content += token
        scrollToBottom()
      },
      // onDone
      (data) => {
        // 后端已保证reply干净，直接使用
        chatHistory.value[npcMsgIndex].content = data.reply
        chatHistory.value[npcMsgIndex].emotion = data.npc_mood || 'neutral'
        addDialogue('npc', data.reply)

        // 播放NPC语音
        speak(data.reply, selectedNpc.value!.id)

        if (data.trust_change !== 0) {
          updateTrust(selectedNpc.value!.id, data.trust_change)
          playSFX(data.trust_change > 0 ? 'trust_up' : 'trust_down')
        }

        if (data.fragment_revealed && data.fragment_data) {
          revealFragment(data.fragment_revealed)
          const trust = gameState.value!.npc_trust[selectedNpc.value!.id] || 30
          if (trust >= 60) {
            collectFragment(data.fragment_revealed)
            popupFragment.value = { ...data.fragment_data, just_collected: true }
            playSFX('fragment_found')
          } else {
            popupFragment.value = { ...data.fragment_data, just_collected: false }
          }
          showFragmentPopup.value = true
        }

        if (data.reply.includes('？') || data.reply.includes('?')) {
          presetOptions.value = ['继续问', '换个话题', '告辞']
        }

        chatLoading.value = false
        scrollToBottom()
      },
      // onError
      (errMsg) => {
        chatHistory.value[npcMsgIndex].content = `[${errMsg}]`
        chatLoading.value = false
        scrollToBottom()
      },
    )
  } catch {
    chatHistory.value.push({ role: 'system', content: '[连接中断，请重试]' })
    chatLoading.value = false
    scrollToBottom()
  }
}

const collectCurrentFragment = (fragmentId: string) => {
  collectFragment(fragmentId)
  showFragmentPopup.value = false
}

const scrollToBottom = () => {
  nextTick(() => {
    if (chatContainer.value) {
      chatContainer.value.scrollTop = chatContainer.value.scrollHeight
    }
  })
}

const getTrustLevel = (npcId: string) => {
  const trust = gameState.value?.npc_trust[npcId] || 30
  if (trust >= 80) return { label: '完全信任', color: '#4ade80' }
  if (trust >= 60) return { label: '比较信任', color: '#60a5fa' }
  if (trust >= 30) return { label: '初识', color: '#facc15' }
  return { label: '警惕', color: '#f87171' }
}

watch(() => gameState.value?.collected_fragments?.length, async (newVal) => {
  if (!newVal || !gameState.value) return

  // 每收集一个碎片自动存档
  autoSave()

  // 在最后一幕时用后端评估结局
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

      setTimeout(() => {
        playSFX(`ending_${endingType}`)
        emit('ending', endingType)
      }, endingType === 'legacy' ? 6000 : 5000)
    } catch {
      // 降级：本地判断
      const percent = totalFragments.value > 0 ? (newVal / totalFragments.value) * 100 : 0
      const endingType: EndingType = percent >= 80 ? 'hope' : percent >= 40 ? 'bittersweet' : 'tragic'
      emit('ending', endingType)
    }
  } else if (newVal >= totalFragments.value && totalFragments.value > 0) {
    // 非最后一幕但全部收集
    narrativeText.value = '所有记忆碎片已经收集完毕……去最后一幕完成修复吧。'
    typeStart(narrativeText.value)
  }
})

// 进入最后一幕时触发结局评估
watch(() => gameState.value?.current_scene, async (newScene) => {
  if (newScene !== 'scene_2089' || !gameState.value) return
  const collected = gameState.value.collected_fragments?.length || 0
  if (collected === 0) return

  try {
    const { data } = await evaluateEnding(gameState.value)
    const endingType = data.type as EndingType

    if (endingType === 'tragic') {
      narrativeText.value = '记忆碎片太少了……修复程序难以启动……'
      typeStart(narrativeText.value)
      setTimeout(() => {
        playSFX('ending_tragic')
        emit('ending', 'tragic')
      }, 5000)
    }
  } catch { /* 降级忽略 */ }
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
    <div class="dialogue-float" :class="{ open: selectedNpc }" role="dialog" aria-label="NPC对话面板" aria-modal="false">
      <div class="dialogue-glass">
        <div class="dialogue-header" v-if="selectedNpc">
          <span>与 {{ selectedNpc.name }} 对话</span>
          <button class="close-btn" @click="selectedNpc = null">✕</button>
        </div>
        <div class="dialogue-header" v-else>
          <span>选择下方角色开始对话</span>
        </div>

        <div class="chat-area" ref="chatContainer" role="log" aria-live="polite" aria-label="对话历史">
          <div v-if="!selectedNpc" class="empty-chat">
            <p>点击下方角色头像开始对话</p>
          </div>
          <div
            v-for="(msg, i) in chatHistory"
            :key="i"
            class="chat-msg"
            :class="msg.role"
          >
            <NpcAvatar v-if="msg.role === 'npc' && msg.npcId" :npc-id="msg.npcId" :emotion="msg.emotion || 'neutral'" :size="28" class="msg-avatar" />
            <span class="msg-avatar-player" v-else-if="msg.role === 'player'">你</span>
            <div class="msg-body">
              <span class="msg-name" v-if="msg.role === 'npc'">{{ msg.npcName }}</span>
              <span class="msg-name" v-else-if="msg.role === 'player'">你</span>
              <span class="msg-name" v-else>系统</span>
              <span class="msg-text">{{ msg.content }}</span>
            </div>
          </div>
          <div v-if="chatLoading" class="chat-msg npc loading">
            <span class="msg-name">{{ selectedNpc?.name }}</span>
            <span class="msg-text typing-dots">思考中<span class="dot">.</span><span class="dot">.</span><span class="dot">.</span></span>
          </div>
        </div>

        <!-- 预设选项 -->
        <div class="preset-options" v-if="selectedNpc && presetOptions.length">
          <button
            v-for="opt in presetOptions"
            :key="opt"
            class="preset-btn"
            @click="playSFX('click'); sendMessage(opt)"
            :disabled="chatLoading"
          >{{ opt }}</button>
        </div>

        <!-- 输入框 -->
        <div class="input-area" v-if="selectedNpc">
          <input
            v-model="playerInput"
            class="chat-input"
            placeholder="你想说什么..."
            @keyup.enter="sendMessage()"
            :disabled="chatLoading"
          />
          <button class="send-btn" @click="playSFX('click'); sendMessage()" :disabled="chatLoading || !playerInput.trim()" aria-label="发送消息">➤</button>
        </div>
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
    <div class="inventory-panel" v-if="showInventory" role="complementary" aria-label="记忆碎片背包">
      <div class="inventory-header">
        <h3>🧩 记忆碎片</h3>
        <button @click="showInventory = false">✕</button>
      </div>
      <div class="inventory-progress">
        <MemoryProgress :collected="collectedCount" :total="totalFragments" />
      </div>
      <div class="inventory-list">
        <div
          v-for="(frag, id) in gameState.fragment_states"
          :key="id"
          class="inventory-item"
          :class="{ collected: frag.collected }"
        >
          <span class="frag-icon">{{ frag.collected ? '🧩' : '❓' }}</span>
          <span class="frag-name">{{ frag.collected ? frag.name : '???' }}</span>
          <span class="frag-scene">{{ frag.scene }}</span>
        </div>
      </div>
    </div>

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
      :chat-history="chatHistory"
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
.game {
  position: relative;
  width: 100vw;
  height: 100vh;
  overflow: hidden;
  background: #0a0a0a;
  font-family: 'Noto Serif SC', 'Noto Sans SC', sans-serif;
  color: #e8e0d0;
}

/* ===== 全屏背景层 ===== */
.bg-layer {
  position: fixed;
  inset: 0;
  z-index: 0;
}
.bg-layer :deep(.scene-illustration) {
  width: 100%;
  height: 100%;
  content-visibility: auto;
  contain-intrinsic-size: 800px 500px;
}
.bg-layer :deep(.scene-illustration svg),
.bg-layer :deep(.scene-illustration img) {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.bg-vignette {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(ellipse at 50% 50%, transparent 30%, rgba(0,0,0,0.6) 70%, rgba(0,0,0,0.9) 100%),
    linear-gradient(180deg, rgba(0,0,0,0.3) 0%, transparent 15%, transparent 85%, rgba(0,0,0,0.5) 100%);
  pointer-events: none;
  z-index: 1;
}

/* ===== 顶部栏 ===== */
.top-bar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 28px;
  background: linear-gradient(180deg, rgba(0,0,0,0.85) 0%, rgba(0,0,0,0.4) 60%, transparent 100%);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-bottom: 1px solid rgba(232, 180, 80, 0.06);
}
.scene-info {
  display: flex;
  align-items: center;
  gap: 12px;
}
.scene-time {
  display: inline-block;
  background: rgba(232, 180, 80, 0.2);
  border: 1px solid rgba(232, 180, 80, 0.3);
  color: #e8b450;
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 2px;
}
.scene-title {
  font-size: 16px;
  font-weight: 600;
  color: #f0e8d8;
  text-shadow: 0 1px 4px rgba(0,0,0,0.8);
}
.scene-location {
  font-size: 13px;
  color: rgba(232, 180, 80, 0.7);
  text-shadow: 0 1px 4px rgba(0,0,0,0.8);
}
.status-right {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}
.icon-btn {
  background: rgba(0,0,0,0.4);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 8px;
  color: #e8e0d0;
  font-size: 18px;
  cursor: pointer;
  padding: 6px 10px;
  transition: all 0.2s;
}
.icon-btn:hover {
  background: rgba(232, 180, 80, 0.2);
  border-color: rgba(232, 180, 80, 0.4);
}
.scene-nav {
  display: flex;
  gap: 6px;
}
.nav-btn {
  background: rgba(232, 180, 80, 0.15);
  border: 1px solid rgba(232, 180, 80, 0.3);
  border-radius: 8px;
  color: #e8b450;
  padding: 6px 14px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
  font-family: inherit;
}
.nav-btn:hover:not(:disabled) {
  background: rgba(232, 180, 80, 0.3);
}
.nav-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
.fragment-counter {
  cursor: pointer;
  font-size: 14px;
  color: #b8d4e8;
  background: rgba(0,0,0,0.4);
  padding: 6px 12px;
  border-radius: 8px;
  border: 1px solid rgba(255,255,255,0.1);
  transition: all 0.2s;
}
.fragment-counter:hover {
  background: rgba(58, 134, 255, 0.2);
  border-color: rgba(58, 134, 255, 0.3);
}
.explore-badge {
  font-size: 12px;
  background: rgba(232, 180, 80, 0.15);
  color: #e8b450;
  padding: 4px 10px;
  border-radius: 10px;
  border: 1px solid rgba(232, 180, 80, 0.2);
}
.explore-badge.done {
  background: rgba(80, 232, 120, 0.15);
  color: #50e878;
  border-color: rgba(80, 232, 120, 0.3);
}

/* ===== 叙事文本（左下） ===== */
.narrative-float {
  position: fixed;
  z-index: 50;
  bottom: 100px;
  left: 24px;
  max-width: 500px;
  max-height: 220px;
  overflow-y: auto;
  background: linear-gradient(135deg, rgba(0,0,0,0.65) 0%, rgba(10,10,20,0.7) 100%);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border: 1px solid rgba(232, 180, 80, 0.12);
  border-radius: 16px;
  padding: 18px 24px;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow:
    0 4px 30px rgba(0,0,0,0.3),
    inset 0 1px 0 rgba(232, 180, 80, 0.06);
}
.narrative-float:hover {
  background: linear-gradient(135deg, rgba(0,0,0,0.75) 0%, rgba(10,10,20,0.8) 100%);
  border-color: rgba(232, 180, 80, 0.2);
  box-shadow:
    0 8px 40px rgba(0,0,0,0.4),
    0 0 20px rgba(232, 180, 80, 0.05),
    inset 0 1px 0 rgba(232, 180, 80, 0.1);
}
.narrative-text {
  font-size: 15px;
  line-height: 2;
  color: #f0e8d0;
  text-shadow: 0 1px 4px rgba(0,0,0,0.6);
  font-family: 'Noto Serif SC', serif;
  letter-spacing: 0.5px;
}
.cursor {
  animation: blink 0.8s infinite;
  color: #e8b450;
}
@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

/* ===== NPC 底部栏 ===== */
.npc-dock {
  position: fixed;
  z-index: 60;
  bottom: 28px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 14px;
  padding: 8px 16px;
  background: rgba(0,0,0,0.3);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border-radius: 50px;
  border: 1px solid rgba(255,255,255,0.06);
}
.npc-chip {
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(0,0,0,0.5);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 40px;
  padding: 6px 16px 6px 6px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.22, 1, 0.36, 1);
}
.npc-chip:hover {
  background: rgba(232, 180, 80, 0.2);
  border-color: rgba(232, 180, 80, 0.3);
  transform: translateY(-3px);
  box-shadow: 0 8px 24px rgba(0,0,0,0.3);
}
.npc-chip.active {
  background: rgba(232, 180, 80, 0.25);
  border-color: rgba(232, 180, 80, 0.6);
  box-shadow:
    0 0 24px rgba(232, 180, 80, 0.2),
    0 8px 32px rgba(0,0,0,0.3);
  transform: translateY(-2px);
}
.npc-chip-info {
  display: flex;
  flex-direction: column;
  line-height: 1.2;
}
.npc-chip-name {
  font-size: 13px;
  font-weight: 600;
  color: #f0e8d8;
}
.npc-chip-trust {
  font-size: 11px;
  opacity: 0.8;
}
.trust-bar-container {
  width: 60px;
  height: 3px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 2px;
  overflow: hidden;
}
.trust-bar {
  height: 100%;
  border-radius: 2px;
  transition: width 0.5s ease;
}

/* ===== 对话面板（右侧滑出） ===== */
.dialogue-float {
  position: fixed;
  z-index: 80;
  right: -440px;
  top: 70px;
  bottom: 28px;
  width: 420px;
  transition: right 0.4s cubic-bezier(0.22, 1, 0.36, 1);
}
.dialogue-float.open {
  right: 24px;
}
.dialogue-glass {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: linear-gradient(180deg, rgba(10, 10, 18, 0.82) 0%, rgba(15, 12, 20, 0.88) 100%);
  backdrop-filter: blur(32px);
  -webkit-backdrop-filter: blur(32px);
  border: 1px solid rgba(232, 180, 80, 0.1);
  border-radius: 20px;
  overflow: hidden;
  box-shadow:
    0 8px 50px rgba(0,0,0,0.5),
    0 0 1px rgba(232, 180, 80, 0.1),
    inset 0 1px 0 rgba(255,255,255,0.04);
}
.dialogue-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 18px;
  background: rgba(0,0,0,0.3);
  border-bottom: 1px solid rgba(232, 180, 80, 0.1);
  font-size: 14px;
  color: #e8b450;
  font-weight: 600;
}
.close-btn {
  background: none;
  border: none;
  color: rgba(255,255,255,0.4);
  font-size: 18px;
  cursor: pointer;
  padding: 2px 6px;
  border-radius: 4px;
  transition: all 0.15s;
}
.close-btn:hover {
  color: #e8e0d0;
  background: rgba(255,255,255,0.1);
}
.chat-area {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.chat-area::-webkit-scrollbar { width: 4px; }
.chat-area::-webkit-scrollbar-track { background: transparent; }
.chat-area::-webkit-scrollbar-thumb {
  background: rgba(232, 180, 80, 0.2);
  border-radius: 2px;
}
.empty-chat {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(255,255,255,0.3);
  font-size: 14px;
}
.chat-msg {
  display: flex;
  gap: 8px;
  align-items: flex-start;
}
.chat-msg.npc { flex-direction: row; }
.chat-msg.player { flex-direction: row-reverse; }
.chat-msg.system { justify-content: center; }
.msg-avatar {
  flex-shrink: 0;
  margin-top: 2px;
}
.msg-avatar-player {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: rgba(100, 150, 255, 0.2);
  border: 1px solid rgba(100, 150, 255, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  color: #a0b0ff;
  flex-shrink: 0;
}
.msg-body {
  display: flex;
  flex-direction: column;
  gap: 2px;
  max-width: 80%;
}
.msg-name {
  font-size: 11px;
  opacity: 0.6;
  padding: 0 4px;
}
.msg-text {
  padding: 8px 14px;
  border-radius: 12px;
  font-size: 13px;
  line-height: 1.6;
}
.chat-msg.npc .msg-text {
  background: rgba(232, 180, 80, 0.1);
  border: 1px solid rgba(232, 180, 80, 0.12);
  border-top-left-radius: 4px;
}
.chat-msg.player .msg-text {
  background: rgba(58, 134, 255, 0.15);
  border: 1px solid rgba(58, 134, 255, 0.15);
  border-top-right-radius: 4px;
  color: #b8d4e8;
}
.chat-msg.system .msg-text {
  background: rgba(255,255,255,0.05);
  font-size: 12px;
}
.typing-dots .dot {
  animation: dotPulse 1.4s infinite;
  opacity: 0.3;
}
.typing-dots .dot:nth-child(2) { animation-delay: 0.2s; }
.typing-dots .dot:nth-child(3) { animation-delay: 0.4s; }
@keyframes dotPulse {
  0%, 100% { opacity: 0.3; }
  50% { opacity: 1; }
}
.preset-options {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  padding: 8px 16px 4px;
}
.preset-btn {
  background: rgba(232, 180, 80, 0.1);
  border: 1px solid rgba(232, 180, 80, 0.2);
  border-radius: 16px;
  color: #e8b450;
  padding: 5px 14px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.15s;
  font-family: inherit;
}
.preset-btn:hover:not(:disabled) {
  background: rgba(232, 180, 80, 0.25);
}
.preset-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
.input-area {
  display: flex;
  gap: 6px;
  padding: 8px 12px 12px;
}
.chat-input {
  flex: 1;
  background: rgba(0,0,0,0.3);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 20px;
  padding: 8px 16px;
  color: #e8e0d0;
  font-size: 13px;
  outline: none;
  transition: border-color 0.2s;
  font-family: inherit;
}
.chat-input:focus {
  border-color: rgba(232, 180, 80, 0.3);
}
.chat-input::placeholder {
  color: rgba(255,255,255,0.2);
}
.send-btn {
  background: rgba(232, 180, 80, 0.2);
  border: 1px solid rgba(232, 180, 80, 0.3);
  border-radius: 50%;
  width: 36px;
  height: 36px;
  color: #e8b450;
  font-size: 16px;
  cursor: pointer;
  transition: all 0.15s;
  display: flex;
  align-items: center;
  justify-content: center;
}
.send-btn:hover:not(:disabled) {
  background: rgba(232, 180, 80, 0.35);
}
.send-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

/* ===== 弹窗/面板 ===== */
.popup-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 200;
  backdrop-filter: blur(8px);
  animation: popupFadeIn 0.3s ease;
}
@keyframes popupFadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}
.fragment-popup {
  background: linear-gradient(135deg, rgba(26, 26, 46, 0.95) 0%, rgba(42, 42, 78, 0.95) 100%);
  border: 1px solid rgba(232,180,80,0.2);
  border-radius: 20px;
  padding: 48px;
  text-align: center;
  max-width: 440px;
  box-shadow:
    0 0 80px rgba(232,180,80,0.12),
    0 0 120px rgba(232,180,80,0.06),
    0 20px 60px rgba(0,0,0,0.5);
  animation: popupScaleIn 0.4s cubic-bezier(0.22, 1, 0.36, 1);
  position: relative;
  overflow: hidden;
}
.fragment-popup::before {
  content: '';
  position: absolute;
  inset: -50%;
  background: conic-gradient(from 0deg, transparent, rgba(232,180,80,0.08), transparent, rgba(232,180,80,0.05), transparent);
  animation: popupRotate 8s linear infinite;
  pointer-events: none;
}
@keyframes popupRotate {
  to { transform: rotate(360deg); }
}
@keyframes popupScaleIn {
  from { transform: scale(0.8); opacity: 0; }
  to { transform: scale(1); opacity: 1; }
}
.popup-icon { font-size: 48px; margin-bottom: 12px; }
.fragment-popup h3 { color: rgba(232,180,80,0.6); font-size: 14px; margin: 0 0 8px; }
.fragment-popup h2 { font-size: 22px; color: #e8b450; margin: 0 0 16px; }
.fragment-desc { color: rgba(240,232,208,0.7); font-size: 14px; line-height: 1.8; margin-bottom: 12px; }
.fragment-memory {
  color: rgba(255,200,100,0.8);
  font-size: 14px;
  font-style: italic;
  line-height: 1.8;
  margin-bottom: 24px;
  padding: 12px;
  background: rgba(255,200,100,0.05);
  border-radius: 8px;
  border-left: 3px solid rgba(255,200,100,0.3);
}
.btn-close {
  padding: 10px 32px;
  border-radius: 8px;
  background: rgba(232,180,80,0.2);
  border: 1px solid rgba(232,180,80,0.3);
  color: #e8b450;
  font-size: 15px;
  cursor: pointer;
  font-family: inherit;
  transition: all 0.15s;
}
.btn-close:hover { background: rgba(232,180,80,0.35); }
.inventory-panel {
  position: fixed;
  right: 0;
  top: 0;
  bottom: 0;
  width: 320px;
  background: rgba(10,10,18,0.95);
  border-left: 1px solid rgba(232,180,80,0.12);
  z-index: 150;
  display: flex;
  flex-direction: column;
  backdrop-filter: blur(16px);
}
.inventory-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid rgba(232,180,80,0.1);
}
.inventory-progress {
  padding: 12px 16px;
  border-bottom: 1px solid rgba(232,180,80,0.08);
}
.inventory-header h3 { margin: 0; font-size: 16px; color: #e8b450; }
.inventory-header button {
  background: none;
  border: none;
  color: rgba(255,255,255,0.4);
  font-size: 18px;
  cursor: pointer;
}
.inventory-list {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}
.inventory-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: 8px;
  margin-bottom: 8px;
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.06);
}
.inventory-item.collected {
  background: rgba(232,180,80,0.08);
  border-color: rgba(232,180,80,0.2);
}
.frag-icon { font-size: 24px; }
.frag-name { flex: 1; font-size: 14px; }
.frag-scene { font-size: 11px; color: rgba(255,255,255,0.3); }

/* ===== 响应式 ===== */
@media (max-width: 1024px) {
  .dialogue-float { width: 340px; right: -380px; }
  .dialogue-float.open { right: 16px; }
  .narrative-float { max-width: 360px; left: 16px; bottom: 90px; }
}
@media (max-width: 768px) {
  .top-bar {
    flex-direction: column;
    gap: 8px;
    padding: 8px 12px;
    align-items: flex-start;
  }
  .status-right {
    gap: 6px;
    width: 100%;
    justify-content: flex-end;
  }
  .scene-title { font-size: 14px; }
  .scene-time { font-size: 11px; padding: 2px 8px; }
  .narrative-float {
    left: 8px; right: 8px;
    bottom: 80px;
    max-width: none;
    max-height: 120px;
    padding: 12px 14px;
  }
  .narrative-text { font-size: 13px; line-height: 1.7; }
  .npc-dock {
    bottom: 8px;
    gap: 8px;
    left: 8px; right: 8px;
    transform: none;
    justify-content: center;
    flex-wrap: wrap;
  }
  .npc-chip { padding: 4px 10px 4px 4px; }
  .dialogue-float {
    top: 0; bottom: 0; left: 0;
    width: 100%;
    right: -100%;
    transition: right 0.3s ease;
  }
  .dialogue-float.open { right: 0; }
  .dialogue-glass { border-radius: 0; border: none; }
  .fragment-popup { width: 90%; padding: 24px; }
  .inventory-panel { width: 100%; }
}
@media (max-width: 480px) {
  .top-bar { padding: 6px 8px; }
  .scene-info { gap: 6px; }
  .status-right { gap: 4px; }
  .icon-btn { padding: 4px 8px; font-size: 14px; }
  .nav-btn { padding: 4px 10px; font-size: 12px; }
  .fragment-counter { font-size: 12px; padding: 4px 8px; }
  .explore-badge { font-size: 10px; padding: 2px 6px; }
}

/* 滚动条 */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb {
  background: rgba(232,180,80,0.2);
  border-radius: 3px;
}

/* 语言切换按钮 */
.lang-btn {
  background: rgba(0,0,0,0.4);
  border: 1px solid rgba(232,180,80,0.3);
  border-radius: 6px;
  color: #e8b450;
  padding: 4px 10px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}
.lang-btn:hover {
  background: rgba(232,180,80,0.2);
  border-color: rgba(232,180,80,0.5);
}

/* 响应式优化 */
@media (max-width: 480px) {
  .top-bar {
    padding: 8px 12px;
    flex-wrap: wrap;
    gap: 8px;
  }
  .scene-info {
    flex-wrap: wrap;
    gap: 6px;
  }
  .dialogue-float {
    width: 100%;
    right: -100%;
  }
  .dialogue-float.open {
    right: 0;
  }
  .narrative-float {
    left: 8px;
    right: 8px;
    bottom: 100px;
    max-width: none;
  }
  .npc-dock {
    padding: 6px 8px;
    gap: 6px;
    flex-wrap: wrap;
    justify-content: center;
  }
  .npc-chip {
    min-width: 80px;
  }
  .inventory-panel {
    width: 100%;
    max-height: 60vh;
  }
}

@media (min-width: 481px) and (max-width: 768px) {
  .dialogue-float {
    width: 360px;
  }
  .narrative-float {
    max-width: 360px;
  }
}

@media (min-width: 769px) and (max-width: 1024px) {
  .dialogue-float {
    width: 380px;
  }
}

/* 焦点样式（无障碍） */
*:focus-visible {
  outline: 2px solid rgba(232,180,80,0.6);
  outline-offset: 2px;
}

/* 减少动画（无障碍） */
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}

/* 加载遮罩 */
.loading-overlay {
  position: fixed;
  inset: 0;
  z-index: 1000;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: rgba(10, 10, 26, 0.95);
  backdrop-filter: blur(12px);
}
.loading-spinner {
  width: 48px;
  height: 48px;
  border: 2px solid rgba(232, 180, 80, 0.15);
  border-top-color: #e8b450;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 20px;
  box-shadow: 0 0 20px rgba(232, 180, 80, 0.1);
}
@keyframes spin {
  to { transform: rotate(360deg); }
}
.loading-text {
  color: #e8b450;
  font-size: 15px;
  font-family: 'Noto Serif SC', serif;
  letter-spacing: 3px;
  animation: loadingPulse 2s ease-in-out infinite;
}
@keyframes loadingPulse {
  0%, 100% { opacity: 0.5; }
  50% { opacity: 1; }
}

/* 淡入淡出过渡 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.4s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* ===== 电影级全局动画 ===== */

/* 胶片颗粒感 */
.game::after {
  content: '';
  position: fixed;
  inset: 0;
  z-index: 999;
  pointer-events: none;
  opacity: 0.03;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
  background-size: 128px;
  animation: grainShift 0.5s steps(4) infinite;
}
@keyframes grainShift {
  0% { transform: translate(0, 0); }
  25% { transform: translate(-2px, 1px); }
  50% { transform: translate(1px, -1px); }
  75% { transform: translate(-1px, 2px); }
}

/* 呼吸式环境光 */
.game::before {
  content: '';
  position: fixed;
  inset: 0;
  z-index: 1;
  pointer-events: none;
  background: radial-gradient(ellipse at 50% 40%, rgba(232, 180, 80, 0.04) 0%, transparent 60%);
  animation: ambientBreathe 6s ease-in-out infinite;
}
@keyframes ambientBreathe {
  0%, 100% { opacity: 0.5; transform: scale(1); }
  50% { opacity: 1; transform: scale(1.05); }
}

/* 场景切换时的墨幕效果 */
@keyframes inkWash {
  0% { clip-path: circle(0% at 50% 50%); }
  50% { clip-path: circle(70% at 50% 50%); }
  100% { clip-path: circle(100% at 50% 50%); }
}

/* 碎片弹窗光晕 */
.fragment-popup .popup-icon {
  animation: fragmentGlow 3s ease-in-out infinite;
}
@keyframes fragmentGlow {
  0%, 100% { filter: drop-shadow(0 0 8px rgba(232,180,80,0.3)); }
  50% { filter: drop-shadow(0 0 20px rgba(232,180,80,0.6)); }
}

/* 聊天消息进场动画 */
.chat-msg {
  animation: msgSlideIn 0.3s ease-out;
}
@keyframes msgSlideIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

/* 发送按钮脉冲 */
.send-btn:not(:disabled):hover {
  animation: sendPulse 0.6s ease;
}
@keyframes sendPulse {
  0% { box-shadow: 0 0 0 0 rgba(232, 180, 80, 0.4); }
  70% { box-shadow: 0 0 0 10px rgba(232, 180, 80, 0); }
  100% { box-shadow: 0 0 0 0 rgba(232, 180, 80, 0); }
}


.butterfly-btn {
  font-size: 12px;
  color: rgba(180, 160, 255, 0.8);
  cursor: pointer;
  padding: 2px 8px;
  border-radius: 4px;
  transition: all 0.2s;
}
.butterfly-btn:hover {
  background: rgba(180, 160, 255, 0.15);
}
.butterfly-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  z-index: 200;
  display: flex;
  align-items: center;
  justify-content: center;
}
.butterfly-overlay .butterfly-panel {
  background: rgba(10, 10, 30, 0.95);
  border: 1px solid rgba(100, 150, 255, 0.2);
  border-radius: 16px;
  max-width: 500px;
  width: 90%;
  max-height: 80vh;
  overflow-y: auto;
}

.timeline-btn, .log-btn {
  font-size: 12px;
  cursor: pointer;
  padding: 2px 8px;
  border-radius: 4px;
  transition: all 0.2s;
}
.timeline-btn {
  color: rgba(100, 200, 150, 0.8);
}
.timeline-btn:hover {
  background: rgba(100, 200, 150, 0.15);
}
.log-btn {
  color: rgba(255, 215, 100, 0.8);
}
.log-btn:hover {
  background: rgba(255, 215, 100, 0.15);
}
</style>
