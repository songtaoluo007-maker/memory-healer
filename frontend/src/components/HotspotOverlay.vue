<script setup lang="ts">
/**
 * 热区叠加层 — 在场景插画上显示可探索的交互点
 * 皮影戏风格：热区用脉冲光圈+小灯笼图标提示
 */
import { ref, computed } from 'vue'
import { useI18n } from '../composables/useI18n'
import type { Hotspot } from '../composables/useHotspots'

const { t } = useI18n()

const props = defineProps<{
  hotspots: Hotspot[]
  exploredIds: Set<string>
  sceneId: string
}>()

const emit = defineEmits<{
  explore: [hotspot: Hotspot]
}>()

const hoveredId = ref<string | null>(null)

// 根据场景年代决定光圈颜色
const eraColor = computed(() => {
  if (props.sceneId.includes('1972')) return { main: '#f59e0b', glow: 'rgba(245,158,11,0.3)' }
  if (props.sceneId.includes('2024')) return { main: '#60a5fa', glow: 'rgba(96,165,250,0.3)' }
  return { main: '#a78bfa', glow: 'rgba(167,139,250,0.3)' }
})

const handleClick = (hotspot: Hotspot) => {
  if (!props.exploredIds.has(hotspot.id)) {
    emit('explore', hotspot)
  }
}
</script>

<template>
  <svg
    class="hotspot-overlay"
    viewBox="0 0 800 500"
    preserveAspectRatio="xMidYMid meet"
    role="img"
    :aria-label="t('a11y.hotspot')"
  >
    <defs>
      <!-- 脉冲动画 -->
      <radialGradient :id="'pulse-' + sceneId" cx="50%" cy="50%" r="50%">
        <stop offset="0%" :stop-color="eraColor.main" stop-opacity="0.6">
          <animate attributeName="stop-opacity" values="0.6;0.2;0.6" dur="2s" repeatCount="indefinite" />
        </stop>
        <stop offset="100%" :stop-color="eraColor.main" stop-opacity="0" />
      </radialGradient>

      <!-- 发光滤镜 -->
      <filter :id="'glow-' + sceneId" x="-50%" y="-50%" width="200%" height="200%">
        <feGaussianBlur in="SourceGraphic" stdDeviation="3" result="blur" />
        <feMerge>
          <feMergeNode in="blur" />
          <feMergeNode in="SourceGraphic" />
        </feMerge>
      </filter>
    </defs>

    <!-- 每个热区 -->
    <g
      v-for="hotspot in hotspots"
      :key="hotspot.id"
      class="hotspot-group"
      :class="{
        explored: exploredIds.has(hotspot.id),
        hovered: hoveredId === hotspot.id
      }"
      @click="handleClick(hotspot)"
      @mouseenter="hoveredId = hotspot.id"
      @mouseleave="hoveredId = null"
    >
      <!-- 脉冲光圈（未探索才显示） -->
      <circle
        v-if="!exploredIds.has(hotspot.id)"
        :cx="hotspot.x"
        :cy="hotspot.y"
        :r="hotspot.radius * 1.8"
        :fill="`url(#pulse-${sceneId})`"
        class="pulse-ring"
      />

      <!-- 主热区圆圈 -->
      <circle
        :cx="hotspot.x"
        :cy="hotspot.y"
        :r="hotspot.radius"
        :fill="exploredIds.has(hotspot.id) ? 'rgba(100,100,100,0.2)' : eraColor.glow"
        :stroke="exploredIds.has(hotspot.id) ? 'rgba(100,100,100,0.3)' : eraColor.main"
        stroke-width="2"
        :filter="exploredIds.has(hotspot.id) ? 'none' : `url(#glow-${sceneId})`"
        class="hotspot-circle"
      />

      <!-- 热区图标 -->
      <text
        :x="hotspot.x"
        :y="hotspot.y + 5"
        text-anchor="middle"
        :font-size="hotspot.radius * 0.7"
        :fill="exploredIds.has(hotspot.id) ? 'rgba(150,150,150,0.5)' : '#fff'"
        class="hotspot-icon"
      >
        {{ exploredIds.has(hotspot.id) ? '✓' : '✦' }}
      </text>

      <!-- 悬浮提示 -->
      <g v-if="hoveredId === hotspot.id && !exploredIds.has(hotspot.id)">
        <rect
          :x="hotspot.x - 100"
          :y="hotspot.y - hotspot.radius - 35"
          width="200"
          height="28"
          rx="6"
          fill="rgba(0,0,0,0.8)"
          :stroke="eraColor.main"
          stroke-width="1"
        />
        <text
          :x="hotspot.x"
          :y="hotspot.y - hotspot.radius - 17"
          text-anchor="middle"
          font-size="12"
          fill="#e0e0ff"
          font-family="'Noto Serif SC', serif"
        >
          {{ hotspot.hint.length > 18 ? hotspot.hint.substring(0, 18) + '...' : hotspot.hint }}
        </text>
      </g>
    </g>
  </svg>
</template>

<style scoped>
.hotspot-overlay {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 10;
}

.hotspot-group {
  pointer-events: all;
  cursor: pointer;
  transition: transform 0.2s;
}

.hotspot-group:not(.explored):hover {
  transform: scale(1.1);
}

.hotspot-group.explored {
  cursor: default;
  opacity: 0.5;
}

.hotspot-circle {
  transition: all 0.3s;
}

.hotspot-group:not(.explored):hover .hotspot-circle {
  stroke-width: 3;
}

.pulse-ring {
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 0.6; transform-origin: center; }
  50% { opacity: 0.2; }
}

.hotspot-icon {
  pointer-events: none;
  user-select: none;
}
</style>
