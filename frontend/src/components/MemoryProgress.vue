<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  collected: number
  total: number
}>()

const percent = computed(() => {
  if (!props.total) return 0
  return Math.round((props.collected / props.total) * 100)
})

const label = computed(() => {
  if (percent.value >= 100) return '记忆完整'
  if (percent.value >= 60) return '记忆正在恢复...'
  if (percent.value >= 30) return '记忆碎片浮现...'
  return '记忆碎片稀少'
})
</script>

<template>
  <div class="memory-progress">
    <div class="progress-header">
      <span class="progress-label">记忆完整度</span>
      <span class="progress-percent">{{ percent }}%</span>
    </div>
    <div class="progress-bar">
      <div class="progress-fill" :style="{ width: percent + '%' }" />
    </div>
    <div class="progress-hint">{{ label }}</div>
  </div>
</template>

<style scoped>
.memory-progress {
  padding: 8px 12px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 8px;
  border: 1px solid rgba(100, 150, 255, 0.1);
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.progress-label {
  font-size: 11px;
  color: rgba(150, 170, 220, 0.5);
}

.progress-percent {
  font-size: 12px;
  color: #60a5fa;
  font-weight: 600;
}

.progress-bar {
  height: 4px;
  background: rgba(100, 150, 255, 0.1);
  border-radius: 2px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #3a5fcd, #60a5fa);
  border-radius: 2px;
  transition: width 0.5s ease;
}

.progress-hint {
  font-size: 11px;
  color: rgba(150, 170, 220, 0.4);
  margin-top: 4px;
}
</style>
