<script setup lang="ts">
/**
 * 存档管理 — 10槽位存档/读档面板
 * 皮影戏风格卷轴式
 */
import { ref, onMounted, computed } from 'vue'
import { listSaves, deleteSave } from '../api'
import { useI18n } from '../composables/useI18n'
import type { SaveSlot } from '../types/game'

const MAX_SLOTS = 10

const emit = defineEmits<{
  load: [slotId: number]
  close: []
}>()

const { t } = useI18n()
const saves = ref<SaveSlot[]>([])
const loading = ref(true)

onMounted(async () => {
  await refreshSaves()
})

async function refreshSaves() {
  loading.value = true
  try {
    const res = await listSaves()
    saves.value = res.data.saves || []
  } catch {
    saves.value = []
  } finally {
    loading.value = false
  }
}

// 合并所有10个槽位
const allSlots = computed(() => {
  const slots: Array<{ slot_id: number; slot: SaveSlot | null }> = []
  for (let i = 0; i <= MAX_SLOTS; i++) {
    const found = saves.value.find(s => s.slot_id === i) || null
    slots.push({ slot_id: i, slot: found })
  }
  return slots
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
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  if (h > 0) return `${h}h${m}m`
  return `${m}:${String(seconds % 60).padStart(2, '0')}`
}

const getSceneName = (sceneId: string) => {
  const names: Record<string, string> = {
    scene_1972: '1972 · 西安老巷',
    scene_2024: '2024 · 深圳城中村',
    scene_2089: '2089 · 拾忆实验室',
    scene_1990: '1990 · 深圳火车站',
    scene_2050: '2050 · 北京颁奖典礼',
  }
  return names[sceneId] || sceneId || '未知'
}

const slotLabel = (slotId: number) => {
  if (slotId === 0) return '自动存档'
  return `存档位 ${slotId}`
}
</script>

<template>
  <div class="save-overlay" @click.self="emit('close')" role="dialog" aria-label="存档管理" aria-modal="true">
    <div class="save-scroll">
      <div class="scrl-top">
        <div class="rod"></div>
        <div class="orn">存</div>
        <div class="rod"></div>
      </div>

      <div class="save-body">
        <h2 class="save-title">存档管理</h2>
        <p class="save-sub">选择一个存档位读取</p>

        <div v-if="loading" class="loading-state">
          <div class="spinner" />
          <p>加载中...</p>
        </div>

        <div v-else class="slot-list">
          <div
            v-for="{ slot_id, slot } in allSlots"
            :key="slot_id"
            class="slot-card"
            :class="{ filled: !!slot, auto: slot_id === 0 }"
          >
            <div class="slot-header">
              <span class="slot-label">{{ slotLabel(slot_id) }}</span>
              <span v-if="slot" class="slot-scene">{{ getSceneName(slot.scene_id) }}</span>
            </div>

            <div v-if="slot" class="slot-info">
              <div class="slot-name">{{ slot.slot_name || '未命名存档' }}</div>
              <div class="slot-meta">
                <span>⏱ {{ formatTime(slot.play_time) }}</span>
                <span>{{ new Date(slot.updated_at).toLocaleString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) }}</span>
              </div>
            </div>

            <div v-else class="slot-empty">
              <span>空</span>
            </div>

            <div class="slot-actions">
              <button
                v-if="slot"
                class="act-btn load-btn"
                @click="loadSlot(slot_id)"
              >
                读取
              </button>
              <button
                v-if="slot"
                class="act-btn del-btn"
                @click="deleteSlot(slot_id)"
              >
                删除
              </button>
            </div>
          </div>
        </div>
      </div>

      <div class="scrl-top">
        <div class="rod"></div>
      </div>

      <button class="close-btn" @click="emit('close')">✕</button>
    </div>
  </div>
</template>

<style scoped>
.save-overlay {
  position: fixed;
  inset: 0;
  z-index: 200;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0,0,0,0.6);
  backdrop-filter: blur(4px);
}

.save-scroll {
  width: 500px;
  max-width: 94vw;
  max-height: 85vh;
  overflow-y: auto;
  background: linear-gradient(160deg, #120f1a, #1a1525);
  border: 1px solid rgba(255,180,60,0.2);
  border-radius: 14px;
  position: relative;
  animation: unfurl 0.4s ease;
}

@keyframes unfurl {
  from { transform: scaleY(0.9); opacity: 0; }
  to { transform: scaleY(1); opacity: 1; }
}

.scrl-top {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 16px;
}

.rod {
  flex: 1;
  height: 3px;
  background: linear-gradient(90deg, transparent, #c9a44a, transparent);
  border-radius: 2px;
}

.orn {
  width: 28px; height: 28px;
  border: 2px solid #c9a44a;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ffd700;
  font-size: 12px;
  font-family: 'Noto Serif SC', serif;
}

.save-body {
  padding: 16px 20px 20px;
}

.save-title {
  font-size: 20px;
  color: #e0d8c8;
  font-family: 'Noto Serif SC', serif;
  margin: 0 0 4px;
}

.save-sub {
  font-size: 13px;
  color: #6a6070;
  margin: 0 0 16px;
}

.slot-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.slot-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 10px;
  transition: all 0.2s;
}

.slot-card.filled {
  border-color: rgba(255,180,60,0.15);
  background: rgba(255,180,60,0.03);
}

.slot-card.auto {
  border-style: dashed;
}

.slot-card:hover {
  background: rgba(255,255,255,0.06);
  border-color: rgba(255,180,60,0.2);
}

.slot-header {
  min-width: 70px;
}

.slot-label {
  display: block;
  font-size: 12px;
  color: #c0b8d0;
  font-weight: 600;
}

.slot-scene {
  display: block;
  font-size: 10px;
  color: #6a6070;
  margin-top: 2px;
}

.slot-info {
  flex: 1;
  min-width: 0;
}

.slot-name {
  font-size: 13px;
  color: #e0d8c8;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.slot-meta {
  display: flex;
  gap: 10px;
  font-size: 11px;
  color: #6a6070;
  margin-top: 2px;
}

.slot-empty {
  flex: 1;
  font-size: 12px;
  color: #3a3040;
}

.slot-actions {
  display: flex;
  gap: 4px;
  flex-shrink: 0;
}

.act-btn {
  padding: 4px 12px;
  border: none;
  border-radius: 6px;
  font-size: 12px;
  cursor: pointer;
  font-family: 'Noto Serif SC', serif;
  transition: all 0.2s;
}

.load-btn {
  background: rgba(201,164,74,0.2);
  color: #c9a44a;
}

.load-btn:hover {
  background: rgba(201,164,74,0.3);
}

.del-btn {
  background: rgba(255,80,80,0.1);
  color: rgba(255,120,120,0.6);
}

.del-btn:hover {
  background: rgba(255,80,80,0.2);
  color: #ff7878;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px 0;
  color: #6a6070;
}

.spinner {
  width: 28px; height: 28px;
  border: 3px solid rgba(201,164,74,0.15);
  border-top-color: #c9a44a;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
  margin-bottom: 10px;
}

@keyframes spin { to { transform: rotate(360deg); } }

.close-btn {
  position: absolute;
  top: 10px;
  right: 10px;
  width: 26px; height: 26px;
  border: none;
  background: rgba(255,255,255,0.04);
  border-radius: 50%;
  color: #6a6070;
  cursor: pointer;
  font-size: 13px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-btn:hover {
  background: rgba(255,255,255,0.08);
  color: #e0d8c8;
}
</style>
