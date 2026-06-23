<script setup lang="ts">
/**
 * 游戏开场引导 — 第一次进入时显示
 * 皮影戏风格：卷轴展开，引入故事背景
 */
import { ref } from 'vue'

const emit = defineEmits<{
  start: []
}>()

const step = ref(0)

const steps = [
  {
    title: '序章',
    text: '2089年，一个普通的夜晚。\n你接到了一个特殊的委托——\n一位患有阿尔茨海默症的老人，\n正在逐渐忘记自己的一生。',
  },
  {
    title: '拾忆计划',
    text: '你加入了一个名为"拾忆"的实验项目。\n通过神经接口技术，\n你可以进入老人的记忆碎片，\n修复那些正在消散的光影。',
  },
  {
    title: '你的任务',
    text: '探索不同时代的记忆场景，\n与记忆中的人物对话，\n收集散落的记忆碎片，\n帮助老人找回他的一生。',
  },
  {
    title: '提示',
    text: '✦ 点击发光的物品可以探索\n✦ 点击人物头像可以对话\n✦ 你的选择会影响故事走向\n✦ 右上角可以查看当前任务',
  },
]

function nextStep() {
  if (step.value < steps.length - 1) {
    step.value++
  } else {
    emit('start')
  }
}
</script>

<template>
  <div class="intro-overlay" @click="nextStep">
    <div class="intro-scroll">
      <!-- 卷轴顶部 -->
      <div class="scroll-ornament top">
        <div class="rod"></div>
        <div class="ornament-center">卷</div>
        <div class="rod"></div>
      </div>

      <!-- 内容 -->
      <div class="intro-content" :key="step">
        <div class="intro-chapter">{{ steps[step].title }}</div>
        <div class="intro-text">
          <p v-for="(line, i) in steps[step].text.split('\n')" :key="i">{{ line }}</p>
        </div>
      </div>

      <!-- 卷轴底部 -->
      <div class="scroll-ornament bottom">
        <div class="rod"></div>
      </div>

      <!-- 进度指示 -->
      <div class="step-dots">
        <span
          v-for="(_, i) in steps"
          :key="i"
          class="dot"
          :class="{ active: i === step }"
        ></span>
      </div>

      <!-- 操作提示 -->
      <div class="click-hint">
        {{ step < steps.length - 1 ? '点击继续' : '点击开始' }}
      </div>
    </div>
  </div>
</template>

<style scoped>
.intro-overlay {
  position: fixed;
  inset: 0;
  z-index: 200;
  background: rgba(0, 0, 0, 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  animation: fadeIn 0.5s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.intro-scroll {
  max-width: 420px;
  width: 90%;
  animation: scrollUnfurl 0.8s ease;
}

@keyframes scrollUnfurl {
  from { transform: scaleY(0); opacity: 0; }
  to { transform: scaleY(1); opacity: 1; }
}

.scroll-ornament {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 0;
}

.rod {
  flex: 1;
  height: 4px;
  background: linear-gradient(90deg, transparent, #c9a44a, #ffd700, #c9a44a, transparent);
  border-radius: 2px;
  box-shadow: 0 0 8px rgba(255, 215, 0, 0.3);
}

.ornament-center {
  width: 32px;
  height: 32px;
  border: 2px solid #c9a44a;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ffd700;
  font-size: 14px;
  font-family: 'Noto Serif SC', serif;
}

.intro-content {
  padding: 30px 20px;
  min-height: 200px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  animation: contentFade 0.5s ease;
}

@keyframes contentFade {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.intro-chapter {
  font-size: 22px;
  color: #ffd700;
  font-family: 'Noto Serif SC', serif;
  margin-bottom: 20px;
  text-shadow: 0 0 12px rgba(255, 215, 0, 0.3);
}

.intro-text {
  text-align: center;
}

.intro-text p {
  font-size: 15px;
  color: #c0b8d0;
  line-height: 1.8;
  margin: 0 0 6px;
}

.step-dots {
  display: flex;
  justify-content: center;
  gap: 8px;
  margin-top: 16px;
}

.dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
  transition: all 0.3s;
}

.dot.active {
  background: #ffd700;
  box-shadow: 0 0 6px rgba(255, 215, 0, 0.5);
}

.click-hint {
  text-align: center;
  margin-top: 20px;
  font-size: 13px;
  color: #8a8090;
  animation: blink 2s infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}
</style>
