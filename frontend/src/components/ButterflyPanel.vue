<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'

interface ButterflyRule {
  id: string
  trigger_scene: string
  trigger_choice: string
  triggered: boolean
  effects_count: number
  target_scenes: string[]
}

const props = defineProps<{
  gameState: Record<string, any> | null
}>()

const rules = ref<ButterflyRule[]>([])
const triggeredCount = ref(0)
const totalRules = ref(0)
const loading = ref(false)

const sceneNames: Record<string, string> = {
  scene_1972: '1972 西安老巷',
  scene_1990: '1990 深圳站',
  scene_2024: '2024 城中村',
  scene_2050: '2050 颁奖礼',
  scene_2089: '2089 实验室',
}

const choiceNames: Record<string, string> = {
  encourage_art: '鼓励传承手艺',
  discourage_art: '劝说放弃手艺',
  talk_to_stranger: '与陌生人交谈',
  ignore_stranger: '忽略陌生人',
  found_letter: '发现信件',
  help_elderly: '帮助老人',
  accept_award: '接受奖项',
  reject_award: '拒绝奖项',
  mention_xiaoyu: '提到小雨',
}

async function fetchStatus() {
  if (!props.gameState) return
  loading.value = true
  try {
    const baseURL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
    const res = await fetch(`${baseURL}/api/butterfly/status`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ game_state: props.gameState }),
    })
    const data = await res.json()
    rules.value = data.rules
    triggeredCount.value = data.triggered_count
    totalRules.value = data.total_rules
  } catch { /* ignore */ }
  loading.value = false
}

onMounted(fetchStatus)
watch(() => props.gameState?.butterfly_choices, fetchStatus, { deep: true })

defineExpose({ refresh: fetchStatus })
</script>

<template>
  <div class="butterfly-panel">
    <div class="butterfly-header">
      <span class="butterfly-icon">🦋</span>
      <span class="butterfly-title">蝴蝶效应</span>
      <span class="butterfly-count">{{ triggeredCount }}/{{ totalRules }}</span>
    </div>

    <div class="butterfly-hint" v-if="triggeredCount === 0">
      你的选择会影响未来的剧情……
    </div>

    <div class="butterfly-rules">
      <div
        v-for="rule in rules"
        :key="rule.id"
        class="butterfly-rule"
        :class="{ triggered: rule.triggered }"
      >
        <div class="rule-trigger">
          <span class="rule-icon">{{ rule.triggered ? '🦋' : '○' }}</span>
          <span class="rule-scene">{{ sceneNames[rule.trigger_scene] || rule.trigger_scene }}</span>
          <span class="rule-choice">{{ choiceNames[rule.trigger_choice] || rule.trigger_choice }}</span>
        </div>
        <div class="rule-arrow" v-if="rule.triggered">→</div>
        <div class="rule-effects" v-if="rule.triggered">
          <span
            v-for="scene in rule.target_scenes"
            :key="scene"
            class="effect-target"
          >
            {{ sceneNames[scene] || scene }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.butterfly-panel {
  padding: 16px;
  font-family: 'Noto Serif SC', serif;
}

.butterfly-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.butterfly-icon {
  font-size: 20px;
}

.butterfly-title {
  font-size: 16px;
  color: #e0e0ff;
  letter-spacing: 2px;
}

.butterfly-count {
  margin-left: auto;
  font-size: 13px;
  color: rgba(150, 170, 220, 0.6);
}

.butterfly-hint {
  font-size: 13px;
  color: rgba(150, 170, 220, 0.4);
  text-align: center;
  padding: 20px 0;
}

.butterfly-rules {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.butterfly-rule {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.05);
  transition: all 0.3s;
}

.butterfly-rule.triggered {
  background: rgba(100, 200, 150, 0.08);
  border-color: rgba(100, 200, 150, 0.2);
}

.rule-trigger {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.rule-icon {
  font-size: 14px;
}

.rule-scene {
  font-size: 12px;
  color: rgba(150, 170, 220, 0.6);
}

.rule-choice {
  font-size: 12px;
  color: #e0e0ff;
}

.rule-arrow {
  color: rgba(100, 200, 150, 0.6);
  font-size: 14px;
}

.rule-effects {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.effect-target {
  font-size: 11px;
  color: rgba(100, 200, 150, 0.8);
  background: rgba(100, 200, 150, 0.1);
  padding: 2px 8px;
  border-radius: 4px;
}
</style>
