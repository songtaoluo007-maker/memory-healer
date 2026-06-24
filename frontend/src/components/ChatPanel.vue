<script setup lang="ts">
import { ref, nextTick, watch } from 'vue'
import { chatWithNpcStream } from '../api'
import { useAudio } from '../composables/useAudio'
import type { ChatMessage, NpcSummary, Fragment, EndingType } from '../types/game'

const props = defineProps<{
  selectedNpc: NpcSummary | null
  gameState: Record<string, any> | null
  totalFragments: number
}>()

const emit = defineEmits<{
  trustChange: [npcId: string, change: number]
  fragmentReveal: [fragmentId: string, fragmentData: any]
  ending: [type: EndingType]
  choiceDetected: [msg: string, npcId: string]
}>()

const chatHistory = ref<ChatMessage[]>([])
const chatContainer = ref<HTMLElement | null>(null)
const playerInput = ref('')
const chatLoading = ref(false)
const presetOptions = ref<string[]>([])

const { speak, stopSpeak, playSFX } = useAudio()

function scrollToBottom() {
  nextTick(() => {
    if (chatContainer.value) {
      chatContainer.value.scrollTop = chatContainer.value.scrollHeight
    }
  })
}

function detectAndRecordChoice(playerMsg: string, npcId: string) {
  emit('choiceDetected', playerMsg, npcId)
}

const sendMessage = async (text?: string) => {
  const msg = text || playerInput.value.trim()
  if (!msg || !props.selectedNpc || !props.gameState || chatLoading.value) return

  playerInput.value = ''
  chatLoading.value = true

  chatHistory.value.push({ role: 'player', content: msg })
  detectAndRecordChoice(msg, props.selectedNpc.id)
  scrollToBottom()

  const npcMsgIndex = chatHistory.value.length
  chatHistory.value.push({
    role: 'npc',
    content: '',
    npcName: props.selectedNpc.name,
    npcId: props.selectedNpc.id,
    emotion: 'neutral',
  })

  try {
    chatWithNpcStream(
      { npc_id: props.selectedNpc.id, player_input: msg, game_state: props.gameState },
      (token) => {
        chatHistory.value[npcMsgIndex].content += token
        scrollToBottom()
      },
      (data) => {
        chatHistory.value[npcMsgIndex].content = data.reply
        chatHistory.value[npcMsgIndex].emotion = data.npc_mood || 'neutral'

        speak(data.reply, props.selectedNpc!.id)

        if (data.trust_change !== 0) {
          emit('trustChange', props.selectedNpc!.id, data.trust_change)
          playSFX(data.trust_change > 0 ? 'trust_up' : 'trust_down')
        }

        if (data.fragment_revealed && data.fragment_data) {
          emit('fragmentReveal', data.fragment_revealed, data.fragment_data)
        }

        if (data.preset_dialogues?.length) {
          presetOptions.value = data.preset_dialogues
        }

        chatLoading.value = false
      },
      (error) => {
        chatHistory.value[npcMsgIndex].content = '[连接中断]'
        chatLoading.value = false
      }
    )
  } catch {
    chatHistory.value[npcMsgIndex].content = '[发送失败]'
    chatLoading.value = false
  }
}

function clearHistory() {
  chatHistory.value = []
  presetOptions.value = []
  stopSpeak()
}

defineExpose({ chatHistory, clearHistory })
</script>

<template>
  <div class="chat-panel">
    <!-- 消息列表 -->
    <div class="chat-messages" ref="chatContainer">
      <div v-if="!chatHistory.length && selectedNpc" class="chat-empty">
        <p>与 {{ selectedNpc.name }} 开始对话吧</p>
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
        <NpcAvatar :npc-id="selectedNpc?.id || ''" emotion="neutral" :size="28" class="msg-avatar" />
        <div class="msg-body">
          <span class="msg-name">{{ selectedNpc?.name }}</span>
          <span class="msg-text typing-dots">思考中<span class="dot">.</span><span class="dot">.</span><span class="dot">.</span></span>
        </div>
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
        placeholder="说点什么……"
        @keyup.enter="sendMessage()"
        :disabled="chatLoading"
      />
      <button class="send-btn" @click="sendMessage()" :disabled="chatLoading || !playerInput.trim()">发送</button>
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
.typing-dots .dot:nth-child(2) { animation-delay: 0.2s; }
.typing-dots .dot:nth-child(3) { animation-delay: 0.4s; }
@keyframes dotBlink {
  0%, 80%, 100% { opacity: 0; }
  40% { opacity: 1; }
}

/* 预设选项 */
.preset-options {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  padding: 8px 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.04);
}

.preset-btn {
  background: rgba(232, 180, 80, 0.08);
  border: 1px solid rgba(232, 180, 80, 0.15);
  border-radius: 16px;
  color: rgba(232, 180, 80, 0.8);
  font-size: 12px;
  padding: 6px 14px;
  cursor: pointer;
  transition: all 0.2s;
  font-family: 'Noto Serif SC', serif;
}
.preset-btn:hover:not(:disabled) {
  background: rgba(232, 180, 80, 0.15);
  border-color: rgba(232, 180, 80, 0.3);
}
.preset-btn:disabled { opacity: 0.4; cursor: not-allowed; }

/* 输入区 */
.input-area {
  display: flex;
  gap: 8px;
  padding: 12px 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
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
.send-btn:disabled { opacity: 0.4; cursor: not-allowed; }

/* 移动端适配 */
@media (max-width: 768px) {
  .chat-messages { padding: 12px; gap: 10px; }
  .msg-body { max-width: 85%; }
  .msg-text { font-size: 14px; padding: 10px 14px; }
  .preset-options { padding: 8px 12px; }
  .preset-btn { padding: 8px 16px; font-size: 13px; min-height: 36px; }
  .input-area { padding: 10px 12px; padding-bottom: max(10px, env(safe-area-inset-bottom)); }
  .chat-input { font-size: 16px; padding: 12px 14px; } /* 16px防止iOS缩放 */
  .send-btn { padding: 12px 20px; min-height: 44px; }
}

@media (max-width: 480px) {
  .msg-text { font-size: 13px; }
  .msg-avatar-player { width: 24px; height: 24px; font-size: 10px; }
  .preset-btn { font-size: 12px; padding: 6px 12px; }
}
</style>
