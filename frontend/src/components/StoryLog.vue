<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

interface LogEntry {
  time: string
  type: 'dialogue' | 'choice' | 'fragment' | 'scene' | 'butterfly' | 'system'
  scene?: string
  npc?: string
  content: string
  icon: string
}

const props = defineProps<{
  gameState: Record<string, any> | null
  chatHistory: Array<{ role: string; content: string; npcName?: string }>
}>()

const emit = defineEmits<{
  close: []
}>()

const filter = ref<string>('all')

const sceneNames: Record<string, string> = {
  scene_1972: '1972 西安老巷',
  scene_1990: '1990 深圳站',
  scene_2024: '2024 城中村',
  scene_2050: '2050 颁奖礼',
  scene_2089: '2089 实验室',
}

const iconMap: Record<string, string> = {
  dialogue: '💬',
  choice: '🔀',
  fragment: '✨',
  scene: '🏙',
  butterfly: '🦋',
  system: '📝',
}

function buildLog(): LogEntry[] {
  const entries: LogEntry[] = []
  const gs = props.gameState
  if (!gs) return entries

  // 从聊天历史提取对话
  for (const msg of props.chatHistory) {
    if (msg.role === 'system') {
      entries.push({
        time: '',
        type: 'system',
        content: msg.content,
        icon: '📝',
      })
    } else if (msg.role === 'npc') {
      entries.push({
        time: '',
        type: 'dialogue',
        npc: msg.npcName,
        content: msg.content,
        icon: '💬',
      })
    }
  }

  // 从蝴蝶选择提取关键决策
  const choices = gs.butterfly_choices || {}
  for (const [scene, choice] of Object.entries(choices)) {
    entries.push({
      time: '',
      type: 'choice',
      scene,
      content: `在${sceneNames[scene] || scene}做出了选择`,
      icon: '🔀',
    })
  }

  // 从碎片状态提取收集记录
  const fragments = gs.fragment_states || {}
  for (const [id, frag] of Object.entries(fragments)) {
    if ((frag as any)?.collected) {
      entries.push({
        time: '',
        type: 'fragment',
        content: `收集碎片: ${(frag as any).title || id}`,
        icon: '✨',
      })
    }
  }

  return entries
}

const logEntries = computed(() => {
  const all = buildLog()
  if (filter.value === 'all') return all
  return all.filter(e => e.type === filter.value)
})

const filterOptions = [
  { value: 'all', label: '全部', icon: '📋' },
  { value: 'dialogue', label: '对话', icon: '💬' },
  { value: 'choice', label: '选择', icon: '🔀' },
  { value: 'fragment', label: '碎片', icon: '✨' },
  { value: 'system', label: '系统', icon: '📝' },
]
</script>

<template>
  <div class="log-overlay" @click.self="emit('close')">
    <div class="log-panel">
      <div class="log-header">
        <h2>📜 剧情日志</h2>
        <button class="close-btn" @click="emit('close')">✕</button>
      </div>

      <div class="log-filters">
        <button
          v-for="opt in filterOptions"
          :key="opt.value"
          class="filter-btn"
          :class="{ active: filter === opt.value }"
          @click="filter = opt.value"
        >
          {{ opt.icon }} {{ opt.label }}
        </button>
      </div>

      <div class="log-content" v-if="logEntries.length">
        <div
          v-for="(entry, i) in logEntries"
          :key="i"
          class="log-entry"
          :class="entry.type"
        >
          <span class="entry-icon">{{ entry.icon }}</span>
          <div class="entry-body">
            <span class="entry-meta" v-if="entry.npc || entry.scene">
              <span v-if="entry.npc" class="entry-npc">{{ entry.npc }}</span>
              <span v-if="entry.scene" class="entry-scene">{{ sceneNames[entry.scene] || entry.scene }}</span>
            </span>
            <span class="entry-text">{{ entry.content }}</span>
          </div>
        </div>
      </div>

      <div class="log-empty" v-else>
        <p>暂无记录</p>
        <p class="log-empty-hint">开始探索，你的每一步都会被记录。</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.log-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.75);
  z-index: 200;
  display: flex;
  align-items: center;
  justify-content: center;
}

.log-panel {
  background: rgba(10, 10, 30, 0.97);
  border: 1px solid rgba(100, 150, 255, 0.15);
  border-radius: 16px;
  width: 90%;
  max-width: 600px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  font-family: 'Noto Serif SC', serif;
}

.log-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.log-header h2 {
  margin: 0;
  font-size: 18px;
  color: #e0e0ff;
  letter-spacing: 2px;
}

.close-btn {
  background: none;
  border: none;
  color: rgba(255, 255, 255, 0.4);
  font-size: 18px;
  cursor: pointer;
  padding: 4px 8px;
  transition: color 0.2s;
}
.close-btn:hover { color: #fff; }

.log-filters {
  display: flex;
  gap: 6px;
  padding: 12px 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
  flex-wrap: wrap;
}

.filter-btn {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 6px;
  color: rgba(255, 255, 255, 0.5);
  font-size: 12px;
  padding: 4px 10px;
  cursor: pointer;
  transition: all 0.2s;
  font-family: 'Noto Serif SC', serif;
}
.filter-btn:hover { border-color: rgba(100, 150, 255, 0.3); }
.filter-btn.active {
  background: rgba(100, 150, 255, 0.15);
  border-color: rgba(100, 150, 255, 0.4);
  color: #a0b0ff;
}

.log-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px 20px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.log-entry {
  display: flex;
  gap: 10px;
  padding: 8px 12px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.02);
  transition: background 0.2s;
}
.log-entry:hover { background: rgba(255, 255, 255, 0.04); }

.entry-icon {
  flex-shrink: 0;
  font-size: 14px;
  margin-top: 2px;
}

.entry-body {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.entry-meta {
  display: flex;
  gap: 8px;
  font-size: 11px;
}

.entry-npc {
  color: rgba(232, 180, 80, 0.8);
  font-weight: 500;
}

.entry-scene {
  color: rgba(100, 200, 150, 0.6);
}

.entry-text {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.75);
  line-height: 1.5;
  word-break: break-word;
}

.log-entry.choice .entry-text { color: rgba(180, 160, 255, 0.8); }
.log-entry.fragment .entry-text { color: rgba(255, 215, 100, 0.8); }
.log-entry.system .entry-text { color: rgba(255, 255, 255, 0.4); font-style: italic; }

.log-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: rgba(255, 255, 255, 0.3);
}
.log-empty p { margin: 0; }
.log-empty-hint { font-size: 13px; }

/* 移动端适配 */
@media (max-width: 768px) {
  .story-log { padding: 16px; max-height: 80vh; }
  .story-log h3 { font-size: 16px; }
  .log-filters { gap: 4px; }
  .log-filter-btn { padding: 4px 10px; font-size: 12px; }
  .log-item { padding: 10px; }
}
@media (max-width: 480px) {
  .story-log { padding: 12px; }
  .log-item { padding: 8px; font-size: 13px; }
}
</style>

