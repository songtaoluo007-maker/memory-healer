<script setup lang="ts">
/**
 * 任务追踪条 — 固定在游戏画面上方，显示当前目标
 * 皮影戏风格：半透明卷轴条，提示下一步行动
 */
import type { Quest } from '../composables/useQuests'

defineProps<{
  mainQuest: Quest | null
  currentHint: string
  actTitle: string
}>()

const emit = defineEmits<{
  openPanel: []
}>()
</script>

<template>
  <div class="quest-tracker" @click="emit('openPanel')">
    <div class="tracker-act">{{ actTitle }}</div>
    <div class="tracker-hint">
      <span class="hint-icon">✦</span>
      <span class="hint-text">{{ currentHint }}</span>
    </div>
    <div class="tracker-expand">任务 ▾</div>
  </div>
</template>

<style scoped>
.quest-tracker {
  position: absolute;
  top: 8px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 20;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 6px 16px;
  background: rgba(10, 8, 18, 0.8);
  border: 1px solid rgba(255, 180, 60, 0.25);
  border-radius: 20px;
  backdrop-filter: blur(8px);
  cursor: pointer;
  transition: all 0.3s;
  max-width: 90%;
}

.quest-tracker:hover {
  border-color: rgba(255, 180, 60, 0.5);
  background: rgba(10, 8, 18, 0.9);
}

.tracker-act {
  font-size: 11px;
  color: #c9a44a;
  font-family: 'Noto Serif SC', serif;
  white-space: nowrap;
  padding-right: 10px;
  border-right: 1px solid rgba(255, 180, 60, 0.2);
}

.tracker-hint {
  display: flex;
  align-items: center;
  gap: 6px;
  flex: 1;
  min-width: 0;
}

.hint-icon {
  color: #ffd700;
  font-size: 10px;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

.hint-text {
  font-size: 12px;
  color: #c0b8d0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tracker-expand {
  font-size: 11px;
  color: #8a8090;
  white-space: nowrap;
  padding-left: 10px;
  border-left: 1px solid rgba(255, 255, 255, 0.1);
}
</style>
