<script setup lang="ts">
import { ref } from 'vue'
import Home from './views/Home.vue'
import Intro from './views/Intro.vue'
import Game from './views/Game.vue'
import Ending from './views/Ending.vue'
import Saves from './views/Saves.vue'

type View = 'home' | 'intro' | 'game' | 'ending'

const currentView = ref<View>('home')
const showSaves = ref(false)
const endingType = ref<'hope' | 'bittersweet' | 'tragic'>('hope')

const startGame = () => {
  currentView.value = 'intro'
}

const introComplete = () => {
  currentView.value = 'game'
}

const loadGame = () => {
  showSaves.value = true
}

const loadFromSlot = async (_slotId: number) => {
  showSaves.value = false
  // Game.vue 会通过 slotId 加载对应存档
  currentView.value = 'game'
}

const onEnding = (type: 'hope' | 'bittersweet' | 'tragic') => {
  endingType.value = type
  currentView.value = 'ending'
}

const restart = () => {
  currentView.value = 'home'
}
</script>

<template>
  <div id="app">
    <!-- 开场动画 -->
    <Intro v-if="currentView === 'intro'" @complete="introComplete" />

    <!-- 主菜单 -->
    <Home v-if="currentView === 'home'" @start="startGame" @load="loadGame" />

    <!-- 游戏主界面 -->
    <Game v-if="currentView === 'game'" @ending="onEnding" />

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
</style>
