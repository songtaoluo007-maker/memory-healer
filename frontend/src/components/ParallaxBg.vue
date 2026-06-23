<script setup lang="ts">
/**
 * 电影级视差背景
 * 多层视差滚动 + 记忆碎片光效 + 环境氛围
 */
import { ref, computed, onMounted, onUnmounted } from 'vue'

const props = defineProps<{
  sceneId: string
  mouseX?: number
  mouseY?: number
}>()

const containerRef = ref<HTMLElement | null>(null)

// 视差偏移（基于鼠标）
const offsetX = ref(0)
const offsetY = ref(0)

// 鼠标追踪
function onMouseMove(e: MouseEvent) {
  if (!containerRef.value) return
  const rect = containerRef.value.getBoundingClientRect()
  const cx = rect.width / 2
  const cy = rect.height / 2
  offsetX.value = (e.clientX - rect.left - cx) / cx
  offsetY.value = (e.clientY - rect.top - cy) / cy
}

onMounted(() => {
  window.addEventListener('mousemove', onMouseMove)
})
onUnmounted(() => {
  window.removeEventListener('mousemove', onMouseMove)
})

// 各层视差系数
const layers = computed(() => [
  { depth: 0.02, blur: 0, opacity: 1 },    // 最远背景
  { depth: 0.05, blur: 1, opacity: 0.7 },   // 中景
  { depth: 0.1, blur: 2, opacity: 0.5 },    // 近景
])

// 场景氛围色
const ambientColors: Record<string, { primary: string; secondary: string; glow: string }> = {
  scene_1972: { primary: 'rgba(180, 140, 60, 0.08)', secondary: 'rgba(120, 80, 20, 0.05)', glow: 'rgba(255, 200, 80, 0.03)' },
  scene_1990: { primary: 'rgba(60, 100, 180, 0.08)', secondary: 'rgba(40, 70, 140, 0.05)', glow: 'rgba(80, 140, 255, 0.03)' },
  scene_2024: { primary: 'rgba(100, 60, 140, 0.08)', secondary: 'rgba(70, 40, 100, 0.05)', glow: 'rgba(160, 100, 220, 0.03)' },
  scene_2050: { primary: 'rgba(40, 100, 160, 0.08)', secondary: 'rgba(20, 70, 120, 0.05)', glow: 'rgba(60, 160, 255, 0.03)' },
  scene_2089: { primary: 'rgba(160, 100, 40, 0.08)', secondary: 'rgba(120, 70, 20, 0.05)', glow: 'rgba(255, 160, 60, 0.03)' },
}

const ambient = computed(() => ambientColors[props.sceneId] || ambientColors.scene_1972)
</script>

<template>
  <div ref="containerRef" class="parallax-bg" aria-hidden="true">
    <!-- 视差层 -->
    <div
      v-for="(layer, i) in layers"
      :key="i"
      class="parallax-layer"
      :style="{
        transform: `translate(${offsetX * layer.depth * 30}px, ${offsetY * layer.depth * 20}px)`,
        filter: layer.blur ? `blur(${layer.blur}px)` : 'none',
        opacity: layer.opacity,
      }"
    >
      <slot :name="`layer-${i}`" />
    </div>

    <!-- 环境光效 -->
    <div
      class="ambient-glow"
      :style="{
        background: `radial-gradient(ellipse at ${50 + offsetX * 20}% ${50 + offsetY * 15}%, ${ambient.glow} 0%, transparent 70%)`,
      }"
    />

    <!-- 记忆碎片光点（装饰性） -->
    <div class="memory-sparks">
      <div
        v-for="n in 6"
        :key="n"
        class="spark"
        :style="{
          left: `${15 + n * 14}%`,
          top: `${20 + (n % 3) * 25}%`,
          animationDelay: `${n * 0.8}s`,
          animationDuration: `${3 + n * 0.5}s`,
        }"
      />
    </div>

    <!-- 场景氛围叠加 -->
    <div
      class="scene-atmosphere"
      :style="{
        background: `linear-gradient(135deg, ${ambient.primary} 0%, transparent 50%, ${ambient.secondary} 100%)`,
      }"
    />
  </div>
</template>

<style scoped>
.parallax-bg {
  position: absolute;
  inset: 0;
  overflow: hidden;
  pointer-events: none;
}

.parallax-layer {
  position: absolute;
  inset: -5%;
  width: 110%;
  height: 110%;
  transition: transform 0.3s ease-out;
  will-change: transform;
}

.ambient-glow {
  position: absolute;
  inset: 0;
  transition: background 1s ease;
  pointer-events: none;
}

.memory-sparks {
  position: absolute;
  inset: 0;
}

.spark {
  position: absolute;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(255, 220, 150, 0.9), rgba(255, 180, 80, 0.4));
  box-shadow: 0 0 12px rgba(255, 200, 100, 0.5), 0 0 24px rgba(255, 180, 80, 0.2);
  animation: sparkFloat ease-in-out infinite;
  opacity: 0;
}

@keyframes sparkFloat {
  0%, 100% {
    opacity: 0;
    transform: translateY(0) scale(0.5);
  }
  30% {
    opacity: 0.7;
    transform: translateY(-15px) scale(1);
  }
  70% {
    opacity: 0.5;
    transform: translateY(-30px) scale(0.8);
  }
}

.scene-atmosphere {
  position: absolute;
  inset: 0;
  mix-blend-mode: overlay;
  transition: background 1.5s ease;
}
</style>
