<script setup lang="ts">
import { computed, nextTick, onUnmounted, ref, watch } from 'vue'
import NpcAvatar from './NpcAvatar.vue'
import { requestNpcVoice } from '../api'
import { useGameState } from '../composables/useGameState'
import {
  createSceneVoiceIntegration,
  type SceneVoiceIntegration,
} from '../composables/useScene'
import { useSfxBus } from '../composables/useSfxBus'
import { useVoicePlayback } from '../composables/useVoicePlayback'
import type { ChatMessage, DialogueResponse, GameState, NpcSummary } from '../types/game'

export interface SuggestedPrompt {
  fragmentId: string
  name: string
  text: string
}

export interface DialogueTaskFeedback {
  npcId: string
  message: string
}

const props = defineProps<{
  selectedNpc: NpcSummary | null
  gameState: GameState | null
  suggestedPrompts?: SuggestedPrompt[]
  taskFeedback?: DialogueTaskFeedback | null
  voicePlayback?: ReturnType<typeof useVoicePlayback>
  voiceCoordinator?: SceneVoiceIntegration
}>()

const emit = defineEmits<{
  dialogueComplete: [result: DialogueResponse, newlyCollected: boolean, npcId: string]
}>()

const chatContainer = ref<HTMLElement | null>(null)
const playerInput = ref('')
const chatLoading = ref(false)
const visibleFromIndex = ref(0)
const statusFeedback = ref<{ npcId: string; messages: string[] } | null>(null)

const { playSFX } = useSfxBus()
const voice = props.voicePlayback ?? useVoicePlayback()
const voiceCoordinator = props.voiceCoordinator ?? createSceneVoiceIntegration(voice)
const { sendDialogue } = useGameState()
const chatHistory = computed<ChatMessage[]>(() =>
  (props.gameState?.dialogue_history ?? []).slice(visibleFromIndex.value).map((message) => ({
    role: message.role,
    content: message.content,
    npcId: message.npc_id ?? undefined,
    npcName:
      message.npc_id && message.npc_id === props.selectedNpc?.id
        ? props.selectedNpc.name
        : message.role === 'npc'
          ? '记忆中的人'
          : undefined,
    emotion: message.emotion ?? undefined,
  })),
)
const statusMessage = computed(() => {
  const npcId = props.selectedNpc?.id
  if (!npcId) return ''
  const messages = [
    props.taskFeedback?.npcId === npcId ? props.taskFeedback.message : '',
    statusFeedback.value?.npcId === npcId ? statusFeedback.value.messages.join(' · ') : '',
  ].filter(Boolean)
  return messages.join(' · ')
})

function scrollToBottom() {
  nextTick(() => {
    if (chatContainer.value) {
      chatContainer.value.scrollTop = chatContainer.value.scrollHeight
    }
  })
}

const sendMessage = async (text?: string) => {
  const msg = text || playerInput.value.trim()
  if (!msg || !props.selectedNpc || !props.gameState || chatLoading.value) return

  const npc = props.selectedNpc
  const collectedBefore = new Set(props.gameState.collected_fragments)
  playerInput.value = ''
  chatLoading.value = true
  statusFeedback.value = null
  scrollToBottom()

  try {
    const result = await sendDialogue(npc.id, msg)
    const newlyCollected = Boolean(
      result.fragment_revealed &&
        !collectedBefore.has(result.fragment_revealed) &&
        result.state.collected_fragments.includes(result.fragment_revealed),
    )
    const feedback: string[] = []
    if (result.trust_change !== 0) {
      playSFX(result.trust_change > 0 ? 'trust_up' : 'trust_down')
      feedback.push(
        result.trust_change > 0
          ? `${npc.name}愿意多说一些 · 信任 +${result.trust_change}`
          : `${npc.name}收紧了话头 · 信任 ${result.trust_change}`,
      )
    }
    if (newlyCollected && result.fragment_data) {
      feedback.push(`线索归档 · ${result.fragment_data.name}`)
    }
    if (result.degraded) {
      feedback.push('记忆回声暂时不稳定，已切换为角色本地对白。')
    }
    if (props.selectedNpc?.id === npc.id && feedback.length) {
      statusFeedback.value = { npcId: npc.id, messages: feedback }
    }
    const dialogueGeneration = voiceCoordinator.beginDialogueVoice()
    emit('dialogueComplete', result, newlyCollected, npc.id)
    scrollToBottom()
    void requestNpcVoice(result.reply, npc.id, result.npc_mood, 0.5)
      .then((response) => {
        if (props.selectedNpc?.id !== npc.id) {
          return false
        }
        return voiceCoordinator.playDialogueResponse(dialogueGeneration, response.data)
      })
      .catch(() => false)
  } catch (caught: unknown) {
    if (props.selectedNpc?.id === npc.id) {
      statusFeedback.value = {
        npcId: npc.id,
        messages: [(caught as Error).message || '发送失败，请稍后重试。'],
      }
    }
  } finally {
    chatLoading.value = false
  }
}

