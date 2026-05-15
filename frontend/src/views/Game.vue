<script setup lang="ts">
import { ref, onMounted, watch, nextTick } from 'vue'
import { useGameState } from '../composables/useGameState'
import { useTypewriter } from '../composables/useTypewriter'
import { chatWithNpc, chatWithNpcStream, getSceneDetail, advanceNarrative, saveGame } from '../api'
import SceneIllustration from '../components/SceneIllustration.vue'
import MemoryProgress from '../components/MemoryProgress.vue'
import type { Scene, NpcSummary, Fragment, ChatMessage, EndingType } from '../types/game'

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

const chatHistory = ref<ChatMessage[]>([])
const chatContainer = ref<HTMLElement | null>(null)

// 场景切换
const sceneTransitioning = ref(false)

// 游戏时间
const playStartTime = Date.now()
const getPlayTime = () => Math.floor((Date.now() - playStartTime) / 1000)

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
    narrativeText.value = narrRes.data.scene_description
    presetOptions.value = narrRes.data.available_actions
    typeStart(narrRes.data.scene_description)
  } catch {
    narrativeText.value = currentScene.value?.description || '场景加载中...'
    typeStart(narrativeText.value)
  } finally {
    setTimeout(() => { sceneTransitioning.value = false }, 600)
  }
}

// 场景切换
const switchScene = async (targetScene: string) => {
  if (!gameState.value || sceneTransitioning.value) return
  sceneTransitioning.value = true
  gameState.value.current_scene = targetScene
  selectedNpc.value = null
  chatHistory.value = []
  await autoSave()
  await loadScene()
}

const selectNpc = (npc: any) => {
  selectedNpc.value = npc
  playerInput.value = ''
}

