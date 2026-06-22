<script setup lang="ts">
/**
 * 碎片关联图 — 可视化碎片之间的依赖关系和解锁路径
 * 皮影戏风格：用线条连接相关碎片，已收集的高亮，未收集的虚线
 */
import { computed } from 'vue'
import type { FragmentState } from '../types/game'

const props = defineProps<{
  fragmentStates: Record<string, FragmentState>
  currentScene: string
}>()

// 碎片关联关系定义
const fragmentLinks: Array<{ from: string; to: string; label: string }> = [
  // 1972年关联
  { from: 'puppet_stage', to: 'carving_knife', label: '探索发现' },
  { from: 'carving_knife', to: 'opera_three_kingdoms', label: '信任≥60' },
  { from: 'puppet_stage', to: 'alley_memory', label: '对话触发' },
  // 2024年关联
  { from: 'old_photos', to: 'repair_tools', label: '探索发现' },
  { from: 'repair_tools', to: 'puppet_box', label: '信任≥50' },
  { from: 'xiaoyu_letter', to: 'puppet_box', label: '蝴蝶效应' },
  // 2089年关联
  { from: 'memory_data', to: 'quantum_state', label: '数据收集' },
  { from: 'quantum_state', to: 'hologram', label: '信任≥70' },
  // 跨年代关联
  { from: 'opera_three_kingdoms', to: 'memory_data', label: '记忆传承' },
  { from: 'puppet_box', to: 'hologram', label: '时光回响' },
]

// 碎片位置布局（按年代分层）
const fragmentPositions: Record<string, { x: number; y: number; scene: string }> = {
  // 1972年 (左)
  puppet_stage: { x: 80, y: 80, scene: 'scene_1972' },
  carving_knife: { x: 80, y: 180, scene: 'scene_1972' },
  opera_three_kingdoms: { x: 80, y: 280, scene: 'scene_1972' },
  alley_memory: { x: 180, y: 130, scene: 'scene_1972' },
  // 2024年 (中)
  old_photos: { x: 320, y: 80, scene: 'scene_2024' },
  repair_tools: { x: 320, y: 180, scene: 'scene_2024' },
  puppet_box: { x: 320, y: 280, scene: 'scene_2024' },
  xiaoyu_letter: { x: 420, y: 130, scene: 'scene_2024' },
  // 2089年 (右)
  memory_data: { x: 560, y: 80, scene: 'scene_2089' },
  quantum_state: { x: 560, y: 180, scene: 'scene_2089' },
  hologram: { x: 560, y: 280, scene: 'scene_2089' },
}

// 年代标签
const sceneLabels: Record<string, { label: string; color: string }> = {
  scene_1972: { label: '1972 西安', color: '#f59e0b' },
  scene_2024: { label: '2024 深圳', color: '#60a5fa' },
  scene_2089: { label: '2089 实验室', color: '#a78bfa' },
}

// 计算链接状态
const linkStates = computed(() => {
  return fragmentLinks.map(link => {
    const fromState = props.fragmentStates[link.from]
    const toState = props.fragmentStates[link.to]
    const fromCollected = fromState?.collected || false
    const toCollected = toState?.collected || false
    const fromRevealed = fromState?.revealed || false

    return {
      ...link,
      fromPos: fragmentPositions[link.from],
      toPos: fragmentPositions[link.to],
      active: fromCollected && toCollected,
      partial: fromRevealed || (fromCollected && !toCollected),
      locked: !fromRevealed && !fromCollected,
    }
  })
})

// 碎片节点状态
const fragmentNodes = computed(() => {
  return Object.entries(fragmentPositions).map(([id, pos]) => {
    const state = props.fragmentStates[id]
    return {
      id,
      ...pos,
      collected: state?.collected || false,
      revealed: state?.revealed || false,
      name: state?.name || id,
      isCurrentScene: pos.scene === props.currentScene,
    }
  })
})

// 统计
const stats = computed(() => {
  const nodes = fragmentNodes.value
  return {
    total: nodes.length,
    collected: nodes.filter(n => n.collected).length,
    revealed: nodes.filter(n => n.revealed).length,
    percent: Math.round((nodes.filter(n => n.collected).length / nodes.length) * 100),
  }
})
</script>

