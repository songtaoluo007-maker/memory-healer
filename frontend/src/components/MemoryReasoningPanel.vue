<script setup lang="ts">
import { computed } from 'vue'
import { buildReasoningSnapshot } from '../domain/memoryReasoning'
import { getFragmentPresentation } from '../stage/fragmentPresentation'
import type { Hypothesis, SceneFragment } from '../types/game'
import FragmentArtwork from './FragmentArtwork.vue'

const props = defineProps<{
  hypothesis: Hypothesis
  fragments: SceneFragment[]
  collectedIds: string[]
  selectedIds: string[]
  confirmed: boolean
  pending: boolean
  scanMode: boolean
}>()

const emit = defineEmits<{
  toggleEvidence: [evidenceId: string]
  confirm: []
  toggleScan: []
}>()

const snapshot = computed(() =>
  buildReasoningSnapshot(
    props.hypothesis,
    props.fragments,
    props.selectedIds,
    props.confirmed,
    props.collectedIds,
  ),
)

const presentationFor = (fragmentId: string) => getFragmentPresentation(fragmentId)
</script>

<template>
  <section
    class="reasoning-panel"
    :class="{ resolved: confirmed }"
    aria-labelledby="memory-question-title"
  >
    <header class="reasoning-header">
      <div>
        <span>MEMORY QUESTION / 本幕问题</span>
        <strong>{{ confirmed ? '推理完成' : snapshot.progressLabel }}</strong>
      </div>
      <h2 id="memory-question-title">{{ hypothesis.question }}</h2>
      <p v-if="confirmed">{{ hypothesis.resolution }}</p>
      <p v-else>取得证据并将它们并置，建立一条能够承担选择后果的解释。</p>
    </header>

    <div class="evidence-grid" aria-label="推理证据">
      <button
        v-for="evidence in snapshot.evidence"
        :key="evidence.id"
        class="evidence-card"
        :class="{
          available: evidence.available,
          selected: evidence.selected,
          unavailable: !evidence.available,
        }"
        type="button"
        :disabled="!evidence.available || confirmed || pending"
        :aria-pressed="evidence.selected"
        @click="emit('toggleEvidence', evidence.id)"
      >
        <FragmentArtwork
          v-if="presentationFor(evidence.id)"
          :presentation="presentationFor(evidence.id)!"
        />
        <span class="evidence-copy">
          <small>{{
            evidence.available ? (evidence.selected ? '已接入推理' : '可用证据') : '尚未取得'
          }}</small>
          <strong>{{ evidence.name }}</strong>
        </span>
      </button>
    </div>

    <blockquote v-if="snapshot.canConfirm || confirmed" class="hypothesis-statement">
      {{ hypothesis.statement }}
    </blockquote>

    <footer class="reasoning-actions">
      <button
        class="scan-action"
        type="button"
        :aria-pressed="scanMode"
        @click="emit('toggleScan')"
      >
        {{ scanMode ? '收束感知' : '扫描全景' }}
      </button>
      <button
        class="weave-action"
        type="button"
        :disabled="!snapshot.canConfirm || pending"
        @click="emit('confirm')"
      >
        <span>{{ confirmed ? '因果选择已开放' : pending ? '正在校验' : '编织假说' }}</span>
        <small>{{ confirmed ? 'DECISION UNLOCKED' : 'WEAVE HYPOTHESIS' }}</small>
      </button>
    </footer>
  </section>
</template>

<style scoped>
.reasoning-panel {
  width: min(26rem, 32vw);
  border: 1px solid rgba(215, 196, 162, 0.18);
  color: rgba(241, 229, 206, 0.92);
  background:
    linear-gradient(135deg, rgba(166, 109, 44, 0.08), transparent 42%), rgba(4, 5, 5, 0.84);
  box-shadow: 0 1.8rem 5rem rgba(0, 0, 0, 0.42);
  backdrop-filter: blur(18px);
}

.reasoning-panel.resolved {
  border-color: rgba(214, 173, 102, 0.42);
}

.reasoning-header {
  padding: 0.95rem 1.05rem 0.85rem;
  border-bottom: 1px solid rgba(215, 196, 162, 0.11);
}

.reasoning-header > div {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
}

.reasoning-header span,
.reasoning-header > div strong,
.evidence-copy small,
.weave-action small {
  color: rgba(214, 173, 102, 0.78);
  font:
    600 0.48rem/1.2 ui-monospace,
    monospace;
  letter-spacing: 0.16em;
}

.reasoning-header h2 {
  max-width: 23rem;
  margin: 0.75rem 0 0;
  font-size: clamp(1rem, 1.35vw, 1.28rem);
  font-weight: 500;
  line-height: 1.65;
  letter-spacing: 0.06em;
}

