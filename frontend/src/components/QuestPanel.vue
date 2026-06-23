<script setup lang="ts">
/**
 * 任务追踪面板 — 显示当前主线/支线任务和目标
 * 皮影戏风格：展开在画面右侧，像卷轴一样展开
 */
import { computed } from 'vue'
import type { Quest } from '../composables/useQuests'

const props = defineProps<{
  mainQuest: Quest | null
  sideQuests: Quest[]
  currentHint: string
  actTitle: string
  completedCount: number
  totalCount: number
}>()

const emit = defineEmits<{
  close: []
}>()

const progressPercent = computed(() => {
  if (props.totalCount === 0) return 0
  return Math.round((props.completedCount / props.totalCount) * 100)
})
</script>

<template>
  <div class="quest-panel" @click.self="emit('close')">
    <div class="quest-scroll">
      <!-- 卷轴顶部装饰 -->
      <div class="scroll-top">
        <div class="scroll-rod"></div>
        <h2 class="scroll-title">{{ actTitle }}</h2>
        <div class="scroll-rod"></div>
      </div>

      <!-- 总进度 -->
      <div class="progress-bar">
        <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
        <span class="progress-text">{{ completedCount }}/{{ totalCount }} 任务</span>
      </div>

      <!-- 主线任务 -->
      <div v-if="mainQuest" class="quest-section main">
        <div class="section-badge">主线</div>
        <h3 class="quest-title">{{ mainQuest.title }}</h3>
        <p class="quest-desc">{{ mainQuest.description }}</p>

        <div class="objectives">
          <div
            v-for="obj in mainQuest.objectives"
            :key="obj.id"
            class="objective"
            :class="{ done: obj.completed }"
          >
            <span class="obj-check">{{ obj.completed ? '☑' : '☐' }}</span>
            <span class="obj-text">{{ obj.text }}</span>
          </div>
        </div>

        <!-- 提示 -->
        <div class="hints" v-if="mainQuest.objectives.some(o => !o.completed)">
          <div class="hint-label">💡 提示</div>
          <div
            v-for="(hint, i) in mainQuest.hints"
            :key="i"
            class="hint-text"
          >
            {{ hint }}
          </div>
        </div>
      </div>

      <!-- 支线任务 -->
      <div v-if="sideQuests.length > 0" class="quest-section side">
        <div class="section-badge side-badge">支线</div>
        <div v-for="quest in sideQuests" :key="quest.id" class="side-quest">
          <h4 class="quest-title">{{ quest.title }}</h4>
          <p class="quest-desc">{{ quest.description }}</p>
          <div class="objectives compact">
            <div
              v-for="obj in quest.objectives"
              :key="obj.id"
              class="objective"
              :class="{ done: obj.completed }"
            >
              <span class="obj-check">{{ obj.completed ? '☑' : '☐' }}</span>
              <span class="obj-text">{{ obj.text }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 卷轴底部装饰 -->
      <div class="scroll-bottom">
        <div class="scroll-rod"></div>
      </div>

      <!-- 关闭按钮 -->
      <button class="close-btn" @click="emit('close')">✕</button>
    </div>
  </div>
</template>

<style scoped>
.quest-panel {
  position: fixed;
  inset: 0;
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(2px);
  animation: fadeIn 0.2s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.quest-scroll {
  width: 380px;
  max-height: 85vh;
  overflow-y: auto;
  background: linear-gradient(135deg, #1a1520 0%, #0d0a14 100%);
  border: 1px solid rgba(255, 180, 60, 0.3);
  border-radius: 12px;
  padding: 24px;
  margin: 16px;
  animation: slideIn 0.3s ease;
  position: relative;
}

@keyframes slideIn {
  from { transform: translateX(100px); opacity: 0; }
  to { transform: translateX(0); opacity: 1; }
}

/* 卷轴装饰 */
.scroll-top {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.scroll-rod {
  flex: 1;
  height: 3px;
  background: linear-gradient(90deg, transparent, #c9a44a, transparent);
  border-radius: 2px;
}

.scroll-title {
  font-size: 18px;
  color: #ffd700;
  font-family: 'Noto Serif SC', serif;
  white-space: nowrap;
}

.scroll-bottom {
  margin-top: 16px;
}

.scroll-bottom .scroll-rod {
  height: 3px;
  background: linear-gradient(90deg, transparent, #c9a44a, transparent);
  border-radius: 2px;
}

/* 进度条 */
.progress-bar {
  height: 20px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 10px;
  margin-bottom: 20px;
  position: relative;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #c9a44a, #ffd700);
  border-radius: 10px;
  transition: width 0.5s ease;
}

.progress-text {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: 11px;
  color: #fff;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.8);
}

/* 任务区域 */
.quest-section {
  margin-bottom: 20px;
}

.section-badge {
  display: inline-block;
  padding: 2px 10px;
  background: rgba(255, 180, 60, 0.2);
  border: 1px solid rgba(255, 180, 60, 0.4);
  border-radius: 10px;
  font-size: 11px;
  color: #ffd700;
  margin-bottom: 8px;
}

.side-badge {
  background: rgba(120, 160, 255, 0.15);
  border-color: rgba(120, 160, 255, 0.3);
  color: #8ab4ff;
}

.quest-title {
  font-size: 16px;
  color: #e0d8c8;
  font-family: 'Noto Serif SC', serif;
  margin: 0 0 6px;
}

.quest-desc {
  font-size: 13px;
  color: #8a8090;
  line-height: 1.6;
  margin: 0 0 12px;
}

/* 目标列表 */
.objectives {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 12px;
}

.objectives.compact {
  gap: 4px;
}

.objective {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  font-size: 13px;
  color: #b0a8c0;
  transition: color 0.3s;
}

.objective.done {
  color: #6a6070;
  text-decoration: line-through;
}

.obj-check {
  font-size: 14px;
  flex-shrink: 0;
}

.objective.done .obj-check {
  color: #4caf50;
}

.obj-text {
  line-height: 1.4;
}

/* 提示 */
.hints {
  background: rgba(255, 180, 60, 0.06);
  border: 1px solid rgba(255, 180, 60, 0.15);
  border-radius: 8px;
  padding: 10px;
}

.hint-label {
  font-size: 11px;
  color: #c9a44a;
  margin-bottom: 6px;
}

.hint-text {
  font-size: 12px;
  color: #8a8070;
  line-height: 1.5;
  padding-left: 8px;
  border-left: 2px solid rgba(255, 180, 60, 0.2);
  margin-bottom: 4px;
}

.side-quest {
  margin-bottom: 14px;
  padding-bottom: 14px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.side-quest:last-child {
  border-bottom: none;
  margin-bottom: 0;
  padding-bottom: 0;
}

/* 关闭按钮 */
.close-btn {
  position: absolute;
  top: 12px;
  right: 12px;
  width: 28px;
  height: 28px;
  border: none;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 50%;
  color: #8a8090;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
}

.close-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #e0d8c8;
}
</style>
