<script setup lang="ts">
/**
 * 记忆档案面板 — 包含碎片关联图和详细信息
 * 可在游戏中随时打开查看
 */
import { ref, computed } from 'vue'
import FragmentGraph from './FragmentGraph.vue'
import type { FragmentState } from '../types/game'

const props = defineProps<{
  fragmentStates: Record<string, FragmentState>
  currentScene: string
  collectedCount: number
  totalFragments: number
}>()

const emit = defineEmits<{
  close: []
}>()

const activeTab = ref<'graph' | 'list'>('graph')

// 碎片列表（按年代分组）
const fragmentsByScene = computed(() => {
  const groups: Record<string, Array<{ id: string } & FragmentState>> = {
    scene_1972: [],
    scene_2024: [],
    scene_2089: [],
  }

  for (const [id, state] of Object.entries(props.fragmentStates)) {
    const scene = state.scene || 'scene_1972'
    if (groups[scene]) {
      groups[scene].push({ ...state, id: id })
    }
  }

  return groups
})

const sceneLabels: Record<string, string> = {
  scene_1972: '1972 西安老巷',
  scene_2024: '2024 深圳城中村',
  scene_2089: '2089 记忆实验室',
}
</script>

<template>
  <div class="memory-panel">
    <div class="panel-header">
      <h2 class="panel-title">📜 记忆档案</h2>
      <button class="btn-close" @click="emit('close')">✕</button>
    </div>

    <!-- 标签切换 -->
    <div class="tab-bar">
      <button
        class="tab-btn"
        :class="{ active: activeTab === 'graph' }"
        @click="activeTab = 'graph'"
      >
        关联图
      </button>
      <button
        class="tab-btn"
        :class="{ active: activeTab === 'list' }"
        @click="activeTab = 'list'"
      >
        碎片列表
      </button>
    </div>

    <!-- 关联图 -->
    <div v-if="activeTab === 'graph'" class="tab-content">
      <FragmentGraph
        :fragment-states="fragmentStates"
        :current-scene="currentScene"
      />
    </div>

    <!-- 碎片列表 -->
    <div v-if="activeTab === 'list'" class="tab-content">
      <div v-for="(scene, sceneId) in fragmentsByScene" :key="sceneId" class="scene-group">
        <h3 class="scene-title">{{ sceneLabels[sceneId as string] }}</h3>
        <div class="fragment-list">
          <div
            v-for="frag in scene"
            :key="frag.id"
            class="fragment-item"
            :class="{ collected: frag.collected, revealed: frag.revealed && !frag.collected }"
          >
            <span class="frag-icon">
              {{ frag.collected ? '✦' : frag.revealed ? '◯' : '?' }}
            </span>
            <div class="frag-info">
              <span class="frag-name">{{ frag.name || frag.id }}</span>
              <span class="frag-hint" v-if="frag.revealed && !frag.collected">
                继续探索...
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 底部统计 -->
    <div class="panel-footer">
      <div class="progress-bar">
        <div
          class="progress-fill"
          :style="{ width: `${totalFragments > 0 ? (collectedCount / totalFragments) * 100 : 0}%` }"
        ></div>
      </div>
      <span class="footer-text">
        记忆完整度 {{ collectedCount }}/{{ totalFragments }}
      </span>
    </div>
  </div>
</template>

<style scoped>
.memory-panel {
  position: fixed;
  inset: 0;
  z-index: 200;
  background: rgba(5, 5, 20, 0.95);
  display: flex;
  flex-direction: column;
  font-family: 'Noto Serif SC', serif;
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid rgba(100, 150, 255, 0.15);
}

.panel-title {
  font-size: 20px;
  color: #e0e0ff;
  margin: 0;
  letter-spacing: 2px;
}

.btn-close {
  background: none;
  border: none;
  color: rgba(150, 170, 220, 0.6);
  font-size: 20px;
  cursor: pointer;
  padding: 8px;
  transition: color 0.2s;
}

.btn-close:hover {
  color: #e0e0ff;
}

.tab-bar {
  display: flex;
  gap: 4px;
  padding: 12px 24px;
  border-bottom: 1px solid rgba(100, 150, 255, 0.1);
}

.tab-btn {
  padding: 8px 16px;
  border-radius: 6px;
  border: 1px solid rgba(100, 150, 255, 0.2);
  background: transparent;
  color: rgba(150, 170, 220, 0.6);
  font-size: 13px;
  cursor: pointer;
  font-family: 'Noto Serif SC', serif;
  transition: all 0.2s;
}

.tab-btn.active {
  background: rgba(58, 95, 205, 0.3);
  border-color: rgba(100, 150, 255, 0.4);
  color: #e0e0ff;
}

.tab-content {
  flex: 1;
  overflow-y: auto;
  padding: 20px 24px;
}

.scene-group {
  margin-bottom: 24px;
}

.scene-title {
  font-size: 14px;
  color: rgba(200, 210, 255, 0.6);
  margin: 0 0 12px;
  letter-spacing: 1px;
}

.fragment-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.fragment-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: 8px;
  background: rgba(30, 30, 60, 0.5);
  border: 1px solid rgba(100, 150, 255, 0.1);
  transition: all 0.2s;
}

.fragment-item.collected {
  border-color: rgba(74, 222, 128, 0.3);
  background: rgba(74, 222, 128, 0.05);
}

.fragment-item.revealed {
  border-color: rgba(245, 158, 11, 0.3);
  background: rgba(245, 158, 11, 0.05);
}

.frag-icon {
  font-size: 18px;
  width: 30px;
  text-align: center;
}

.fragment-item.collected .frag-icon {
  color: #4ade80;
}

.fragment-item.revealed .frag-icon {
  color: #f59e0b;
}

.frag-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.frag-name {
  font-size: 14px;
  color: #e0e0ff;
}

.frag-hint {
  font-size: 11px;
  color: rgba(150, 170, 220, 0.5);
}

.panel-footer {
  padding: 16px 24px;
  border-top: 1px solid rgba(100, 150, 255, 0.15);
}

.progress-bar {
  height: 4px;
  background: rgba(50, 50, 80, 0.5);
  border-radius: 2px;
  overflow: hidden;
  margin-bottom: 8px;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #4ade80, #60a5fa);
  transition: width 0.5s ease;
}

.footer-text {
  font-size: 12px;
  color: rgba(150, 170, 220, 0.5);
}
</style>