<template>
  <div class="fragment-graph">
    <div class="graph-header">
      <h3 class="graph-title">记忆碎片关联图</h3>
      <div class="graph-stats">
        <span class="stat-collected">{{ stats.collected }}/{{ stats.total }} 已收集</span>
        <span class="stat-percent">{{ stats.percent }}%</span>
      </div>
    </div>

    <svg viewBox="0 0 680 360" class="graph-svg">
      <defs>
        <!-- 发光滤镜 -->
        <filter id="glow" x="-30%" y="-30%" width="160%" height="160%">
          <feGaussianBlur in="SourceGraphic" stdDeviation="4" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>

        <!-- 年代渐变 -->
        <linearGradient id="grad-1972" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stop-color="#f59e0b" stop-opacity="0.3" />
          <stop offset="100%" stop-color="#f59e0b" stop-opacity="0" />
        </linearGradient>
        <linearGradient id="grad-2024" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stop-color="#60a5fa" stop-opacity="0.3" />
          <stop offset="100%" stop-color="#60a5fa" stop-opacity="0" />
        </linearGradient>
        <linearGradient id="grad-2089" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stop-color="#a78bfa" stop-opacity="0.3" />
          <stop offset="100%" stop-color="#a78bfa" stop-opacity="0" />
        </linearGradient>
      </defs>

      <!-- 年代背景 -->
      <rect x="20" y="30" width="200" height="300" rx="8" fill="url(#grad-1972)" />
      <rect x="260" y="30" width="200" height="300" rx="8" fill="url(#grad-2024)" />
      <rect x="500" y="30" width="160" height="300" rx="8" fill="url(#grad-2089)" />

      <!-- 年代标签 -->
      <text x="120" y="55" text-anchor="middle" font-size="14" :fill="sceneLabels.scene_1972.color" font-weight="bold">1972 西安</text>
      <text x="360" y="55" text-anchor="middle" font-size="14" :fill="sceneLabels.scene_2024.color" font-weight="bold">2024 深圳</text>
      <text x="580" y="55" text-anchor="middle" font-size="14" :fill="sceneLabels.scene_2089.color" font-weight="bold">2089 实验室</text>

      <!-- 链接线 -->
      <g v-for="link in linkStates" :key="`${link.from}-${link.to}`">
        <line
          :x1="link.fromPos.x"
          :y1="link.fromPos.y"
          :x2="link.toPos.x"
          :y2="link.toPos.y"
          :stroke="link.active ? '#4ade80' : link.partial ? '#f59e0b' : 'rgba(100,100,100,0.3)'"
          :stroke-width="link.active ? 3 : 2"
          :stroke-dasharray="link.locked ? '5,5' : 'none'"
          :opacity="link.locked ? 0.4 : 0.8"
        />
        <!-- 链接标签 -->
        <text
          :x="(link.fromPos.x + link.toPos.x) / 2"
          :y="(link.fromPos.y + link.toPos.y) / 2 - 8"
          text-anchor="middle"
          font-size="10"
          :fill="link.active ? '#4ade80' : 'rgba(150,150,150,0.5)'"
        >
          {{ link.label }}
        </text>
      </g>

      <!-- 碎片节点 -->
      <g v-for="node in fragmentNodes" :key="node.id">
        <!-- 节点背景 -->
        <circle
          :cx="node.x"
          :cy="node.y"
          r="24"
          :fill="node.collected ? 'rgba(74,222,128,0.2)' : node.revealed ? 'rgba(245,158,11,0.2)' : 'rgba(50,50,50,0.3)'"
          :stroke="node.collected ? '#4ade80' : node.revealed ? '#f59e0b' : 'rgba(100,100,100,0.3)'"
          stroke-width="2"
          :filter="node.collected ? 'url(#glow)' : 'none'"
          :class="{ 'node-current': node.isCurrentScene }"
        />

        <!-- 节点图标 -->
        <text
          :x="node.x"
          :y="node.y + 5"
          text-anchor="middle"
          font-size="16"
          :fill="node.collected ? '#4ade80' : node.revealed ? '#f59e0b' : 'rgba(100,100,100,0.5)'"
        >
          {{ node.collected ? '✦' : node.revealed ? '◯' : '?' }}
        </text>

        <!-- 节点名称 -->
        <text
          :x="node.x"
          :y="node.y + 38"
          text-anchor="middle"
          font-size="10"
          :fill="node.collected ? '#e0e0ff' : 'rgba(150,150,150,0.5)'"
        >
          {{ node.name.length > 6 ? node.name.substring(0, 6) + '..' : node.name }}
        </text>
      </g>
    </svg>

    <!-- 图例 -->
    <div class="graph-legend">
      <div class="legend-item">
        <span class="legend-dot collected"></span>
        <span>已收集</span>
      </div>
      <div class="legend-item">
        <span class="legend-dot revealed"></span>
        <span>已发现</span>
      </div>
      <div class="legend-item">
        <span class="legend-dot locked"></span>
        <span>未解锁</span>
      </div>
      <div class="legend-item">
        <span class="legend-line active"></span>
        <span>已关联</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.fragment-graph {
  background: rgba(10, 10, 30, 0.9);
  border: 1px solid rgba(100, 150, 255, 0.15);
  border-radius: 12px;
  padding: 16px;
  max-width: 700px;
  margin: 0 auto;
}

.graph-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.graph-title {
  font-size: 16px;
  color: #e0e0ff;
  margin: 0;
  font-family: 'Noto Serif SC', serif;
}

.graph-stats {
  display: flex;
  gap: 12px;
  align-items: center;
}

.stat-collected {
  font-size: 12px;
  color: rgba(150, 170, 220, 0.6);
}

.stat-percent {
  font-size: 14px;
  color: #4ade80;
  font-weight: 600;
}

.graph-svg {
  width: 100%;
  height: auto;
}

.node-current {
  animation: pulse-node 2s ease-in-out infinite;
}

@keyframes pulse-node {
  0%, 100% { stroke-width: 2; }
  50% { stroke-width: 4; }
}

.graph-legend {
  display: flex;
  justify-content: center;
  gap: 20px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid rgba(100, 150, 255, 0.1);
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: rgba(150, 170, 220, 0.6);
}

.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.legend-dot.collected {
  background: #4ade80;
}

.legend-dot.revealed {
  background: #f59e0b;
}

.legend-dot.locked {
  background: rgba(100, 100, 100, 0.5);
}

.legend-line {
  width: 20px;
  height: 2px;
}

.legend-line.active {
  background: #4ade80;
}
</style>
