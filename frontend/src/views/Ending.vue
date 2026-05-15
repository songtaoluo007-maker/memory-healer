<script setup lang="ts">
import { ref, computed } from 'vue'
import { useGameState } from '../composables/useGameState'

const props = defineProps<{
  endingType: 'hope' | 'bittersweet' | 'tragic'
}>()

const emit = defineEmits<{
  restart: []
}>()

const { collectedCount, totalFragments } = useGameState()

const phase = ref(0)
setTimeout(() => { phase.value = 1 }, 500)
setTimeout(() => { phase.value = 2 }, 3000)
setTimeout(() => { phase.value = 3 }, 7000)

const endingData = computed(() => {
  const endings = {
    hope: {
      title: '结局一：光',
      icon: '🌅',
      description: `所有记忆碎片收集完毕。陈爷爷在梦中重新走过了1972年的西安老巷，2024年的深圳城中村，最终在2089年的实验室里睁开了眼睛。

他看着小雨，眼眶湿润："小雨……爷爷想起来了。那个孙悟空的皮影人偶……爷爷还没送给你。"

小雨紧紧握住爷爷的手，泪水滑落。

记忆修复成功了。那些被遗忘的光影、刻刀、锣鼓声——它们回来了。

不是作为冰冷的数据，而是作为温暖的记忆。`,
      mood: '温暖、感动、希望',
    },
    bittersweet: {
      title: '结局二：余温',
      icon: '🌙',
      description: `部分记忆碎片被找回。陈爷爷在梦中看到了一些模糊的画面——1972年的皮影戏台，那把刻着「陈」字的刻刀。

他醒来后，沉默了很久。

"我好像……想起了什么。但又不太清楚。"

小雨把那个孙悟空的皮影人偶放在爷爷手心。爷爷的手指摩挲着人偶，嘴角微微上扬。

虽然记忆不完整，但那份温暖还在。`,
      mood: '苦涩、温暖、遗憾',
    },
    tragic: {
      title: '结局三：消散',
      icon: '🕯️',
      description: `记忆碎片太少，修复失败了。

陈爷爷在梦中看到了一些碎片——光影、锣鼓、一把刻刀。但它们太模糊了，像水中的倒影，一碰就散。

他醒来后，看着小雨，眼神空洞。

"你是……谁？"

小雨没有哭。她拿出那个孙悟空的皮影人偶，放在爷爷面前。

"爷爷，我是小雨。我来看你了。"

爷爷接过人偶，手指下意识地摩挲着。他不记得了。但他的手记得。`,
      mood: '悲伤、遗憾、深沉',
    },
  }
  return endings[props.endingType]
})

const fragmentsPercent = computed(() => {
  if (!totalFragments.value) return 0
  return Math.round((collectedCount.value / totalFragments.value) * 100)
})
</script>

<template>
  <div class="ending" :class="'ending-' + endingType">
    <!-- 背景粒子 -->
    <div class="particles">
      <div v-for="i in 30" :key="i" class="particle" :style="{
        left: Math.random() * 100 + '%',
        animationDelay: Math.random() * 5 + 's',
        animationDuration: (4 + Math.random() * 6) + 's',
      }" />
    </div>

    <!-- Phase 0: 黑屏淡入 -->
    <div v-if="phase >= 0" class="ending-content" :class="{ visible: phase >= 1 }">
      <!-- 结局标题 -->
      <div class="ending-header" :class="{ visible: phase >= 1 }">
        <span class="ending-icon">{{ endingData.icon }}</span>
        <h1 class="ending-title">{{ endingData.title }}</h1>
        <div class="ending-mood">{{ endingData.mood }}</div>
      </div>

      <!-- 结局故事 -->
      <div class="ending-story" :class="{ visible: phase >= 2 }">
        <p v-for="(line, i) in endingData.description.split('\n\n')" :key="i" class="story-paragraph">
          {{ line }}
        </p>
      </div>

      <!-- 统计 -->
      <div class="ending-stats" :class="{ visible: phase >= 3 }">
        <div class="stat">
          <span class="stat-value">{{ collectedCount }}/{{ totalFragments }}</span>
          <span class="stat-label">记忆碎片</span>
        </div>
        <div class="stat">
          <span class="stat-value">{{ fragmentsPercent }}%</span>
          <span class="stat-label">记忆完整度</span>
        </div>
      </div>

      <!-- 重新开始 -->
      <div class="ending-actions" :class="{ visible: phase >= 3 }">
        <button class="btn-restart" @click="emit('restart')">
          重新开始修复
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.ending {
  position: fixed;
  inset: 0;
  background: #000;
  z-index: 300;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: 'Noto Serif SC', serif;
  overflow-y: auto;
}

