<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from '../composables/useI18n'
import type { Hotspot } from '../types/game'

const { t } = useI18n()

const props = withDefaults(
  defineProps<{
    hotspots: Hotspot[]
    exploredIds: Set<string>
    sceneId: string
    scanMode?: boolean
  }>(),
  {
    scanMode: false,
  },
)

const emit = defineEmits<{
  explore: [hotspot: Hotspot]
}>()

const hoveredId = ref<string | null>(null)

const interactionLabel = (interaction: Hotspot['interaction']) =>
  ({
    inspect: '观察异样',
    collect: '拾取线索',
    talk: '询问此物',
  })[interaction]

const handleClick = (hotspot: Hotspot) => {
  if (!props.exploredIds.has(hotspot.id)) {
    emit('explore', hotspot)
  }
}

const horizontalClass = (hotspot: Hotspot) => {
  if (hotspot.x >= 0.68) return 'align-right'
  if (hotspot.x <= 0.28) return 'align-left'
  return 'align-center'
}
</script>

<template>
  <div
    class="hotspot-overlay"
    :class="{ 'scan-active': scanMode }"
    role="group"
    :aria-label="t('a11y.hotspot')"
    :data-scene-id="sceneId"
  >
    <button
      v-for="hotspot in hotspots"
      :key="hotspot.id"
      class="perception-cue"
      :class="[
        horizontalClass(hotspot),
        {
          explored: exploredIds.has(hotspot.id),
          active: hoveredId === hotspot.id,
          scanning: scanMode,
        },
      ]"
      :style="{ left: `${hotspot.x * 100}%`, top: `${hotspot.y * 100}%` }"
      type="button"
      :disabled="exploredIds.has(hotspot.id)"
      :aria-label="`${interactionLabel(hotspot.interaction)}：${hotspot.label}`"
      @click="handleClick(hotspot)"
      @mouseenter="hoveredId = hotspot.id"
      @mouseleave="hoveredId = null"
      @focus="hoveredId = hotspot.id"
      @blur="hoveredId = null"
    >
      <span class="cue-frame" aria-hidden="true"><i /></span>
      <span class="cue-copy">
        <small>{{ interactionLabel(hotspot.interaction) }}</small>
        <strong>{{ hotspot.label }}</strong>
      </span>
    </button>
  </div>
</template>

<style scoped>
.hotspot-overlay {
  position: absolute;
  z-index: 10;
  inset: 0;
  pointer-events: none;
}

.perception-cue {
  position: absolute;
  display: grid;
  width: 4.5rem;
  height: 4.5rem;
  place-items: center;
  padding: 0;
  border: 0;
  color: #f1e5ce;
  background: transparent;
  transform: translate(-50%, -50%);
  pointer-events: auto;
  cursor: pointer;
}

.cue-frame {
  position: relative;
  display: block;
  width: 1.7rem;
  height: 1.7rem;
  border-top: 1px solid rgba(214, 173, 102, 0.76);
  border-left: 1px solid rgba(214, 173, 102, 0.76);
  opacity: 0.58;
  filter: drop-shadow(0 0 0.45rem rgba(214, 173, 102, 0.24));
  transition:
    width 240ms ease,
    height 240ms ease,
    opacity 180ms ease,
    border-color 180ms ease,
    transform 320ms cubic-bezier(0.2, 0.72, 0.15, 1);
}

.cue-frame::after {
  position: absolute;
  right: 0;
  bottom: 0;
  width: 0.65rem;
  height: 0.65rem;
  border-right: 1px solid rgba(214, 173, 102, 0.48);
  border-bottom: 1px solid rgba(214, 173, 102, 0.48);
  content: '';
}

.cue-frame i {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 0.25rem;
  height: 1px;
  background: rgba(241, 229, 206, 0.78);
  transform: translate(-50%, -50%);
  transition: width 180ms ease;
}

.cue-copy {
  position: absolute;
  top: calc(50% + 1.35rem);
  display: grid;
  min-width: max-content;
  padding: 0.42rem 0.58rem 0.48rem;
  border-top: 1px solid rgba(214, 173, 102, 0.5);
  color: rgba(241, 229, 206, 0.92);
  text-align: left;
  background: rgba(5, 6, 6, 0.76);
  box-shadow: 0 0.8rem 2rem rgba(0, 0, 0, 0.34);
  opacity: 0;
  transform: translateY(0.35rem);
  backdrop-filter: blur(10px);
  pointer-events: none;
  transition:
    opacity 180ms ease,
    transform 260ms cubic-bezier(0.2, 0.72, 0.15, 1);
}

.align-left .cue-copy {
  left: 50%;
}

.align-center .cue-copy {
  left: 50%;
  transform: translate(-50%, 0.35rem);
}

.align-right .cue-copy {
  right: 50%;
}

.cue-copy small {
  color: rgba(214, 173, 102, 0.72);
  font:
    600 0.46rem/1.2 ui-monospace,
    monospace;
  letter-spacing: 0.18em;
}

.cue-copy strong {
  margin-top: 0.24rem;
  font-size: 0.7rem;
  font-weight: 500;
  letter-spacing: 0.1em;
}

.perception-cue:hover .cue-frame,
.perception-cue:focus-visible .cue-frame,
.perception-cue.active .cue-frame,
.perception-cue.scanning .cue-frame {
  width: 2.2rem;
  height: 2.2rem;
  border-color: rgba(241, 229, 206, 0.94);
  opacity: 1;
  transform: scale(1.02);
}

.perception-cue:hover .cue-frame i,
.perception-cue:focus-visible .cue-frame i,
.perception-cue.active .cue-frame i,
.perception-cue.scanning .cue-frame i {
  width: 0.7rem;
}

.perception-cue:hover .cue-copy,
.perception-cue:focus-visible .cue-copy,
.perception-cue.active .cue-copy,
.perception-cue.scanning .cue-copy {
  opacity: 1;
  transform: translateY(0);
}

.perception-cue.align-center:hover .cue-copy,
.perception-cue.align-center:focus-visible .cue-copy,
.perception-cue.align-center.active .cue-copy,
.perception-cue.align-center.scanning .cue-copy {
  transform: translate(-50%, 0);
}

.perception-cue:focus-visible {
  outline: 1px solid rgba(241, 229, 206, 0.72);
  outline-offset: 0.1rem;
}

.perception-cue.explored {
  cursor: default;
}

.perception-cue.explored .cue-frame {
  width: 1rem;
  height: 0.6rem;
  border-top-color: transparent;
  border-left-color: rgba(215, 196, 162, 0.24);
  opacity: 0.45;
  filter: none;
}

.perception-cue.explored .cue-frame::after {
  width: 0.55rem;
  height: 0;
  border-right: 0;
  border-bottom-color: rgba(215, 196, 162, 0.28);
}

.perception-cue.explored .cue-frame i,
.perception-cue.explored .cue-copy {
  display: none;
}

@media (max-width: 680px) {
  .perception-cue {
    width: 3.75rem;
    height: 3.75rem;
  }

  .cue-copy {
    max-width: 9rem;
    min-width: 7rem;
    white-space: normal;
  }
}

@media (prefers-reduced-motion: reduce) {
  .cue-frame,
  .cue-frame i,
  .cue-copy {
    transition: none;
  }
}
</style>
