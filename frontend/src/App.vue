<script setup lang="ts">
import { ref, onErrorCaptured } from 'vue'
import Home from './views/Home.vue'
import Intro from './views/Intro.vue'
import Game from './views/Game.vue'
import Ending from './views/Ending.vue'
import Saves from './views/Saves.vue'
import type { EndingType } from './types/game'

type View = 'home' | 'intro' | 'game' | 'ending'

const currentView = ref<View>('home')
const showSaves = ref(false)
const endingType = ref<EndingType>('hope')
const loadSlotId = ref<number | null>(null)
const globalError = ref<string | null>(null)

// 全局错误捕获
onErrorCaptured((err, instance, info) => {
  console.error('[拾忆错误]', err, info)
  globalError.value = err.message || '发生了未知错误'
  return false // 阻止错误向上传播
})

const clearError = () => {
  globalError.value = null
}

const startGame = () => {
  loadSlotId.value = null
  currentView.value = 'intro'
}

const introComplete = () => {
  currentView.value = 'game'
}

const loadGame = () => {
  showSaves.value = true
}

const loadFromSlot = async (slotId: number) => {
  showSaves.value = false
  loadSlotId.value = slotId
  currentView.value = 'game'
}

const onEnding = (type: EndingType) => {
  endingType.value = type
  currentView.value = 'ending'
}

const restart = () => {
  loadSlotId.value = null
  currentView.value = 'home'
}
</script>

<template>
  <div id="app">
    <!-- 全局错误提示 -->
    <div v-if="globalError" class="error-overlay" @click="clearError">
      <div class="error-box">
        <div class="error-icon">⚠️</div>
        <div class="error-title">游戏遇到问题</div>
        <div class="error-msg">{{ globalError }}</div>
        <button class="error-btn" @click="clearError">确定</button>
      </div>
    </div>

    <!-- 开场动画 -->
    <Intro v-if="currentView === 'intro'" @complete="introComplete" />

    <!-- 主菜单 -->
    <Home v-if="currentView === 'home'" @start="startGame" @load="loadGame" />

    <!-- 游戏主界面 -->
    <Game v-if="currentView === 'game'" :load-slot-id="loadSlotId" @ending="onEnding" />

    <!-- 结局 -->
    <Ending v-if="currentView === 'ending'" :ending-type="endingType" @restart="restart" />

    <!-- 存档管理弹窗 -->
    <Saves v-if="showSaves" @load="loadFromSlot" @close="showSaves = false" />
  </div>
</template>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  background: #0a0a1a;
  overflow: hidden;
}

#app {
  width: 100vw;
  height: 100vh;
}

::-webkit-scrollbar {
  width: 6px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: rgba(100, 150, 255, 0.2);
  border-radius: 3px;
}

/* 全局错误提示 */
.error-overlay {
  position: fixed;
  inset: 0;
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(8px);
}
.error-box {
  background: linear-gradient(135deg, #1a1a2e, #16213e);
  border: 1px solid rgba(232, 180, 80, 0.3);
  border-radius: 12px;
  padding: 32px;
  max-width: 400px;
  text-align: center;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
}
.error-icon {
  font-size: 48px;
  margin-bottom: 16px;
}
.error-title {
  font-size: 18px;
  font-weight: 600;
  color: #e8b450;
  margin-bottom: 12px;
}
.error-msg {
  font-size: 14px;
  color: #a0a0a0;
  margin-bottom: 24px;
  line-height: 1.6;
}
.error-btn {
  background: linear-gradient(135deg, #e8b450, #d4a03c);
  color: #1a1a2e;
  border: none;
  padding: 10px 32px;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}
.error-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(232, 180, 80, 0.3);
}
</style>
