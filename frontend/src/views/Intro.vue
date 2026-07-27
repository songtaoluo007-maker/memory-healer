<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import prologueBackdrop from '../assets/cinematic/scene-1972-xian-alley.png'

const emit = defineEmits<{
  complete: []
}>()

const phase = ref(0)
const timers: number[] = []

onMounted(() => {
  timers.push(
    window.setTimeout(() => (phase.value = 1), 500),
    window.setTimeout(() => (phase.value = 2), 2300),
    window.setTimeout(() => (phase.value = 3), 8300),
    window.setTimeout(() => emit('complete'), 9400),
  )
})

onUnmounted(() => timers.forEach(window.clearTimeout))

const skip = () => emit('complete')
</script>

<template>
  <section class="intro" :class="`phase-${phase}`" aria-label="故事序章">
    <img class="prologue-backdrop" :src="prologueBackdrop" alt="" aria-hidden="true" />
    <div class="prologue-grade" aria-hidden="true" />
    <div class="film-gate" aria-hidden="true"><i /><i /></div>

    <header class="prologue-header">
      <span>拾忆计划 / 档案 001</span>
      <strong>PROLOGUE</strong>
    </header>

    <Transition name="title-reveal">
      <div v-if="phase >= 1 && phase < 3" class="title-screen">
        <span class="title-index">MEMORY HEALER</span>
        <h1><span>拾</span><span>忆</span></h1>
        <p>有些故事从未消失，只是失去了讲述它的人。</p>
      </div>
    </Transition>

    <div v-if="phase >= 2 && phase < 3" class="story-text" aria-live="polite">
      <span class="story-date">2089 / 深圳</span>
      <p class="story-line" style="--delay: 0ms">阿尔茨海默症不再是绝症。</p>
      <p class="story-line" style="--delay: 700ms">拾忆技术可以进入记忆，重走一个人的一生。</p>
      <p class="story-line" style="--delay: 1400ms">但被改变的过去，也会在未来留下回声。</p>
      <p class="story-line highlight" style="--delay: 2400ms">你是第一位记忆修复师。</p>
    </div>

    <button v-if="phase > 0 && phase < 3" class="skip-btn" type="button" @click="skip">
      <span>跳过序章</span><span aria-hidden="true">→</span>
    </button>

    <footer class="prologue-footer">
      <span>RESTORE WHAT TIME FORGOT</span>
      <i />
      <span>01</span>
    </footer>
  </section>
</template>

<style scoped>
.intro {
  position: fixed;
  z-index: 300;
  inset: 0;
  overflow: hidden;
  color: var(--paper-100);
  background: #030403;
  transition:
    opacity 1s ease,
    filter 1s ease;
}

.prologue-backdrop,
.prologue-grade {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}

.prologue-backdrop {
  object-fit: cover;
  object-position: center;
  opacity: 0;
  filter: saturate(0.6) contrast(1.12);
  transform: scale(1.08);
  transition:
    opacity 1.8s ease,
    transform 9s ease-out;
}

.phase-2 .prologue-backdrop {
  opacity: 0.36;
  transform: scale(1.02);
}

