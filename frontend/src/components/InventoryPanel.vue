<script setup lang="ts">
import { defineAsyncComponent } from 'vue'
import type { GameState } from '../types/game'

const MemoryProgress = defineAsyncComponent(() => import('./MemoryProgress.vue'))

defineProps<{
  gameState: GameState
  collectedCount: number
  totalFragments: number
}>()

const emit = defineEmits<{ close: [] }>()
</script>

<template>
  <div class="inventory-panel" role="complementary" aria-label="记忆碎片背包">
    <div class="inventory-header">
      <h3>📦 记忆碎片</h3>
      <button @click="emit('close')">✕</button>
    </div>
    <div class="inventory-progress">
      <MemoryProgress :collected="collectedCount" :total="totalFragments" />
    </div>
    <div class="inventory-list">
      <div
        v-for="(frag, id) in gameState.fragment_states"
        :key="id"
        class="inventory-item"
        :class="{ collected: frag.collected }"
      >
        <span class="frag-icon">{{ frag.collected ? '✦' : '○' }}</span>
        <span class="frag-name">{{ frag.collected ? frag.name : '???' }}</span>
        <span class="frag-scene">{{ frag.scene }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.inventory-panel {
  position: fixed;
  right: 16px;
  top: 80px;
  bottom: 120px;
  width: 280px;
  background: rgba(10, 10, 30, 0.95);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(232, 180, 80, 0.15);
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  z-index: 80;
  overflow: hidden;
}
.inventory-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 16px;
  border-bottom: 1px solid rgba(255,255,255,0.06);
}
.inventory-header h3 {
  font-size: 15px;
  color: #e8b450;
}
.inventory-header button {
  background: none;
  border: none;
  color: rgba(255,255,255,0.4);
  font-size: 18px;
  cursor: pointer;
}
.inventory-progress {
  padding: 12px 16px;
  border-bottom: 1px solid rgba(255,255,255,0.04);
}
.inventory-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}
.inventory-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  border-radius: 6px;
  transition: background 0.2s;
}
.inventory-item:hover {
  background: rgba(255,255,255,0.03);
}
.inventory-item.collected {
  background: rgba(232, 180, 80, 0.05);
}
.frag-icon {
  font-size: 14px;
  flex-shrink: 0;
}
.frag-name {
  font-size: 13px;
  color: #e0e0e0;
  flex: 1;
}
.frag-scene {
  font-size: 11px;
  color: rgba(255,255,255,0.3);
}
.inventory-item:not(.collected) .frag-name {
  color: rgba(255,255,255,0.3);
  font-style: italic;
}

@media (max-width: 768px) {
  .inventory-panel {
    width: 100%;
    right: 0;
    top: 60px;
    bottom: 80px;
    border-radius: 12px 12px 0 0;
    max-height: 60vh;
  }
}
</style>
