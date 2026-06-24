<script setup lang="ts">
import { ref, onMounted } from 'vue'

const emit = defineEmits<{
  complete: []
}>()

const currentStep = ref(0)
const visible = ref(false)

const steps = [
  {
    icon: '?',
    title: '欢迎，记忆修复师',
    desc: '你将进入陈守义老人的记忆碎片，通过对话和探索，帮助他找回遗失的往事。',
  },
  {
    icon: '?',
    title: '探索场景',
    desc: '点击场景中的热区（发光区域）可以发现隐藏的记忆碎片。每个场景都藏有不同的故事。',
  },
  {
    icon: '?',
    title: '与NPC对话',
    desc: '点击底部的角色头像可以与他们交谈。你的选择会影响他们对你的信任度，解锁不同的记忆碎片。',
  },
  {
    icon: '?',
    title: '收集碎片',
    desc: '记忆碎片是重建过去的关键。收集足够碎片后，可以进入下一个时代，继续修复旅程。',
  },
  {
    icon: '?',
    title: '准备好了吗？',
    desc: '记住——每个选择都会影响故事的走向。现在，开始你的第一次记忆修复。',
  },
]

onMounted(() => {
  // 检查是否已完成教程
  if (localStorage.getItem('mh_tutorial_done')) {
    emit('complete')
    return
  }
  setTimeout(() => { visible.value = true }, 300)
})

const next = () => {
  if (currentStep.value < steps.length - 1) {
    currentStep.value++
  } else {
    localStorage.setItem('mh_tutorial_done', '1')
    visible.value = false
    setTimeout(() => emit('complete'), 400)
  }
}

const skip = () => {
  localStorage.setItem('mh_tutorial_done', '1')
  visible.value = false
  setTimeout(() => emit('complete'), 400)
}
</script>

<template>
  <Transition name="tutorial">
    <div v-if="visible" class="tutorial-overlay" @click.self="next">
      <div class="tutorial-card">
        <div class="step-indicator">
          <span
            v-for="(_, i) in steps"
            :key="i"
            class="dot"
            :class="{ active: i === currentStep, done: i < currentStep }"
          />
        </div>

        <div class="step-content">
          <div class="step-icon">{{ steps[currentStep].icon }}</div>
          <h2 class="step-title">{{ steps[currentStep].title }}</h2>
          <p class="step-desc">{{ steps[currentStep].desc }}</p>
        </div>

        <div class="step-actions">
          <button class="btn-skip" @click="skip">跳过教程</button>
          <button class="btn-next" @click="next">
            {{ currentStep < steps.length - 1 ? '继续' : '开始旅程' }}
          </button>
        </div>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.tutorial-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(12px);
  z-index: 500;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: 'Noto Serif SC', serif;
}

.tutorial-card {
  background: linear-gradient(135deg, rgba(15, 15, 35, 0.95), rgba(25, 20, 45, 0.95));
  border: 1px solid rgba(100, 150, 255, 0.2);
  border-radius: 20px;
  padding: 48px 40px 36px;
  max-width: 420px;
  width: 90vw;
  text-align: center;
  box-shadow:
    0 0 80px rgba(58, 95, 205, 0.15),
    0 20px 60px rgba(0, 0, 0, 0.5);
}

.step-indicator {
  display: flex;
  justify-content: center;
  gap: 8px;
  margin-bottom: 32px;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: rgba(100, 150, 255, 0.2);
  transition: all 0.3s;
}

.dot.active {
  background: #60a5fa;
  box-shadow: 0 0 12px rgba(96, 165, 250, 0.5);
  width: 24px;
  border-radius: 4px;
}

.dot.done {
  background: rgba(96, 165, 250, 0.5);
}

.step-content {
  margin-bottom: 36px;
}

.step-icon {
  font-size: 52px;
  margin-bottom: 16px;
  animation: float 3s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-8px); }
}

.step-title {
  font-size: 22px;
  color: #e0e0ff;
  margin: 0 0 12px;
  letter-spacing: 2px;
}

.step-desc {
  font-size: 15px;
  color: rgba(200, 210, 255, 0.7);
  line-height: 1.8;
  margin: 0;
}

.step-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.btn-skip {
  background: none;
  border: none;
  color: rgba(150, 170, 220, 0.4);
  font-size: 13px;
  cursor: pointer;
  font-family: 'Noto Serif SC', serif;
  padding: 8px 16px;
  transition: color 0.2s;
}

.btn-skip:hover {
  color: rgba(200, 210, 255, 0.7);
}

.btn-next {
  background: linear-gradient(135deg, #3a5fcd, #5078e0);
  border: none;
  color: white;
  padding: 12px 32px;
  border-radius: 8px;
  font-size: 15px;
  cursor: pointer;
  font-family: 'Noto Serif SC', serif;
  transition: all 0.2s;
  letter-spacing: 1px;
}

.btn-next:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 24px rgba(58, 95, 205, 0.5);
}

/* 过渡动画 */
.tutorial-enter-active { transition: opacity 0.4s; }
.tutorial-leave-active { transition: opacity 0.4s; }
.tutorial-enter-from, .tutorial-leave-to { opacity: 0; }
</style>
