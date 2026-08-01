<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { deleteSave, listSaves } from '../api'
import archiveBackdrop from '../assets/cinematic/scene-1972-xian-alley.png'
import type { SaveSlot } from '../types/game'

const emit = defineEmits<{
  load: [slotId: number]
  close: []
}>()

const saves = ref<SaveSlot[]>([])
const loading = ref(true)
const statusMessage = ref('')

onMounted(async () => {
  try {
    const res = await listSaves()
    saves.value = res.data.saves || []
  } catch {
    saves.value = []
    statusMessage.value = '暂时无法连接云端档案。'
  } finally {
    loading.value = false
  }
})

const deleteSlot = async (slotId: number) => {
  if (!confirm('确定删除这个存档？此操作无法撤销。')) return
  try {
    await deleteSave(slotId)
    saves.value = saves.value.filter((save) => save.slot_id !== slotId)
    statusMessage.value = '存档已删除。'
  } catch {
    statusMessage.value = '删除失败，请稍后重试。'
  }
}

const formatTime = (seconds: number) => {
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = seconds % 60
  return `${minutes}:${String(remainingSeconds).padStart(2, '0')}`
}

const getSceneName = (sceneId: string) => {
  const names: Record<string, string> = {
    scene_1972: '1972 · 西安老巷',
    scene_1990: '1990 · 深圳火车站',
    scene_2024: '2024 · 深圳城中村',
    scene_2050: '2050 · 颁奖典礼',
    scene_2089: '2089 · 拾忆实验室',
  }
  return names[sceneId] || sceneId
}
</script>

<template>
  <main class="saves-page" aria-labelledby="saves-title">
    <img class="archive-backdrop" :src="archiveBackdrop" alt="" aria-hidden="true" />
    <div class="archive-grade" aria-hidden="true" />

    <header class="archive-header">
      <div class="archive-brand"><span>拾</span><strong>拾忆</strong></div>
      <button type="button" @click="emit('close')">返回首页</button>
    </header>

    <section class="archive-intro">
      <span>CLOUD MEMORY ARCHIVE</span>
      <h1 id="saves-title">记忆档案</h1>
      <p>每一次选择都会留下可被再次进入的时间坐标。</p>
    </section>

    <section class="archive-panel" aria-live="polite">
      <div class="panel-heading">
        <span>AVAILABLE RECORDS</span>
        <strong>{{ String(saves.length).padStart(2, '0') }}</strong>
      </div>

      <div v-if="loading" class="loading-state">
        <i />
        <p>正在校验云端档案</p>
      </div>

      <div v-else class="save-list">
        <div v-if="saves.length === 0" class="empty-saves">
          <span>NO MEMORY FOUND</span>
          <h2>还没有可读取的记忆</h2>
          <p>开始新旅程后，系统将在重要节点自动保存。</p>
          <button type="button" @click="emit('close')">回到首页</button>
        </div>

        <article v-for="(save, index) in saves" :key="save.slot_id" class="save-card">
          <span class="save-index">{{ String(index + 1).padStart(2, '0') }}</span>
          <div class="save-info">
            <span class="save-scene">{{ getSceneName(save.scene_id) }}</span>
            <h2>{{ save.slot_name }}</h2>
            <div class="save-meta">
              <span>时长 {{ formatTime(save.play_time) }}</span>
              <span>{{ new Date(save.updated_at).toLocaleString('zh-CN') }}</span>
            </div>
          </div>
          <div class="save-actions">
            <button class="btn-load" type="button" @click="emit('load', save.slot_id)">
              进入记忆 <span aria-hidden="true">→</span>
            </button>
            <button class="btn-delete" type="button" @click="deleteSlot(save.slot_id)">删除</button>
          </div>
        </article>
      </div>

      <p v-if="statusMessage" class="status-message" role="status">{{ statusMessage }}</p>
    </section>

    <footer class="archive-footer">
      <span>AUTHORIZED MEMORY HEALERS ONLY</span><i /><span>SECURE SESSION</span>
    </footer>
  </main>