function stopVoice() {
  voiceCoordinator.cancelPending()
}

function clearHistory() {
  visibleFromIndex.value = props.gameState?.dialogue_history.length ?? 0
  statusFeedback.value = null
  stopVoice()
}

watch(
  () => props.selectedNpc?.id,
  () => {
    statusFeedback.value = null
  },
)

onUnmounted(stopVoice)

defineExpose({ chatHistory, clearHistory, stopVoice })
</script>

<template>
  <div class="chat-panel">
    <!-- 消息列表 -->
    <div class="chat-messages" ref="chatContainer">
      <div v-if="!chatHistory.length && selectedNpc" class="chat-empty">
        <p>与 {{ selectedNpc.name }} 开始对话吧</p>
      </div>
      <div v-for="(msg, i) in chatHistory" :key="i" class="chat-msg" :class="msg.role">
        <NpcAvatar
          v-if="msg.role === 'npc' && msg.npcId"
          :npc-id="msg.npcId"
          :emotion="msg.emotion || 'neutral'"
          :size="28"
          class="msg-avatar"
        />
        <span class="msg-avatar-player" v-else-if="msg.role === 'player'">你</span>
        <div class="msg-body">
          <span class="msg-name" v-if="msg.role === 'npc'">{{ msg.npcName }}</span>
          <span class="msg-name" v-else-if="msg.role === 'player'">你</span>
          <span class="msg-name" v-else>系统</span>
          <span class="msg-text">{{ msg.content }}</span>
        </div>
      </div>
      <div v-if="chatLoading" class="chat-msg npc loading">
        <NpcAvatar
          :npc-id="selectedNpc?.id || ''"
          emotion="neutral"
          :size="28"
          class="msg-avatar"
        />
        <div class="msg-body">
          <span class="msg-name">{{ selectedNpc?.name }}</span>
          <span class="msg-text typing-dots"
            >思考中<span class="dot">.</span><span class="dot">.</span
            ><span class="dot">.</span></span
          >
        </div>
      </div>
      <p v-if="statusMessage" class="chat-status" role="status" aria-live="polite">
        {{ statusMessage }}
      </p>
    </div>

    <!-- 输入框 -->
    <div class="input-area" v-if="selectedNpc">
      <div v-if="suggestedPrompts?.length" class="suggested-prompts" aria-label="可追问的记忆证据">
        <button
          v-for="prompt in suggestedPrompts"
          :key="prompt.fragmentId"
          class="suggested-prompt"
          type="button"
          :disabled="chatLoading"
          @click="sendMessage(prompt.text)"
        >
          <span class="prompt-fragment">{{ prompt.name }}</span>
          <span>{{ prompt.text }}</span>
        </button>
      </div>
      <input
        v-model="playerInput"
        class="chat-input"
        placeholder="说点什么……"
        @keyup.enter="sendMessage()"
        :disabled="chatLoading"
      />
      <button
        class="send-btn"
        @click="sendMessage()"
        :disabled="chatLoading || !playerInput.trim()"
      >
        发送
      </button>
    </div>
  </div>
</template>

<style scoped>
.chat-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  scroll-behavior: smooth;
}

.chat-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: rgba(255, 255, 255, 0.3);
  font-size: 14px;
}

.chat-msg {
  display: flex;
  gap: 8px;
  align-items: flex-start;
}
.chat-msg.npc {
  flex-direction: row;
}
.chat-msg.player {
  flex-direction: row-reverse;
}
.chat-msg.system {
  justify-content: center;
}

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
  overflow-wrap: break-word;
  word-break: break-word;
}