.reasoning-header p {
  margin: 0.5rem 0 0;
  color: rgba(215, 196, 162, 0.6);
  font-size: 0.68rem;
  line-height: 1.8;
  letter-spacing: 0.04em;
}

.evidence-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1px;
  padding: 1px;
  background: rgba(215, 196, 162, 0.12);
}

.evidence-card {
  position: relative;
  min-width: 0;
  padding: 0;
  overflow: hidden;
  border: 0;
  color: inherit;
  text-align: left;
  background: rgba(7, 8, 7, 0.96);
  cursor: pointer;
}

.evidence-card :deep(.fragment-artwork) {
  height: 4.15rem;
  margin: 0;
  overflow: hidden;
}

.evidence-card :deep(.fragment-artwork img) {
  width: 100%;
  height: 100%;
  object-fit: cover;
  filter: saturate(0.7) brightness(0.72);
  transition:
    filter 220ms ease,
    transform 460ms cubic-bezier(0.2, 0.72, 0.15, 1);
}

.evidence-card:hover:not(:disabled) :deep(.fragment-artwork img),
.evidence-card:focus-visible :deep(.fragment-artwork img),
.evidence-card.selected :deep(.fragment-artwork img) {
  filter: saturate(0.95) brightness(0.92);
  transform: scale(1.035);
}

.evidence-card.unavailable :deep(.fragment-artwork img) {
  filter: grayscale(1) brightness(0.28) blur(1px);
}

.evidence-card.selected {
  box-shadow: inset 0 0 0 1px rgba(214, 173, 102, 0.76);
}

.evidence-card:focus-visible {
  outline: 1px solid rgba(241, 229, 206, 0.86);
  outline-offset: -2px;
}

.evidence-card:disabled {
  cursor: default;
}

.evidence-copy {
  display: grid;
  min-height: 2.75rem;
  align-content: center;
  padding: 0.55rem 0.7rem 0.65rem;
}

.evidence-copy strong {
  margin-top: 0.28rem;
  overflow: hidden;
  font-size: 0.72rem;
  font-weight: 500;
  letter-spacing: 0.08em;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.evidence-card.unavailable .evidence-copy {
  opacity: 0.45;
}

.hypothesis-statement {
  margin: 0;
  padding: 0.72rem 1.05rem;
  border-left: 2px solid rgba(214, 173, 102, 0.62);
  color: rgba(241, 229, 206, 0.78);
  font-size: 0.72rem;
  line-height: 1.8;
  background: rgba(166, 109, 44, 0.08);
}

.reasoning-actions {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 1px;
  padding-top: 1px;
  background: rgba(215, 196, 162, 0.12);
}

.reasoning-actions button {
  min-height: 2.9rem;
  border: 0;
  color: rgba(241, 229, 206, 0.72);
  background: rgba(5, 6, 6, 0.96);
  cursor: pointer;
}

.reasoning-actions button:hover:not(:disabled),
.reasoning-actions button:focus-visible {
  color: #f1e5ce;
  background: rgba(31, 25, 18, 0.96);
}

.reasoning-actions button:focus-visible {
  outline: 1px solid rgba(241, 229, 206, 0.78);
  outline-offset: -2px;
}

.scan-action {
  padding: 0 0.9rem;
  font-size: 0.66rem;
  letter-spacing: 0.08em;
}

.weave-action {
  display: grid;
  align-content: center;
  justify-items: start;
  padding: 0 1rem;
}

.weave-action span {
  font-size: 0.76rem;
  letter-spacing: 0.1em;
}

.weave-action small {
  margin-top: 0.28rem;
  font-size: 0.42rem;
}

.weave-action:disabled {
  opacity: 0.36;
  cursor: not-allowed;
}

.reasoning-panel.resolved .weave-action {
  color: #f1e5ce;
  background: rgba(72, 48, 23, 0.86);
}

@media (max-width: 1100px) {
  .reasoning-panel {
    width: min(24rem, 38vw);
  }

  .reasoning-header {
    padding: 0.85rem 0.95rem 0.75rem;
  }

  .reasoning-header p,
  .hypothesis-statement {
    display: none;
  }

  .evidence-card :deep(.fragment-artwork) {
    height: 3.8rem;
  }
}

@media (max-width: 900px), (max-aspect-ratio: 1/1) {
  .reasoning-panel {
    width: min(25rem, calc(100vw - 2rem));
  }

  .reasoning-header h2 {
    margin-top: 0.48rem;
    font-size: 0.92rem;
    line-height: 1.5;
  }

  .evidence-grid {
    display: none;
  }

  .reasoning-actions {
    min-height: 2.7rem;
  }

  .reasoning-actions button {
    min-height: 2.7rem;
  }
}

@media (prefers-reduced-motion: reduce) {
  .evidence-card :deep(.fragment-artwork img) {
    transition: none;
  }
}
</style>