</template>

<style scoped>
.saves-page {
  position: relative;
  width: 100vw;
  height: 100vh;
  overflow: hidden;
  color: var(--paper-100);
  background: #050606;
}

.archive-backdrop,
.archive-grade {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}

.archive-backdrop {
  object-fit: cover;
  object-position: 33% center;
  filter: saturate(0.62) contrast(1.08);
}

.archive-grade {
  background:
    linear-gradient(90deg, rgba(3, 4, 3, 0.45), rgba(3, 4, 3, 0.82) 47%, rgba(3, 4, 3, 0.97) 72%),
    linear-gradient(180deg, rgba(3, 4, 3, 0.58), transparent 30%, rgba(3, 4, 3, 0.76));
}

.archive-header {
  position: absolute;
  z-index: 2;
  top: 0;
  right: 0;
  left: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: max(1.35rem, env(safe-area-inset-top)) var(--safe-inline);
}

.archive-brand {
  display: flex;
  gap: 0.65rem;
  align-items: center;
}

.archive-brand span {
  display: grid;
  width: 2rem;
  height: 2rem;
  place-items: center;
  border: 1px solid rgba(214, 173, 102, 0.6);
  color: var(--gold-300);
}

.archive-brand strong {
  font-size: 0.75rem;
  font-weight: 500;
  letter-spacing: 0.28em;
}

.archive-header button {
  min-height: 2.5rem;
  padding: 0 0.9rem;
  border: 1px solid rgba(215, 196, 162, 0.15);
  color: rgba(241, 229, 206, 0.62);
  background: rgba(5, 6, 6, 0.48);
  cursor: pointer;
}

.archive-intro {
  position: absolute;
  z-index: 2;
  top: 50%;
  left: var(--safe-inline);
  width: min(26rem, 32vw);
  transform: translateY(-50%);
}

.archive-intro > span,
.panel-heading > span,
.empty-saves > span,
.archive-footer {
  color: var(--gold-300);
  font:
    600 0.52rem/1.2 ui-monospace,
    monospace;
  letter-spacing: 0.22em;
}

.archive-intro h1 {
  margin: 0.8rem 0 1.1rem;
  font-size: clamp(3.2rem, 6vw, 6rem);
  font-weight: 400;
  line-height: 1.1;
  letter-spacing: 0.08em;
}

.archive-intro p {
  margin: 0;
  padding-top: 1rem;
  border-top: 1px solid rgba(214, 173, 102, 0.32);
  color: rgba(241, 229, 206, 0.62);
  font-size: 0.82rem;
  line-height: 1.9;
  letter-spacing: 0.1em;
}

.archive-panel {
  position: absolute;
  z-index: 3;
  top: 50%;
  right: var(--safe-inline);
  display: flex;
  width: min(43rem, 54vw);
  height: min(34rem, 72vh);
  flex-direction: column;
  border-top: 1px solid rgba(214, 173, 102, 0.4);
  border-bottom: 1px solid rgba(215, 196, 162, 0.13);
  background: rgba(6, 7, 7, 0.78);
  box-shadow: 0 2rem 6rem rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(20px);
  transform: translateY(-50%);
}

.panel-heading {
  display: flex;
  flex: 0 0 auto;
  align-items: center;
  justify-content: space-between;
  min-height: 4.3rem;
  padding: 0 1.4rem;
  border-bottom: 1px solid rgba(215, 196, 162, 0.1);
}

.panel-heading strong {
  color: var(--gold-300);
  font:
    500 1rem/1 ui-monospace,
    monospace;
}

.save-list {
  flex: 1;
  overflow-y: auto;
}

.save-card {
  display: grid;
  grid-template-columns: 2.5rem 1fr auto;
  gap: 1rem;
  align-items: center;
  min-height: 7rem;
  padding: 1rem 1.4rem;
  border-bottom: 1px solid rgba(215, 196, 162, 0.08);
  transition: background 180ms ease;
}