.ending-hope {
  background: linear-gradient(180deg, #0a0a1a 0%, #1a1a3e 50%, #0a0a1a 100%);
}

.ending-bittersweet {
  background: linear-gradient(180deg, #0a0a1a 0%, #1a1a2e 50%, #0a0a1a 100%);
}

.ending-tragic {
  background: linear-gradient(180deg, #000 0%, #0a0a1a 50%, #000 100%);
}

.particles {
  position: fixed;
  inset: 0;
  pointer-events: none;
}

.particle {
  position: absolute;
  width: 3px;
  height: 3px;
  background: rgba(100, 180, 255, 0.4);
  border-radius: 50%;
  bottom: -10px;
  animation: float linear infinite;
}

@keyframes float {
  0% { transform: translateY(0) scale(1); opacity: 0; }
  10% { opacity: 0.6; }
  90% { opacity: 0.6; }
  100% { transform: translateY(-100vh) scale(0); opacity: 0; }
}

.ending-content {
  max-width: 600px;
  padding: 40px;
  text-align: center;
  opacity: 0;
  transition: opacity 1.5s ease;
}

.ending-content.visible {
  opacity: 1;
}

.ending-header {
  margin-bottom: 40px;
  opacity: 0;
  transform: translateY(20px);
  transition: all 1.5s ease;
}

.ending-header.visible {
  opacity: 1;
  transform: translateY(0);
}

.ending-icon {
  font-size: 64px;
  display: block;
  margin-bottom: 16px;
}

.ending-title {
  font-size: 36px;
  color: #e0e0ff;
  letter-spacing: 6px;
  margin: 0 0 12px;
  text-shadow: 0 0 30px rgba(100, 150, 255, 0.4);
}

.ending-mood {
  font-size: 13px;
  color: rgba(150, 170, 220, 0.5);
  letter-spacing: 2px;
}

.ending-story {
  margin-bottom: 48px;
  opacity: 0;
  transform: translateY(20px);
  transition: all 1.5s ease 0.5s;
}

.ending-story.visible {
  opacity: 1;
  transform: translateY(0);
}

.story-paragraph {
  font-size: 16px;
  color: rgba(200, 210, 255, 0.8);
  line-height: 2;
  margin-bottom: 20px;
  text-align: left;
  text-indent: 2em;
}

.ending-stats {
  display: flex;
  justify-content: center;
  gap: 48px;
  margin-bottom: 40px;
  opacity: 0;
  transition: opacity 1.5s ease;
}

.ending-stats.visible {
  opacity: 1;
}

.stat {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat-value {
  font-size: 28px;
  color: #60a5fa;
  font-weight: 600;
}

.stat-label {
  font-size: 12px;
  color: rgba(150, 170, 220, 0.5);
}

.ending-actions {
  opacity: 0;
  transition: opacity 1.5s ease;
}

.ending-actions.visible {
  opacity: 1;
}

.btn-restart {
  padding: 14px 40px;
  border-radius: 8px;
  border: 1px solid rgba(100, 150, 255, 0.3);
  background: rgba(58, 95, 205, 0.2);
  color: #e0e0ff;
  font-size: 16px;
  cursor: pointer;
  font-family: 'Noto Serif SC', serif;
  letter-spacing: 2px;
  transition: all 0.3s;
}

.btn-restart:hover {
  background: rgba(58, 95, 205, 0.4);
  border-color: rgba(100, 150, 255, 0.5);
  transform: translateY(-2px);
}
</style>