.chat-msg.npc .msg-text {
  background: rgba(232, 180, 80, 0.1);
  border: 1px solid rgba(232, 180, 80, 0.15);
  color: #f0e8d0;
}

.chat-msg.player .msg-text {
  background: rgba(100, 150, 255, 0.15);
  border: 1px solid rgba(100, 150, 255, 0.2);
  color: #c0d0ff;
}

.chat-msg.system .msg-text {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.05);
  color: rgba(255, 255, 255, 0.5);
  font-size: 12px;
}

/* 打字动画 */
.typing-dots .dot {
  animation: dotBlink 1.4s infinite both;
}
.typing-dots .dot:nth-child(2) {
  animation-delay: 0.2s;
}
.typing-dots .dot:nth-child(3) {
  animation-delay: 0.4s;
}
@keyframes dotBlink {
  0%,
  80%,
  100% {
    opacity: 0;
  }
  40% {
    opacity: 1;
  }
}

.chat-status {
  margin: 4px 36px 0;
  color: rgba(224, 184, 115, 0.75);
  font-size: 11px;
  line-height: 1.5;
  text-align: center;
}

/* 输入区 */
.input-area {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 12px 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}

.suggested-prompts {
  display: grid;
  width: 100%;
  gap: 0.42rem;
}

.suggested-prompt {
  display: grid;
  min-height: 44px;
  padding: 0.5rem 0.7rem;
  border: 1px solid rgba(214, 173, 102, 0.38);
  border-left-width: 3px;
  color: rgba(241, 229, 206, 0.9);
  text-align: left;
  background: linear-gradient(90deg, rgba(214, 173, 102, 0.1), rgba(8, 10, 10, 0.74));
  cursor: pointer;
  font: 500 0.78rem/1.45 'Noto Serif SC', serif;
  letter-spacing: 0.03em;
}

.suggested-prompt:hover:not(:disabled),
.suggested-prompt:focus-visible {
  border-color: rgba(241, 229, 206, 0.82);
  background: linear-gradient(90deg, rgba(214, 173, 102, 0.18), rgba(8, 10, 10, 0.88));
  outline: none;
}

.suggested-prompt:disabled {
  cursor: wait;
  opacity: 0.52;
}

.prompt-fragment {
  color: rgba(214, 173, 102, 0.78);
  font: 600 0.54rem/1.35 ui-monospace, monospace;
  letter-spacing: 0.16em;
}

.chat-input {
  flex: 1;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 10px 14px;
  color: #e0e0e0;
  font-size: 14px;
  font-family: 'Noto Serif SC', serif;
  outline: none;
  transition: border-color 0.2s;
}
.chat-input:focus {
  border-color: rgba(100, 150, 255, 0.4);
}
.chat-input::placeholder {
  color: rgba(255, 255, 255, 0.2);
}

.send-btn {
  background: rgba(100, 150, 255, 0.15);
  border: 1px solid rgba(100, 150, 255, 0.25);
  border-radius: 8px;
  color: #a0b0ff;
  padding: 10px 18px;
  cursor: pointer;
  font-size: 13px;
  font-family: 'Noto Serif SC', serif;
  transition: all 0.2s;
}
.send-btn:hover:not(:disabled) {
  background: rgba(100, 150, 255, 0.25);
}
.send-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

/* 移动端适配 */
@media (max-width: 768px) {
  .chat-messages {
    padding: 12px;
    gap: 10px;
  }
  .msg-body {
    max-width: 85%;
  }
  .msg-text {
    font-size: 14px;
    padding: 10px 14px;
  }
  .input-area {
    padding: 10px 12px;
    padding-bottom: max(10px, env(safe-area-inset-bottom));
  }
  .chat-input {
    font-size: 16px;
    padding: 12px 14px;
  } /* 16px防止iOS缩放 */
  .send-btn {
    padding: 12px 20px;
    min-height: 44px;
  }
}

@media (max-width: 480px) {
  .msg-text {
    font-size: 13px;
  }
  .msg-avatar-player {
    width: 24px;
    height: 24px;
    font-size: 10px;
  }
}
</style>