.save-card:hover {
  background: rgba(166, 109, 44, 0.07);
}

.save-index {
  color: var(--gold-300);
  font:
    500 0.65rem/1 ui-monospace,
    monospace;
}

.save-scene {
  color: rgba(214, 173, 102, 0.72);
  font-size: 0.65rem;
  letter-spacing: 0.14em;
}

.save-info h2 {
  margin: 0.35rem 0;
  font-size: 1.05rem;
  font-weight: 500;
  letter-spacing: 0.1em;
}

.save-meta {
  display: flex;
  gap: 1rem;
  color: rgba(215, 196, 162, 0.42);
  font-size: 0.62rem;
}

.save-actions {
  display: flex;
  gap: 0.45rem;
}

.save-actions button,
.empty-saves button {
  min-height: 2.55rem;
  padding: 0 0.8rem;
  border: 1px solid rgba(215, 196, 162, 0.14);
  color: rgba(241, 229, 206, 0.65);
  background: transparent;
  cursor: pointer;
}

.btn-load:hover {
  border-color: rgba(214, 173, 102, 0.55);
  color: var(--paper-100);
}

.btn-delete:hover {
  border-color: rgba(185, 73, 54, 0.45);
  color: #d88778;
}

.empty-saves,
.loading-state {
  display: flex;
  height: 100%;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  text-align: center;
}

.empty-saves h2 {
  margin: 0.9rem 0 0.5rem;
  font-size: 1.4rem;
  font-weight: 500;
}

.empty-saves p,
.loading-state p {
  margin: 0 0 1.4rem;
  color: rgba(215, 196, 162, 0.46);
  font-size: 0.75rem;
}

.loading-state i {
  width: 12rem;
  height: 1px;
  margin-bottom: 1rem;
  overflow: hidden;
  background: linear-gradient(90deg, transparent, var(--gold-300), transparent);
  animation: scan 1.2s ease-in-out infinite;
}

.status-message {
  margin: 0;
  padding: 0.65rem 1.4rem;
  border-top: 1px solid rgba(215, 196, 162, 0.08);
  color: rgba(214, 173, 102, 0.7);
  font-size: 0.66rem;
}

.archive-footer {
  position: absolute;
  z-index: 2;
  right: var(--safe-inline);
  bottom: max(1.4rem, env(safe-area-inset-bottom));
  left: var(--safe-inline);
  display: flex;
  align-items: center;
  gap: 0.7rem;
  color: rgba(215, 196, 162, 0.38);
}

.archive-footer i {
  width: 3rem;
  height: 1px;
  background: rgba(214, 173, 102, 0.23);
}

@keyframes scan {
  50% {
    opacity: 0.3;
    transform: scaleX(0.45);
  }
}

@media (max-width: 820px), (max-aspect-ratio: 4/5) {
  .archive-backdrop {
    object-position: 30% center;
  }

  .archive-grade {
    background: rgba(3, 4, 3, 0.8);
  }

  .archive-header {
    padding-right: 1rem;
    padding-left: 1rem;
  }

  .archive-intro {
    top: 5.5rem;
    right: 1rem;
    left: 1rem;
    width: auto;
    transform: none;
  }

  .archive-intro h1 {
    margin: 0.45rem 0;
    font-size: 2.6rem;
  }

  .archive-intro p {
    display: none;
  }

  .archive-panel {
    top: 11rem;
    right: 1rem;
    bottom: max(3rem, calc(env(safe-area-inset-bottom) + 2.5rem));
    left: 1rem;
    width: auto;
    height: auto;
    transform: none;
  }

  .save-card {
    grid-template-columns: 1.8rem 1fr;
    min-height: 8rem;
  }

  .save-actions {
    grid-column: 2;
  }

  .save-meta {
    flex-direction: column;
    gap: 0.2rem;
  }

  .archive-footer {
    right: 1rem;
    left: 1rem;
  }
}

@media (prefers-reduced-motion: reduce) {
  .loading-state i {
    animation: none;
  }
}
</style>
