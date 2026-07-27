<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import tutorialBackdrop from '../assets/cinematic/scene-1972-xian-alley.png'

const emit = defineEmits<{
  complete: []
}>()

const currentStep = ref(0)
const visible = ref(false)
let revealTimer: number | null = null
let completeTimer: number | null = null

const steps = [
  {
    mark: '识',
    title: '欢迎，记忆修复师',
    desc: '你将进入陈守义的记忆，通过观察、对话与选择，帮助他找回遗失的往事。',
  },
  {
    mark: '探',
    title: '观察记忆场',
    desc: '场景中的暖色光点是可触碰的记忆锚点。探索它们，会发现物件、人物与隐藏线索。',
  },
  {
    mark: '言',
    title: '与记忆中的人交谈',
    desc: '选择人物后可以自由发问。你的语气与决定会改变信任，也会打开不同的记忆路径。',
  },
  {
    mark: '藏',
    title: '归档记忆碎片',
    desc: '碎片是重建一生的证据。它们会被收录进档案，并在跨越年代时彼此产生因果。',
  },
  {
    mark: '启',
    title: '第一次修复即将开始',
    desc: '没有旁观者的选择。你在过去触碰的每一束光，都会在未来留下回声。',
  },
]

onMounted(() => {
  if (localStorage.getItem('mh_tutorial_done')) {
    emit('complete')
    return
  }
  revealTimer = window.setTimeout(() => (visible.value = true), 300)
})

onUnmounted(() => {
  if (revealTimer !== null) window.clearTimeout(revealTimer)
  if (completeTimer !== null) window.clearTimeout(completeTimer)
})

const finish = () => {
  localStorage.setItem('mh_tutorial_done', '1')
  visible.value = false
  completeTimer = window.setTimeout(() => emit('complete'), 400)
}

const next = () => {
  if (currentStep.value < steps.length - 1) {
    currentStep.value += 1
  } else {
    finish()
  }
}

const skip = () => finish()
</script>

<template>
  <Transition name="tutorial">
    <main v-if="visible" class="tutorial-overlay" aria-labelledby="tutorial-title">
      <img class="tutorial-backdrop" :src="tutorialBackdrop" alt="" aria-hidden="true" />
      <div class="tutorial-grade" aria-hidden="true" />

      <header class="tutorial-header">
        <span>拾忆 / 操作校准</span>
        <strong>FIELD ORIENTATION</strong>
      </header>

      <section class="tutorial-card">
        <div class="step-indicator" aria-label="教程进度">
          <button
            v-for="(step, index) in steps"
            :key="step.mark"
            type="button"
            :class="{ active: index === currentStep, done: index < currentStep }"
            :aria-label="`第 ${index + 1} 步：${step.title}`"
            :aria-current="index === currentStep ? 'step' : undefined"
            @click="currentStep = index"
          >
            <span>{{ String(index + 1).padStart(2, '0') }}</span
            ><i />
          </button>
        </div>

        <div class="step-content">
          <span class="step-mark" aria-hidden="true">{{ steps[currentStep].mark }}</span>
          <span class="step-index"
            >ORIENTATION / {{ String(currentStep + 1).padStart(2, '0') }}</span
          >
          <h1 id="tutorial-title">{{ steps[currentStep].title }}</h1>
          <p>{{ steps[currentStep].desc }}</p>
        </div>

        <footer class="step-actions">
          <button class="btn-skip" type="button" @click="skip">跳过校准</button>
          <button class="btn-next" type="button" @click="next">
            <span>{{ currentStep < steps.length - 1 ? '下一步' : '进入记忆' }}</span>
            <span aria-hidden="true">→</span>
          </button>
        </footer>
      </section>
    </main>
  </Transition>
</template>

<style scoped>
.tutorial-overlay {
  position: fixed;
  z-index: 500;
  inset: 0;
  overflow: hidden;
  color: var(--paper-100);
  background: #030403;
}

.tutorial-backdrop,
.tutorial-grade {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}

.tutorial-backdrop {
  object-fit: cover;
  object-position: 40% center;
  filter: saturate(0.58) contrast(1.1);
}

.tutorial-grade {
  background:
    linear-gradient(90deg, rgba(3, 4, 3, 0.48), rgba(3, 4, 3, 0.88) 52%, rgba(3, 4, 3, 0.95)),
    linear-gradient(180deg, rgba(3, 4, 3, 0.65), transparent 32%, rgba(3, 4, 3, 0.74));
}

