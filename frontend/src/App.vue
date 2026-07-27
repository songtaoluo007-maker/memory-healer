<script setup lang="ts">
import { computed, onErrorCaptured, ref } from 'vue'
import { RouterView, useRoute, useRouter } from 'vue-router'
import { useWebVitals } from './composables/useWebVitals'
import type { EndingType } from './types/game'

const router = useRouter()
const route = useRoute()
const globalError = ref<string | null>(null)

useWebVitals()

onErrorCaptured((error, _instance, info) => {
  console.error('[拾忆错误]', error, info)
  globalError.value = error.message || '记忆场暂时失去连接'
  return false
})

const loadSlotId = computed(() => {
  const raw = route.query.slot
  if (typeof raw !== 'string') return null
  const slot = Number.parseInt(raw, 10)
  return Number.isInteger(slot) ? slot : null
})

const endingType = computed<EndingType>(() => {
  const type = route.params.type
  return type === 'legacy' || type === 'bittersweet' || type === 'tragic' ? type : 'hope'
})

const startGame = () => router.push({ name: 'prologue' })

const completeStep = () => {
  if (route.name === 'prologue') {
    return router.push({
      name: localStorage.getItem('mh_tutorial_done') ? 'memory' : 'tutorial',
    })
  }
  return router.push({ name: 'memory' })
}

const loadGame = (slotId?: number) => {
  if (typeof slotId === 'number') {
    return router.push({ name: 'memory', query: { slot: String(slotId) } })
  }
  return router.push({ name: 'saves' })
}

const showEnding = (type: EndingType) => router.push({ name: 'ending', params: { type } })
const goHome = () => router.push({ name: 'home' })
</script>

<template>
  <main class="app-shell">
    <Transition name="error-fade">
      <div v-if="globalError" class="error-overlay" role="alertdialog" aria-modal="true">
        <div class="error-box">
          <span class="error-kicker">MEMORY FIELD / SIGNAL LOST</span>
          <h2>记忆场暂时中断</h2>
          <p>{{ globalError }}</p>
          <button type="button" @click="globalError = null">返回画面</button>
        </div>
      </div>
    </Transition>

    <RouterView v-slot="{ Component, route: activeRoute }">
      <Transition name="film-cut" mode="out-in">
        <component
          :is="Component"
          :key="activeRoute.fullPath"
          :load-slot-id="loadSlotId"
          :ending-type="endingType"
          @start="startGame"
          @load="loadGame"
          @complete="completeStep"
          @ending="showEnding"
          @restart="goHome"
          @close="goHome"
        />
      </Transition>
    </RouterView>
  </main>
</template>

<style scoped>
.app-shell {
  width: 100%;
  height: 100%;
  overflow: hidden;
  background: var(--ink-950);
}

.error-overlay {
  position: fixed;
  z-index: 9999;
  inset: 0;
  display: grid;
  place-items: center;
  padding: 1.5rem;
  background: rgba(4, 5, 5, 0.84);
  backdrop-filter: blur(16px);
}

.error-box {
  width: min(30rem, 100%);
  padding: clamp(1.5rem, 4vw, 3rem);
  border: 1px solid rgba(214, 173, 102, 0.26);
  background:
    linear-gradient(135deg, rgba(185, 73, 54, 0.08), transparent 46%), rgba(13, 14, 15, 0.96);
  box-shadow: 0 2rem 6rem rgba(0, 0, 0, 0.6);
}

.error-kicker {
  color: var(--gold-300);
  font:
    600 0.65rem/1.2 ui-monospace,
    monospace;
  letter-spacing: 0.2em;
}

.error-box h2 {
  margin: 1rem 0 0.6rem;
  font-size: clamp(1.5rem, 3vw, 2rem);
  font-weight: 500;
}

.error-box p {
  margin: 0 0 1.5rem;
  color: var(--paper-300);
  line-height: 1.8;
}

.error-box button {
  min-height: 2.75rem;
  padding: 0 1.4rem;
  border: 1px solid var(--gold-500);
  color: var(--paper-100);
  background: transparent;
  cursor: pointer;
}

.film-cut-enter-active,
.film-cut-leave-active {
  transition:
    opacity 480ms var(--ease-cinema),
    filter 480ms var(--ease-cinema);
}

.film-cut-enter-from,
.film-cut-leave-to {
  opacity: 0;
  filter: brightness(0.45) blur(3px);
}

.error-fade-enter-active,
.error-fade-leave-active {
  transition: opacity 180ms ease;
}

.error-fade-enter-from,
.error-fade-leave-to {
  opacity: 0;
}
</style>