.prologue-grade {
  background:
    linear-gradient(90deg, rgba(3, 4, 3, 0.92), rgba(3, 4, 3, 0.4) 55%, rgba(3, 4, 3, 0.76)),
    linear-gradient(180deg, #030403, transparent 28% 68%, #030403);
}

.film-gate i {
  position: absolute;
  z-index: 3;
  right: 0;
  left: 0;
  height: clamp(1.5rem, 5vh, 4rem);
  background: #030403;
}

.film-gate i:first-child {
  top: 0;
}

.film-gate i:last-child {
  bottom: 0;
}

.prologue-header {
  position: absolute;
  z-index: 5;
  top: max(1.5rem, env(safe-area-inset-top));
  right: var(--safe-inline);
  left: var(--safe-inline);
  display: flex;
  justify-content: space-between;
  color: rgba(215, 196, 162, 0.48);
  font:
    500 0.52rem/1 ui-monospace,
    monospace;
  letter-spacing: 0.22em;
}

.prologue-header strong {
  color: var(--gold-300);
  font-weight: 500;
}

.title-screen {
  position: absolute;
  z-index: 4;
  top: 50%;
  left: var(--safe-inline);
  width: min(34rem, 46vw);
  transform: translateY(-55%);
}

.title-index,
.story-date {
  color: var(--gold-300);
  font:
    600 0.55rem/1.2 ui-monospace,
    monospace;
  letter-spacing: 0.26em;
}

.title-screen h1 {
  display: flex;
  gap: clamp(1rem, 2vw, 2rem);
  margin: 1rem 0;
  font-size: clamp(5.2rem, 9vw, 8.5rem);
  font-weight: 400;
  line-height: 1;
}

.title-screen h1 span:last-child {
  transform: translateY(1rem);
}

.title-screen p {
  width: fit-content;
  padding-top: 1rem;
  border-top: 1px solid rgba(214, 173, 102, 0.35);
  color: rgba(241, 229, 206, 0.66);
  font-size: 0.85rem;
  letter-spacing: 0.14em;
}

.phase-2 .title-screen {
  opacity: 0.13;
  filter: blur(1px);
  transform: translateY(-55%) scale(0.97);
  transition:
    opacity 1.2s ease,
    transform 1.2s ease,
    filter 1.2s ease;
}

.story-text {
  position: absolute;
  z-index: 6;
  top: 50%;
  right: var(--safe-inline);
  width: min(35rem, 45vw);
  transform: translateY(-45%);
}

.story-date {
  display: block;
  margin-bottom: 1.5rem;
}

.story-line {
  margin: 0 0 0.9rem;
  color: rgba(241, 229, 206, 0.75);
  font-size: clamp(0.9rem, 1.3vw, 1.15rem);
  line-height: 1.8;
  letter-spacing: 0.11em;
  opacity: 0;
  transform: translateY(0.8rem);
  animation: line-in 800ms var(--ease-cinema) var(--delay) forwards;
}

.story-line.highlight {
  margin-top: 1.5rem;
  padding-top: 1rem;
  border-top: 1px solid rgba(185, 73, 54, 0.52);
  color: var(--paper-100);
  font-size: clamp(1.05rem, 1.6vw, 1.35rem);
}

.skip-btn {
  position: absolute;
  z-index: 8;
  right: var(--safe-inline);
  bottom: max(4.8rem, env(safe-area-inset-bottom));
  display: flex;
  gap: 1rem;
  align-items: center;
  min-height: 2.8rem;
  padding: 0 1rem;
  border: 1px solid rgba(215, 196, 162, 0.18);
  color: rgba(241, 229, 206, 0.6);
  background: rgba(5, 6, 6, 0.54);
  cursor: pointer;
}

.skip-btn:hover {
  border-color: rgba(214, 173, 102, 0.55);
  color: var(--paper-100);
}

.prologue-footer {
  position: absolute;
  z-index: 5;
  right: var(--safe-inline);
  bottom: max(1.6rem, env(safe-area-inset-bottom));
  left: var(--safe-inline);
  display: flex;
  align-items: center;
  gap: 0.7rem;
  color: rgba(215, 196, 162, 0.38);
  font:
    500 0.48rem/1 ui-monospace,
    monospace;
  letter-spacing: 0.2em;
}

.prologue-footer i {
  width: 3rem;
  height: 1px;
  background: rgba(214, 173, 102, 0.25);
}

.phase-3 {
  opacity: 0;
  filter: brightness(0.35);
}

.title-reveal-enter-active {
  transition:
    opacity 1s ease,
    transform 1.4s var(--ease-cinema);
}

.title-reveal-enter-from {
  opacity: 0;
  transform: translateY(-48%);
}

@keyframes line-in {
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (max-width: 760px), (max-aspect-ratio: 4/5) {
  .prologue-backdrop {
    object-position: 34% center;
  }

  .title-screen,
  .story-text {
    right: 1.25rem;
    left: 1.25rem;
    width: auto;
  }

  .title-screen {
    top: 32%;
  }

  .story-text {
    top: 56%;
    transform: translateY(-40%);
  }

  .phase-2 .title-screen {
    opacity: 0.08;
  }

  .story-line {
    margin-bottom: 0.6rem;
    font-size: 0.88rem;
  }

  .skip-btn {
    right: 1rem;
    bottom: max(4rem, calc(env(safe-area-inset-bottom) + 3.5rem));
  }

  .prologue-header,
  .prologue-footer {
    right: 1rem;
    left: 1rem;
  }
}

@media (prefers-reduced-motion: reduce) {
  .prologue-backdrop,
  .story-line {
    animation: none;
    opacity: 1;
    transform: none;
  }
}
</style>
