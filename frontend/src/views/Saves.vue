<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { listSaves, deleteSave } from '../api'
import type { SaveSlot } from '../types/game'

const emit = defineEmits<{
  load: [slotId: number]
  close: []
}>()

const saves = ref<SaveSlot[]>([])
const loading = ref(true)

onMounted(async () => {
  try {
    const res = await listSaves()
    saves.value = res.data.saves || []
  } catch {
    saves.value = []
  } finally {
    loading.value = false
  }
})

const loadSlot = (slotId: number) => {
  emit('load', slotId)
}

const deleteSlot = async (slotId: number) => {
  if (!confirm('确定删除这个存档？')) return
  try {
    await deleteSave(slotId)
    saves.value = saves.value.filter(s => s.slot_id !== slotId)
  } catch {
    alert('删除失败')
  }
}

const formatTime = (seconds: number) => {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m}:${String(s).padStart(2, '0')}`
}

const getSceneName = (sceneId: string) => {
  const names: Record<string, string> = {
    scene_1972: '1972 · 西安老巷',
    scene_2024: '2024 · 深圳城中村',
    scene_2089: '2089 · 拾忆实验室',
  }
  return names[sceneId] || sceneId
}
</script>

<template>
  <div class="save-overlay" @click.self="emit('close')">
    <div class="save-panel">
      <div class="save-header">
        <h2>📂 存档管理</h2>
        <button class="btn-close" @click="emit('close')">✕</button>
      </div>

      <div class="save-list" v-if="!loading">
        <div v-if="saves.length === 0" class="empty-saves">
          <p>暂无存档</p>
          <p class="hint">游戏过程中会自动创建存档</p>
        </div>
        <div
          v-for="save in saves"
          :key="save.slot_id"
          class="save-card"
        >
          <div class="save-info">
            <div class="save-name">{{ save.slot_name }}</div>
            <div class="save-meta">
              <span class="save-scene">{{ getSceneName(save.scene_id) }}</span>
              <span class="save-time">⏱ {{ formatTime(save.play_time) }}</span>
            </div>
            <div class="save-date">{{ new Date(save.updated_at).toLocaleString('zh-CN') }}</div>
          </div>
          <div class="save-actions">
            <button class="btn-load" @click="loadSlot(save.slot_id)">读取</button>
            <button class="btn-delete" @click="deleteSlot(save.slot_id)">删除</button>
          </div>
        </div>
      </div>

      <div v-else class="loading-state">
        <div class="spinner" />
        <p>加载存档...</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.save-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 200;
  backdrop-filter: blur(6px);
}

.save-panel {
  width: 520px;
  max-height: 70vh;
  background: linear-gradient(135deg, #1a1a3e, #2a2a5e);
  border: 1px solid rgba(100, 150, 255, 0.25);
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.save-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid rgba(100, 150, 255, 0.15);
}

.save-header h2 {
  margin: 0;
  font-size: 20px;
  color: #e0e0ff;
}

.btn-close {
  background: none;
  border: none;
  color: rgba(150, 170, 220, 0.6);
  font-size: 20px;
  cursor: pointer;
  padding: 4px;
}

.btn-close:hover {
  color: #e0e0ff;
}

.save-list {
  flex: 1;
  overflow-y: auto;
  padding: 16px 20px;
}

.empty-saves {
  text-align: center;
  padding: 40px 0;
  color: rgba(150, 170, 220, 0.5);
}

.empty-saves .hint {
  font-size: 13px;
  margin-top: 8px;
  color: rgba(150, 170, 220, 0.3);
}

.save-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(100, 150, 255, 0.1);
  margin-bottom: 10px;
  transition: all 0.2s;
}

.save-card:hover {
  background: rgba(255, 255, 255, 0.07);
  border-color: rgba(100, 150, 255, 0.2);
}

.save-name {
  font-size: 15px;
  font-weight: 600;
  color: #e0e0ff;
  margin-bottom: 4px;
}

.save-meta {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: rgba(150, 170, 220, 0.6);
  margin-bottom: 2px;
}

.save-date {
  font-size: 11px;
  color: rgba(150, 170, 220, 0.35);
}

.save-actions {
  display: flex;
  gap: 8px;
}

.btn-load, .btn-delete {
  padding: 6px 16px;
  border-radius: 6px;
  border: none;
  font-size: 13px;
  cursor: pointer;
  font-family: 'Noto Serif SC', serif;
  transition: all 0.2s;
}

.btn-load {
  background: rgba(58, 95, 205, 0.4);
  color: #e0e0ff;
}

.btn-load:hover {
  background: rgba(58, 95, 205, 0.6);
}

.btn-delete {
  background: rgba(255, 80, 80, 0.15);
  color: rgba(255, 120, 120, 0.7);
}

.btn-delete:hover {
  background: rgba(255, 80, 80, 0.3);
  color: #ff7878;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 0;
  color: rgba(150, 170, 220, 0.5);
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid rgba(100, 150, 255, 0.2);
  border-top-color: #60a5fa;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-bottom: 12px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
