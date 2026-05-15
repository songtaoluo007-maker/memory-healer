<script setup lang="ts">
import { ref, onMounted } from 'vue'

const emit = defineEmits<{
  complete: []
}>()

const phase = ref(0) // 0=黑屏, 1=文字淡入, 2=故事背景, 3=淡出
const skipVisible = ref(false)

onMounted(() => {
  setTimeout(() => { phase.value = 1; skipVisible.value = true }, 800)
  setTimeout(() => { phase.value = 2 }, 3000)
  setTimeout(() => { phase.value = 3 }, 8000)
  setTimeout(() => { emit('complete') }, 9500)
})

const skip = () => {
  emit('complete')
}
</script>

<template>
  <div class="intro" :class="'phase-' + phase">
    <!-- Phase 0: 黑屏 -->
    <div v-if="phase === 0" class="black-screen" />

    <!-- Phase 1: 标题 -->
    <div v-if="phase >= 1 && phase < 3" class="title-screen">
      <div class="title-icon">🧠</div>
      <h1 class="title">拾 忆</h1>
      <p class="subtitle">Memory Healer</p>
    </div>

    <!-- Phase 2: 故事背景 -->
    <div v-if="phase >= 2 && phase < 3" class="story-text">
      <p class="story-line" style="animation-delay: 0s">
        2089年，深圳。
      </p>
      <p class="story-line" style="animation-delay: 0.8s">
        阿尔茨海默症已经不再是绝症。
      </p>
      <p class="story-line" style="animation-delay: 1.6s">
        拾忆科技发明了一种技术——
      </p>
      <p class="story-line" style="animation-delay: 2.4s">
        通过AI重建患者的记忆碎片，
      </p>
      <p class="story-line" style="animation-delay: 3.2s">
        让他们在梦中重走一生。
      </p>
      <p class="story-line highlight" style="animation-delay: 4.2s">
        你是第一位记忆修复师。
      </p>
    </div>

    <!-- 跳过按钮 -->
    <button v-if="skipVisible && phase < 3" class="skip-btn" @click="skip">
      跳过 ▸
    </button>
  </div>
</template>

<style scoped>
.intro {
  position: fixed;
  inset: 0;
  background: #000;
  z-index: 300;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  font-family: 'Noto Serif SC', serif;
  overflow: hidden;
}

.phase-0 {
  background: #000;
}

.phase-1, .phase-2 {
  background: linear-gradient(180deg, #000 0%, #0a0a1a 100%);
}

.phase-3 {
  background: #000;
  opacity: 0;
  transition: opacity 1.5s ease-out;
}

.black-screen {
  width: 100%;
  height: 100%;
}

.title-screen {
  position: absolute;
  top: 30%;
  text-align: center;
  animation: fadeInUp 2s ease-out;
}

.title-icon {
  font-size: 56px;
  margin-bottom: 16px;
  animation: pulse 3s ease-in-out infinite;
}

.title {
  font-size: 64px;
  color: #e0e0ff;
  letter-spacing: 20px;
  margin: 0;
  text-shadow: 0 0 40px rgba(100, 150, 255, 0.5);
}

.subtitle {
  font-size: 14px;
  color: rgba(150, 180, 255, 0.5);
  letter-spacing: 10px;
  text-transform: uppercase;
  margin: 12px 0 0;
}

.story-text {
  position: absolute;
  top: 35%;
  text-align: center;
  padding: 0 40px;
}

.story-line {
  font-size: 18px;
  color: rgba(200, 210, 255, 0.8);
  line-height: 2.2;
  opacity: 0;
  animation: fadeInUp 1s ease-out forwards;
}

.story-line.highlight {
  color: #60a5fa;
  font-size: 20px;
  font-weight: 600;
  margin-top: 12px;
}

.skip-btn {
  position: fixed;
  bottom: 40px;
  right: 40px;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(100, 150, 255, 0.2);
  color: rgba(200, 210, 255, 0.6);
  padding: 8px 20px;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  font-family: 'Noto Serif SC', serif;
  transition: all 0.2s;
}

.skip-btn:hover {
  background: rgba(255, 255, 255, 0.15);
  color: #e0e0ff;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.1); }
}
</style>
