<script setup lang="ts">
/**
 * 皮影幕布转场动画
 * 模拟传统皮影戏的幕布拉上→拉开效果
 * 1972年用暖色幕布，2024年用冷色，2089年用科技蓝
 */
import { ref, computed, watch } from 'vue'

const props = defineProps<{
  active: boolean
  sceneId: string
}>()

const phase = ref<'idle' | 'closing' | 'hold' | 'opening'>('idle')

// 根据场景年代选择幕布风格
const curtainStyle = computed(() => {
  if (props.sceneId.includes('1972')) {
    return {
      color1: '#8B4513',
      color2: '#D2691E',
      pattern: '传统纹样',
      bg: 'linear-gradient(180deg, #8B4513 0%, #D2691E 50%, #8B4513 100%)',
    }
  }
  if (props.sceneId.includes('1990')) {
    return {
      color1: '#8B7355',
      color2: '#D2B48C',
      pattern: '站台光影',
      bg: 'linear-gradient(180deg, #8B7355 0%, #D2B48C 50%, #8B7355 100%)',
    }
  }
  if (props.sceneId.includes('2024')) {
    return {
      color1: '#1a1a3e',
      color2: '#2a2a5e',
      pattern: '城市霓虹',
      bg: 'linear-gradient(180deg, #1a1a3e 0%, #2a2a5e 50%, #1a1a3e 100%)',
    }
  }
  if (props.sceneId.includes('2050')) {
    return {
      color1: '#2F2F2F',
      color2: '#4a4a2a',
      pattern: '金色灯光',
      bg: 'linear-gradient(180deg, #2F2F2F 0%, #4a4a2a 50%, #2F2F2F 100%)',
    }
  }
  return {
    color1: '#0a0a2a',
    color2: '#1a1a4e',
    pattern: '科技光栅',
    bg: 'linear-gradient(180deg, #0a0a2a 0%, #1a1a4e 50%, #0a0a2a 100%)',
  }
})

watch(() => props.active, (newVal) => {
  if (newVal) {
    phase.value = 'closing'
    setTimeout(() => {
      phase.value = 'hold'
      setTimeout(() => {
        phase.value = 'opening'
        setTimeout(() => {
          phase.value = 'idle'
        }, 600)
      }, 300)
    }, 500)
  }
})
</script>

<template>
  <div
    class="curtain-transition"
    :class="[phase, `era-${sceneId.includes('1972') ? '1972' : sceneId.includes('1990') ? '1990' : sceneId.includes('2024') ? '2024' : sceneId.includes('2050') ? '2050' : '2089'}`]"
  >
    <!-- 左幕布 -->
    <div class="curtain curtain-left" :style="{ background: curtainStyle.bg }">
      <div class="curtain-texture"></div>
      <div class="curtain-edge"></div>
    </div>

    <!-- 右幕布 -->
    <div class="curtain curtain-right" :style="{ background: curtainStyle.bg }">
      <div class="curtain-texture"></div>
      <div class="curtain-edge"></div>
    </div>

    <!-- 中间装饰 -->
    <div class="curtain-center" v-if="phase === 'hold'">
      <div class="center-ornament">
        <span class="ornament-text">记忆流转</span>
        <div class="ornament-line"></div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.curtain-transition {
  position: fixed;
  inset: 0;
  z-index: 90;
  pointer-events: none;
  display: flex;
}

.curtain {
  width: 50%;
  height: 100%;
  position: relative;
  transition: transform 0.5s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
}

.curtain-left {
  transform: translateX(-100%);
}

.curtain-right {
  transform: translateX(100%);
}

.curtain-texture {
  position: absolute;
  inset: 0;
  opacity: 0.15;
  background-image:
    repeating-linear-gradient(0deg, transparent, transparent 8px, rgba(255,255,255,0.05) 8px, rgba(255,255,255,0.05) 9px),
    repeating-linear-gradient(90deg, transparent, transparent 20px, rgba(255,255,255,0.03) 20px, rgba(255,255,255,0.03) 21px);
}

.curtain-edge {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 4px;
}

.curtain-left .curtain-edge {
  right: 0;
  background: linear-gradient(180deg, rgba(255,215,0,0.6), rgba(255,215,0,0.2));
}

.curtain-right .curtain-edge {
  left: 0;
  background: linear-gradient(180deg, rgba(255,215,0,0.2), rgba(255,215,0,0.6));
}

.curtain-center {
  position: absolute;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
  z-index: 2;
  animation: fadeIn 0.3s ease;
}

.center-ornament {
  text-align: center;
}

.ornament-text {
  font-family: 'Noto Serif SC', serif;
  font-size: 24px;
  color: rgba(255, 215, 0, 0.8);
  letter-spacing: 8px;
  text-shadow: 0 0 20px rgba(255, 215, 0, 0.4);
}

.ornament-line {
  width: 80px;
  height: 2px;
  background: linear-gradient(90deg, transparent, rgba(255, 215, 0, 0.6), transparent);
  margin: 12px auto 0;
}

/* 关闭阶段 */
.closing .curtain-left {
  transform: translateX(0);
}

.closing .curtain-right {
  transform: translateX(0);
}

/* 保持阶段 */
.hold .curtain-left,
.hold .curtain-right {
  transform: translateX(0);
}

/* 打开阶段 */
.opening .curtain-left {
  transform: translateX(-100%);
}

.opening .curtain-right {
  transform: translateX(100%);
}

/* 不同年代的纹理差异 */
.era-1972 .curtain-texture {
  opacity: 0.2;
  background-image:
    repeating-linear-gradient(45deg, transparent, transparent 10px, rgba(255,215,0,0.05) 10px, rgba(255,215,0,0.05) 11px);
}

.era-1990 .curtain-texture {
  opacity: 0.15;
  background-image:
    repeating-linear-gradient(90deg, transparent, transparent 15px, rgba(210,180,140,0.05) 15px, rgba(210,180,140,0.05) 16px);
}

.era-2024 .curtain-texture {
  opacity: 0.1;
  background-image:
    repeating-linear-gradient(90deg, transparent, transparent 40px, rgba(100,150,255,0.05) 40px, rgba(100,150,255,0.05) 41px);
}

.era-2050 .curtain-texture {
  opacity: 0.18;
  background-image:
    repeating-linear-gradient(0deg, transparent, transparent 5px, rgba(255,215,0,0.04) 5px, rgba(255,215,0,0.04) 6px);
}

.era-2089 .curtain-texture {
  opacity: 0.15;
  background-image:
    repeating-linear-gradient(0deg, transparent, transparent 3px, rgba(100,200,255,0.05) 3px, rgba(100,200,255,0.05) 4px);
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}
</style>