.tutorial-header {
  position: absolute;
  z-index: 2;
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

.tutorial-header strong {
  color: var(--gold-300);
  font-weight: 500;
}

.tutorial-card {
  position: absolute;
  z-index: 3;
  top: 50%;
  right: var(--safe-inline);
  display: grid;
  grid-template-columns: 4.2rem 1fr;
  grid-template-rows: 1fr auto;
  width: min(46rem, 62vw);
  min-height: min(30rem, 68vh);
  border-top: 1px solid rgba(214, 173, 102, 0.45);
  border-bottom: 1px solid rgba(215, 196, 162, 0.12);
  background: rgba(6, 7, 7, 0.84);
  box-shadow: 0 2.5rem 7rem rgba(0, 0, 0, 0.62);
  backdrop-filter: blur(20px);
  transform: translateY(-50%);
}

.step-indicator {
  display: flex;
  grid-row: 1 / 3;
  flex-direction: column;
  border-right: 1px solid rgba(215, 196, 162, 0.1);
}

.step-indicator button {
  display: grid;
  min-height: 4.2rem;
  flex: 1;
  place-items: center;
  border: 0;
  border-bottom: 1px solid rgba(215, 196, 162, 0.08);
  color: rgba(215, 196, 162, 0.32);
  background: transparent;
  cursor: pointer;
}

.step-indicator button span {
  font:
    500 0.58rem/1 ui-monospace,
    monospace;
}

.step-indicator button i {
  display: block;
  width: 0;
  height: 1px;
  background: var(--gold-300);
  transition: width 260ms ease;
}

.step-indicator button.active,
.step-indicator button.done {
  color: var(--gold-300);
  background: rgba(166, 109, 44, 0.08);
}

.step-indicator button.active i {
  width: 1.4rem;
}

.step-content {
  position: relative;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: clamp(2rem, 6vw, 5rem);
  overflow: hidden;
}

.step-mark {
  position: absolute;
  right: 1rem;
  bottom: -3rem;
  color: rgba(214, 173, 102, 0.055);
  font-size: clamp(10rem, 22vw, 18rem);
  line-height: 1;
}

.step-index {
  position: relative;
  color: var(--gold-300);
  font:
    600 0.55rem/1.2 ui-monospace,
    monospace;
  letter-spacing: 0.22em;
}

.step-content h1 {
  position: relative;
  margin: 1rem 0 1.2rem;
  font-size: clamp(1.8rem, 4vw, 3rem);
  font-weight: 400;
  letter-spacing: 0.1em;
}

.step-content p {
  position: relative;
  max-width: 31rem;
  margin: 0;
  padding-top: 1.15rem;
  border-top: 1px solid rgba(214, 173, 102, 0.3);
  color: rgba(241, 229, 206, 0.67);
  font-size: clamp(0.82rem, 1.2vw, 0.98rem);
  line-height: 2;
  letter-spacing: 0.08em;
}

.step-actions {
  display: flex;
  grid-column: 2;
  align-items: center;
  justify-content: space-between;
  min-height: 4.5rem;
  padding: 0 1.5rem;
  border-top: 1px solid rgba(215, 196, 162, 0.1);
}

.btn-skip,
.btn-next {
  min-height: 2.7rem;
  cursor: pointer;
}

.btn-skip {
  padding: 0;
  border: 0;
  color: rgba(215, 196, 162, 0.44);
  background: transparent;
}

.btn-next {
  display: flex;
  min-width: 8.5rem;
  align-items: center;
  justify-content: space-between;
  padding: 0 0.9rem;
  border: 1px solid rgba(214, 173, 102, 0.42);
  color: var(--paper-100);
  background: rgba(166, 109, 44, 0.13);
}

.tutorial-enter-active,
.tutorial-leave-active {
  transition:
    opacity 400ms ease,
    filter 400ms ease;
}

.tutorial-enter-from,
.tutorial-leave-to {
  opacity: 0;
  filter: brightness(0.45);
}

@media (max-width: 760px), (max-aspect-ratio: 4/5) {
  .tutorial-grade {
    background: rgba(3, 4, 3, 0.78);
  }

  .tutorial-header {
    right: 1rem;
    left: 1rem;
  }

  .tutorial-card {
    top: auto;
    right: 0;
    bottom: 0;
    left: 0;
    grid-template-columns: 1fr;
    grid-template-rows: auto 1fr auto;
    width: 100%;
    min-height: 63vh;
    padding-bottom: env(safe-area-inset-bottom);
    transform: none;
  }

  .step-indicator {
    grid-row: 1;
    flex-direction: row;
    border-right: 0;
    border-bottom: 1px solid rgba(215, 196, 162, 0.1);
  }

  .step-indicator button {
    min-height: 3.2rem;
    border-right: 1px solid rgba(215, 196, 162, 0.08);
    border-bottom: 0;
  }

  .step-content {
    padding: 2rem 1.4rem;
  }

  .step-actions {
    grid-column: 1;
    padding: 0 1rem;
  }
}
</style>
