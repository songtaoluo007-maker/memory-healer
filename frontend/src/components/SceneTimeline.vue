<script setup lang="ts">
import { computed } from 'vue'

interface SceneInfo {
  id: string
  name: string
  year: number
  location: string
  description: string
  icon: string
}

const props = defineProps<{
  currentScene: string
  visitedScenes?: string[]
  collectedCounts?: Record<string, number>
  totalCounts?: Record<string, number>
}>()

const emit = defineEmits<{
  navigate: [sceneId: string]
  close: []
}>()

const scenes: SceneInfo[] = [
  { id: 'scene_1972', name: '学艺', year: 1972, location: '西安老巷', description: '25岁的陈守义，皮影戏传人。爷爷的遗言、刻刀上的"陈"字。', icon: '🎭' },
  { id: 'scene_1990', name: '南下', year: 1990, location: '深圳火车站', description: '43岁的陈守义带着一箱皮影去深圳闯荡。陌生人的搭话。', icon: '🚂' },
  { id: 'scene_2024', name: '遗忘', year: 2024, location: '深圳城中村', description: '77岁的陈守义坐在轮椅上，记忆开始消散。', icon: '🏚' },
  { id: 'scene_2050', name: '传承', year: 2050, location: '北京颁奖典礼', description: '小雨创办拾忆公司，获得非遗传承贡献奖。', icon: '🏆' },
  { id: 'scene_2089', name: '修复', year: 2089, location: '拾忆实验室', description: '所有记忆碎片在这里被修复。最终结局。', icon: '🔬' },
]

const visited = computed(() => new Set(props.visitedScenes || []))

function getProgress(sceneId: string): string {
  const collected = props.collectedCounts?.[sceneId] || 0
  const total = props.totalCounts?.[sceneId] || 0
  if (total === 0) return ''
  return `${collected}/${total}`
}
</script>

<template>
  <div class="timeline-overlay" @click.self="emit('close')">
    <div class="timeline-panel">
      <div class="timeline-header">
        <h2>🕰 时光地图</h2>
        <button class="close-btn" @click="emit('close')">✕</button>
      </div>

      <div class="timeline-track">
        <div class="timeline-line" />

        <div
          v-for="(scene, i) in scenes"
          :key="scene.id"
          class="timeline-node"
          :class="{
            current: currentScene === scene.id,
            visited: visited.has(scene.id),
            future: !visited.has(scene.id) && currentScene !== scene.id,
          }"
          @click="visited.has(scene.id) ? emit('navigate', scene.id) : null"
        >
          <div class="node-dot">
            <span class="node-icon">{{ scene.icon }}</span>
          </div>

          <div class="node-content">
            <div class="node-year">{{ scene.year }}</div>
            <div class="node-name">{{ scene.name }}</div>
            <div class="node-location">{{ scene.location }}</div>
            <div class="node-desc">{{ scene.description }}</div>
            <div class="node-progress" v-if="getProgress(scene.id)">
              碎片: {{ getProgress(scene.id) }}
            </div>
          </div>

          <div class="node-badge" v-if="currentScene === scene.id">当前</div>
          <div class="node-badge visited-badge" v-else-if="visited.has(scene.id)">已访</div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.timeline-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.75);
  z-index: 200;
  display: flex;
  align-items: center;
  justify-content: center;
}

.timeline-panel {
  background: rgba(10, 10, 30, 0.97);
  border: 1px solid rgba(100, 150, 255, 0.15);
  border-radius: 16px;
  width: 90%;
  max-width: 700px;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
  font-family: 'Noto Serif SC', serif;
}

.timeline-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.timeline-header h2 {
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

.timeline-track {
  flex: 1;
  overflow-y: auto;
  padding: 24px 20px;
  position: relative;
}

.timeline-line {
  position: absolute;
  left: 36px;
  top: 24px;
  bottom: 24px;
  width: 2px;
  background: linear-gradient(to bottom,
    rgba(100, 200, 150, 0.4),
    rgba(150, 170, 220, 0.2),
    rgba(255, 255, 255, 0.05));
}

.timeline-node {
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
  position: relative;
  cursor: default;
  transition: opacity 0.3s;
}

.timeline-node.visited,
.timeline-node.current {
  cursor: pointer;
}
.timeline-node.future {
  opacity: 0.35;
}

.node-dot {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.05);
  border: 2px solid rgba(255, 255, 255, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  z-index: 1;
  transition: all 0.3s;
}

.timeline-node.current .node-dot {
  background: rgba(100, 150, 255, 0.2);
  border-color: rgba(100, 150, 255, 0.6);
  box-shadow: 0 0 12px rgba(100, 150, 255, 0.3);
}

.timeline-node.visited .node-dot {
  background: rgba(100, 200, 150, 0.1);
  border-color: rgba(100, 200, 150, 0.3);
}

.node-icon {
  font-size: 16px;
}

.node-content {
  flex: 1;
  min-width: 0;
}

.node-year {
  font-size: 11px;
  color: rgba(150, 170, 220, 0.5);
  letter-spacing: 1px;
}

.node-name {
  font-size: 16px;
  color: #e0e0ff;
  font-weight: 500;
  margin: 2px 0;
}

.node-location {
  font-size: 12px;
  color: rgba(150, 170, 220, 0.6);
}

.node-desc {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.4);
  line-height: 1.5;
  margin-top: 4px;
}

.node-progress {
  font-size: 11px;
  color: rgba(255, 215, 100, 0.6);
  margin-top: 4px;
}

.node-badge {
  position: absolute;
  top: 0;
  right: 0;
  font-size: 10px;
  padding: 2px 8px;
  border-radius: 4px;
  background: rgba(100, 150, 255, 0.2);
  color: #a0b0ff;
}

.node-badge.visited-badge {
  background: rgba(100, 200, 150, 0.15);
  color: rgba(100, 200, 150, 0.7);
}

/* 移动端适配 */
@media (max-width: 768px) {
  .scene-timeline { padding: 16px; max-height: 80vh; }
  .scene-timeline h3 { font-size: 16px; }
  .timeline-node { padding: 10px; }
  .node-year { font-size: 18px; }
}
@media (max-width: 480px) {
  .scene-timeline { padding: 12px; }
  .timeline-node { padding: 8px; }
  .node-name { font-size: 13px; }
}
</style>