const sendMessage = async (text?: string) => {
  const msg = text || playerInput.value.trim()
  if (!msg || !selectedNpc.value || !gameState.value || chatLoading.value) return

  playerInput.value = ''
  chatLoading.value = true

  // 添加玩家消息
  chatHistory.value.push({ role: 'player', content: msg })
  addDialogue('player', msg)
  scrollToBottom()

  // 添加 NPC 占位消息
  const npcMsgIndex = chatHistory.value.length
  chatHistory.value.push({ role: 'npc', content: '', npcName: selectedNpc.value.name })

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
        // 用后端解析后的干净文本替换流式拼接文本
        chatHistory.value[npcMsgIndex].content = data.reply
        addDialogue('npc', data.reply)

        if (data.trust_change !== 0) {
          updateTrust(selectedNpc.value!.id, data.trust_change)
        }

        if (data.fragment_revealed && data.fragment_data) {
          revealFragment(data.fragment_revealed)
          const trust = gameState.value!.npc_trust[selectedNpc.value!.id] || 30
          if (trust >= 60) {
            collectFragment(data.fragment_revealed)
            popupFragment.value = { ...data.fragment_data, just_collected: true }
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

watch(() => gameState.value?.collected_fragments?.length, (newVal) => {
  if (newVal && newVal >= totalFragments.value && totalFragments.value > 0) {
    // 所有碎片收集完成
    narrativeText.value = '所有记忆碎片已经收集完毕……陈爷爷的记忆正在恢复。那些消散的光影，重新聚合成完整的画面。'
    typeStart(narrativeText.value)
    setTimeout(() => emit('ending', 'hope'), 4000)
  } else if (newVal) {
    // 每收集一个碎片自动存档
    autoSave()
    // 检查是否触发结局（场景切换到最后一幕且收集了足够碎片）
    const percent = totalFragments.value > 0 ? (newVal / totalFragments.value) * 100 : 0
    if (gameState.value?.current_scene === 'scene_2089' && percent >= 40) {
      narrativeText.value = '记忆修复程序启动……碎片正在聚合……'
      typeStart(narrativeText.value)
      const endingType = percent >= 80 ? 'hope' : 'bittersweet'
      setTimeout(() => emit('ending', endingType), 5000)
    }
  }
})

// 场景切换到最后一幕且碎片不足 40% 时触发悲剧结局
watch(() => gameState.value?.current_scene, (newScene) => {
  if (newScene === 'scene_2089' && gameState.value) {
    const percent = totalFragments.value > 0
      ? (gameState.value.collected_fragments.length / totalFragments.value) * 100
      : 0
    if (percent < 40 && gameState.value.collected_fragments.length > 0) {
      narrativeText.value = '记忆碎片太少了……修复程序难以启动……'
      typeStart(narrativeText.value)
      setTimeout(() => emit('ending', 'tragic'), 5000)
    }
  }
})
</script>

<template>
  <div class="game" v-if="gameState">
    <!-- 顶部状态栏 -->
    <header class="top-bar">
      <div class="scene-info">
        <span class="scene-time">{{ currentScene?.time_period || '...' }}</span>
        <span class="scene-title">{{ currentScene?.title || '加载中...' }}</span>
      </div>
      <div class="status-right">
        <!-- 场景导航 -->
        <div class="scene-nav" v-if="currentScene?.exits">
          <button
            v-for="(target, dir) in currentScene.exits"
            :key="dir"
            class="nav-btn"
            @click="switchScene(target)"
            :disabled="sceneTransitioning"
          >
            {{ dir === 'back' ? '◂ 返回' : '前进 ▸' }}
          </button>
        </div>
        <div class="fragment-counter" @click="showInventory = !showInventory">
          🧩 {{ collectedCount }}/{{ totalFragments }}
        </div>
      </div>
    </header>

    <!-- 主游戏区域 -->
    <div class="main-area">
      <!-- 左侧：场景与叙事 -->
      <div class="scene-panel">
        <!-- 场景插画 -->
        <div class="scene-illustration-box">
          <SceneIllustration :scene-id="gameState.current_scene" />
          <div class="scene-overlay">
            <span class="scene-location">{{ currentScene?.location || '' }}</span>
          </div>
        </div>

        <div class="narrative-box">
          <div class="narrative-text" @click="isTyping ? typeSkip() : null">
            {{ typewriterText }}<span v-if="isTyping" class="cursor">|</span>
          </div>
        </div>

        <!-- NPC选择 -->
        <div class="npc-list">
          <div
            v-for="npc in currentNpcs"
            :key="npc.id"
            class="npc-card"
            :class="{ active: selectedNpc?.id === npc.id }"
            @click="selectNpc(npc)"
          >
            <div class="npc-avatar">{{ npc.name[0] }}</div>
            <div class="npc-info">
              <span class="npc-name">{{ npc.name }}</span>
              <span class="npc-title">{{ npc.title }}</span>
              <span class="npc-trust" :style="{ color: getTrustLevel(npc.id).color }">
                {{ getTrustLevel(npc.id).label }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧：对话面板 -->
      <div class="dialogue-panel">
        <div class="dialogue-header" v-if="selectedNpc">
          <span>与 {{ selectedNpc.name }} 对话</span>
        </div>
        <div class="dialogue-header" v-else>
          <span>选择一个角色开始对话</span>
        </div>

        <div class="chat-area" ref="chatContainer">
          <div v-if="!selectedNpc" class="empty-chat">
            <p>👆 点击左侧角色头像开始对话</p>
          </div>
          <div
            v-for="(msg, i) in chatHistory"
            :key="i"
            class="chat-msg"
            :class="msg.role"
          >
            <span class="msg-name" v-if="msg.role === 'npc'">{{ msg.npcName }}</span>
            <span class="msg-name" v-else-if="msg.role === 'player'">你</span>
            <span class="msg-name" v-else>系统</span>
            <span class="msg-text">{{ msg.content }}</span>
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
            @click="sendMessage(opt)"
            :disabled="chatLoading"
          >
            {{ opt }}
          </button>
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
          <button class="send-btn" @click="sendMessage()" :disabled="chatLoading || !playerInput.trim()">
            ➤
          </button>
        </div>
      </div>
    </div>

    <!-- 场景切换动画 -->
    <div class="scene-transition" :class="{ active: sceneTransitioning }">
      <div class="transition-text">记忆流转...</div>
    </div>

    <!-- 碎片弹窗 -->
    <div class="popup-overlay" v-if="showFragmentPopup" @click.self="showFragmentPopup = false">
      <div class="fragment-popup">
        <div class="popup-icon">🧩</div>
        <h3>{{ popupFragment?.just_collected ? '获得记忆碎片！' : '发现记忆碎片线索' }}</h3>
        <h2>{{ popupFragment?.name }}</h2>
        <p class="fragment-desc">{{ popupFragment?.description }}</p>
        <p class="fragment-memory" v-if="popupFragment?.memory_text && popupFragment?.just_collected">
          「{{ popupFragment.memory_text }}」
        </p>
        <button class="btn-close" @click="popupFragment?.just_collected ? (showFragmentPopup = false) : collectCurrentFragment(popupFragment?.id)">
          {{ popupFragment?.just_collected ? '继续探索' : '收集碎片' }}
        </button>
      </div>
    </div>

    <!-- 背包面板 -->
    <div class="inventory-panel" v-if="showInventory">
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
  </div>
</template>

<style scoped>
.game {
  width: 100vw;
  height: 100vh;
  background: linear-gradient(135deg, #0a0a1a, #1a1a3e);
  color: #e0e0ff;
  font-family: 'Noto Serif SC', serif;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* 顶部状态栏 */
.top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 24px;
  background: rgba(0, 0, 0, 0.3);
  border-bottom: 1px solid rgba(100, 150, 255, 0.15);
}

.scene-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.scene-time {
  background: rgba(58, 95, 205, 0.3);
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 13px;
  color: #60a5fa;
}

.scene-title {
  font-size: 18px;
  letter-spacing: 2px;
}

.fragment-counter {
  cursor: pointer;
  font-size: 15px;
  padding: 4px 12px;
  border-radius: 6px;
  background: rgba(100, 150, 255, 0.1);
}

.scene-nav {
  display: flex;
  gap: 6px;
}

.nav-btn {
  padding: 4px 14px;
  border-radius: 6px;
  border: 1px solid rgba(100, 150, 255, 0.25);
  background: rgba(100, 150, 255, 0.08);
  color: rgba(200, 210, 255, 0.8);
  font-size: 13px;
  cursor: pointer;
  font-family: 'Noto Serif SC', serif;
  transition: all 0.2s;
}

.nav-btn:hover {
  background: rgba(100, 150, 255, 0.15);
  border-color: rgba(100, 150, 255, 0.4);
}

.nav-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

/* 场景切换动画 */
.scene-transition {
  position: fixed;
  inset: 0;
  background: #000;
  z-index: 80;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.5s ease;
}

.scene-transition.active {
  opacity: 1;
  pointer-events: all;
}

.transition-text {
  font-size: 20px;
  color: rgba(200, 210, 255, 0.6);
  letter-spacing: 4px;
  animation: pulse 1.5s ease-in-out infinite;
}

/* 主游戏区域 */
.main-area {
  flex: 1;
  display: flex;
  gap: 0;
  overflow: hidden;
}

/* 左侧场景面板 */
.scene-panel {
  width: 40%;
  display: flex;
  flex-direction: column;
  border-right: 1px solid rgba(100, 150, 255, 0.1);
}

.scene-illustration-box {
  position: relative;
  height: 200px;
  min-height: 200px;
  overflow: hidden;
  border-bottom: 1px solid rgba(100, 150, 255, 0.1);
}

.scene-illustration-box :deep(.scene-illustration) {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.scene-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 8px 16px;
  background: linear-gradient(transparent, rgba(0, 0, 0, 0.6));
}

.scene-location {
  font-size: 12px;
  color: rgba(200, 210, 255, 0.6);
  letter-spacing: 1px;
}

.narrative-box {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
  min-height: 0;
}

.narrative-text {
  font-size: 16px;
  line-height: 2;
  color: rgba(200, 210, 255, 0.85);
  cursor: pointer;
}

.cursor {
  animation: blink 1s infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

.npc-list {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.npc-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(100, 150, 255, 0.1);
  cursor: pointer;
  transition: all 0.2s;
}

.npc-card:hover {
  background: rgba(255, 255, 255, 0.08);
}

.npc-card.active {
  background: rgba(58, 95, 205, 0.2);
  border-color: rgba(58, 95, 205, 0.5);
}

.npc-avatar {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: linear-gradient(135deg, #3a5fcd, #5078e0);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  font-weight: bold;
}

.npc-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.npc-name {
  font-size: 15px;
  font-weight: 600;
}

.npc-title {
  font-size: 12px;
  color: rgba(150, 170, 220, 0.6);
}

.npc-trust {
  font-size: 12px;
}

/* 右侧对话面板 */
.dialogue-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.dialogue-header {
  padding: 14px 20px;
  font-size: 14px;
  color: rgba(150, 170, 220, 0.7);
  border-bottom: 1px solid rgba(100, 150, 255, 0.1);
}

.chat-area {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.empty-chat {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: rgba(150, 170, 220, 0.4);
  font-size: 15px;
}

.chat-msg {
  max-width: 85%;
  padding: 10px 16px;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.7;
}

.chat-msg.player {
  align-self: flex-end;
  background: rgba(58, 95, 205, 0.3);
  border: 1px solid rgba(58, 95, 205, 0.4);
}

.chat-msg.npc {
  align-self: flex-start;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(100, 150, 255, 0.15);
}

.chat-msg.system {
  align-self: center;
  background: rgba(255, 200, 50, 0.1);
  border: 1px solid rgba(255, 200, 50, 0.2);
  font-size: 13px;
  color: rgba(255, 200, 50, 0.8);
}

.msg-name {
  display: block;
  font-size: 12px;
  color: rgba(150, 170, 220, 0.5);
  margin-bottom: 4px;
}

.typing-dots .dot {
  animation: dotFlash 1.4s infinite;
}

.typing-dots .dot:nth-child(2) { animation-delay: 0.2s; }
.typing-dots .dot:nth-child(3) { animation-delay: 0.4s; }

@keyframes dotFlash {
  0%, 100% { opacity: 0; }
  50% { opacity: 1; }
}

/* 预设选项 */
.preset-options {
  padding: 8px 20px;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.preset-btn {
  padding: 6px 16px;
  border-radius: 16px;
  border: 1px solid rgba(100, 150, 255, 0.25);
  background: rgba(100, 150, 255, 0.08);
  color: rgba(200, 210, 255, 0.8);
  font-size: 13px;
  cursor: pointer;
  font-family: 'Noto Serif SC', serif;
  transition: all 0.2s;
}

.preset-btn:hover {
  background: rgba(100, 150, 255, 0.15);
  border-color: rgba(100, 150, 255, 0.4);
}

/* 输入框 */
.input-area {
  display: flex;
  gap: 8px;
  padding: 12px 20px 16px;
  border-top: 1px solid rgba(100, 150, 255, 0.1);
}

.chat-input {
  flex: 1;
  padding: 10px 16px;
  border-radius: 8px;
  border: 1px solid rgba(100, 150, 255, 0.2);
  background: rgba(0, 0, 0, 0.3);
  color: #e0e0ff;
  font-size: 14px;
  font-family: 'Noto Serif SC', serif;
  outline: none;
}

.chat-input:focus {
  border-color: rgba(58, 95, 205, 0.5);
}

.send-btn {
  width: 44px;
  height: 44px;
  border-radius: 8px;
  border: none;
  background: linear-gradient(135deg, #3a5fcd, #5078e0);
  color: white;
  font-size: 18px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.send-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

/* ── 移动端适配 ── */
@media (max-width: 768px) {
  .main-area {
    flex-direction: column;
  }

  .scene-panel {
    width: 100%;
    height: auto;
    max-height: 40vh;
    border-right: none;
    border-bottom: 1px solid rgba(100, 150, 255, 0.1);
  }

  .scene-illustration-box {
    height: 140px;
    min-height: 140px;
  }

  .narrative-box {
    padding: 12px 16px;
    max-height: 80px;
    overflow-y: auto;
  }

  .narrative-text {
    font-size: 13px;
    line-height: 1.7;
  }

  .npc-list {
    flex-direction: row;
    overflow-x: auto;
    padding: 8px 12px;
    gap: 6px;
  }

  .npc-card {
    min-width: 120px;
    padding: 8px 10px;
  }

  .npc-avatar {
    width: 32px;
    height: 32px;
    font-size: 14px;
  }

  .dialogue-panel {
    flex: 1;
    min-height: 0;
  }

  .chat-area {
    padding: 12px;
    gap: 8px;
  }

  .chat-msg {
    max-width: 90%;
    padding: 8px 12px;
    font-size: 13px;
  }

  .input-area {
    padding: 8px 12px;
  }

  .chat-input {
    font-size: 14px;
    padding: 10px 14px;
  }

  .top-bar {
    padding: 8px 12px;
  }

  .scene-title {
    font-size: 14px;
  }

  .scene-time {
    font-size: 11px;
    padding: 2px 8px;
  }

  .fragment-popup {
    width: 90%;
    padding: 24px;
  }

  .popup-icon {
    font-size: 40px;
  }

  .popup-title {
    font-size: 20px;
  }

  .inventory-panel {
    width: 85%;
    max-height: 70vh;
  }
}

/* 碎片弹窗 */
.popup-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
  backdrop-filter: blur(4px);
}

.fragment-popup {
  background: linear-gradient(135deg, #1a1a3e, #2a2a5e);
  border: 1px solid rgba(100, 150, 255, 0.3);
  border-radius: 16px;
  padding: 40px;
  text-align: center;
  max-width: 420px;
  box-shadow: 0 0 60px rgba(58, 95, 205, 0.3);
}

.popup-icon {
  font-size: 48px;
  margin-bottom: 12px;
}

.fragment-popup h3 {
  color: rgba(150, 170, 220, 0.7);
  font-size: 14px;
  margin: 0 0 8px;
}

.fragment-popup h2 {
  font-size: 24px;
  color: #60a5fa;
  margin: 0 0 16px;
}

.fragment-desc {
  color: rgba(200, 210, 255, 0.7);
  font-size: 14px;
  line-height: 1.8;
  margin-bottom: 12px;
}

.fragment-memory {
  color: rgba(255, 200, 100, 0.8);
  font-size: 14px;
  font-style: italic;
  line-height: 1.8;
  margin-bottom: 24px;
  padding: 12px;
  background: rgba(255, 200, 100, 0.05);
  border-radius: 8px;
  border-left: 3px solid rgba(255, 200, 100, 0.3);
}

.btn-close {
  padding: 10px 32px;
  border-radius: 8px;
  border: none;
  background: linear-gradient(135deg, #3a5fcd, #5078e0);
  color: white;
  font-size: 15px;
  cursor: pointer;
  font-family: 'Noto Serif SC', serif;
}

/* 背包面板 */
.inventory-panel {
  position: fixed;
  right: 0;
  top: 0;
  bottom: 0;
  width: 320px;
  background: rgba(10, 10, 30, 0.95);
  border-left: 1px solid rgba(100, 150, 255, 0.2);
  z-index: 50;
  display: flex;
  flex-direction: column;
  backdrop-filter: blur(10px);
}

.inventory-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid rgba(100, 150, 255, 0.15);
}

.inventory-progress {
  padding: 12px 16px;
  border-bottom: 1px solid rgba(100, 150, 255, 0.1);
}

.inventory-header h3 {
  margin: 0;
  font-size: 16px;
}

.inventory-header button {
  background: none;
  border: none;
  color: rgba(150, 170, 220, 0.6);
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
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(100, 150, 255, 0.08);
}

.inventory-item.collected {
  background: rgba(58, 95, 205, 0.1);
  border-color: rgba(58, 95, 205, 0.25);
}

.frag-icon {
  font-size: 24px;
}

.frag-name {
  flex: 1;
  font-size: 14px;
}

.frag-scene {
  font-size: 11px;
  color: rgba(150, 170, 220, 0.4);
}

/* 滚动条 */
::-webkit-scrollbar {
  width: 6px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: rgba(100, 150, 255, 0.2);
  border-radius: 3px;
}
</style>
