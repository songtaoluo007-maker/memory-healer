<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'

const props = defineProps<{
  isSpeaking: boolean
  isPaused: boolean
  voiceVolume: number
  hasReplay: boolean
  isMuted: boolean
}>()

const emit = defineEmits<{
  pause: []
  resume: []
  replay: []
  skip: []
  toggleMute: []
  'update:voiceVolume': [volume: number]
  expandedChange: [expanded: boolean]
}>()

const narrowQuery = '(max-width: 900px), (max-aspect-ratio: 1/1)'
const isNarrow = ref(false)
const expanded = ref(false)
const panelVisible = computed(() => !isNarrow.value || expanded.value)
const hasActiveLine = computed(() => props.isSpeaking || props.isPaused)
const playbackState = computed(() => {
  if (props.isPaused) return '已暂停'
  if (props.isSpeaking) return '播放中'
  return props.hasReplay ? '待重播' : '无对白'
})

let mediaQuery: MediaQueryList | null = null

const syncNarrow = (event: MediaQueryListEvent | MediaQueryList) => {
  isNarrow.value = event.matches
  if (!event.matches && expanded.value) {
    expanded.value = false
    emit('expandedChange', false)
  }
}

const handlePrimaryAction = () => {
  if (!isNarrow.value) {
    emit('toggleMute')
    return
  }

  expanded.value = !expanded.value
  emit('expandedChange', expanded.value)
}

const togglePlayback = () => {
  if (props.isPaused) {
    emit('resume')
  } else {
    emit('pause')
  }
}

const updateVolume = (event: Event) => {
  emit('update:voiceVolume', Number((event.currentTarget as HTMLInputElement).value))
}

onMounted(() => {
  if (typeof window.matchMedia !== 'function') return
  mediaQuery = window.matchMedia(narrowQuery)
  syncNarrow(mediaQuery)
  mediaQuery.addEventListener('change', syncNarrow)
})

onUnmounted(() => {
  mediaQuery?.removeEventListener('change', syncNarrow)
})
</script>

<template>
  <div
    class="voice-controls"
    :class="{ paused: isPaused, speaking: isSpeaking, muted: isMuted }"
    :data-playback-state="playbackState"
  >
    <button
      class="voice-controls-trigger"
      type="button"
      :aria-label="
        isNarrow ? (panelVisible ? '收起语音控制' : '展开语音控制') : isMuted ? '取消静音' : '静音'
      "
      :aria-expanded="isNarrow ? panelVisible : undefined"
      :aria-controls="isNarrow ? 'voice-controls-panel' : undefined"
      @click="handlePrimaryAction"
    >
      {{ isMuted ? '静' : '声' }}
    </button>

    <div
      id="voice-controls-panel"
      class="voice-controls-panel"
      data-voice-controls-panel
      :hidden="!panelVisible"
      role="group"
      aria-label="对白播放控制"
    >
      <span class="voice-state" aria-live="polite">{{ playbackState }}</span>
      <button
        class="voice-control-action"
        :class="{ active: isPaused }"
        type="button"
        :aria-label="isPaused ? '继续对白' : '暂停对白'"
        :disabled="!hasActiveLine"
        @click="togglePlayback"
      >
        {{ isPaused ? '继续' : '暂停' }}
      </button>
      <button
        class="voice-control-action"
        type="button"
        aria-label="重播上一句"
        :disabled="!hasReplay"
        @click="emit('replay')"
      >
        重播
      </button>
      <button
        class="voice-control-action"
        type="button"
        aria-label="跳过当前对白"
        :disabled="!hasActiveLine"
        @click="emit('skip')"
      >
        跳过
      </button>
      <label class="voice-volume">
        <span>音量</span>
        <input
          type="range"
          min="0"
          max="1"
          step="0.05"
          :value="voiceVolume"
          aria-label="对白音量"
          @input="updateVolume"
        />
      </label>
      <button
        class="voice-control-action voice-mute-secondary"
        :class="{ active: isMuted }"
        type="button"
        :aria-label="isMuted ? '取消静音' : '静音'"
        @click="emit('toggleMute')"
      >
        {{ isMuted ? '取消静音' : '全局静音' }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.voice-controls {
  position: relative;
  display: flex;
  align-items: flex-start;
  gap: 0.4rem;
  color: var(--paper-100);
  font:
    600 0.6rem/1 ui-monospace,
    monospace;
}

.voice-controls-trigger,
.voice-control-action {
  min-height: 2.5rem;
  border: 1px solid rgba(215, 196, 162, 0.17);
  color: rgba(241, 229, 206, 0.72);
  background: rgba(5, 6, 6, 0.78);
  cursor: pointer;
  transition:
    color 180ms ease,
    border-color 180ms ease,
    background 180ms ease;
}

.voice-controls-trigger {
  width: 2.5rem;
  padding: 0;
}

.voice-controls-trigger:hover,
.voice-control-action:hover:not(:disabled),
.voice-control-action.active {
  border-color: rgba(214, 173, 102, 0.64);
  color: var(--paper-100);
  background: rgba(40, 29, 16, 0.88);
}

.voice-controls.paused .voice-controls-trigger,
.voice-controls.speaking .voice-controls-trigger {
  border-color: rgba(214, 173, 102, 0.64);
}

.voice-controls.muted .voice-controls-trigger {
  color: rgba(215, 196, 162, 0.42);
  border-style: dashed;
}

.voice-controls-panel {
  display: flex;
  min-height: 2.5rem;
  align-items: stretch;
  border: 1px solid rgba(215, 196, 162, 0.12);
  background: rgba(5, 6, 6, 0.82);
  backdrop-filter: blur(16px);
}

.voice-controls-panel[hidden] {
  display: none;
}

.voice-state {
  display: flex;
  min-width: 4rem;
  align-items: center;
  padding: 0 0.65rem;
  color: rgba(214, 173, 102, 0.72);
  letter-spacing: 0.08em;
  white-space: nowrap;
}

.voice-control-action {
  min-width: 3.1rem;
  padding: 0 0.55rem;
  border-width: 0 0 0 1px;
  background: transparent;
  letter-spacing: 0.08em;
}

.voice-control-action:disabled {
  color: rgba(215, 196, 162, 0.24);
  cursor: not-allowed;
}

.voice-volume {
  display: grid;
  grid-template-columns: auto 5.5rem;
  gap: 0.45rem;
  align-items: center;
  padding: 0 0.65rem;
  border-left: 1px solid rgba(215, 196, 162, 0.11);
  color: rgba(215, 196, 162, 0.55);
  letter-spacing: 0.08em;
}

.voice-volume input {
  width: 5.5rem;
  accent-color: var(--gold-300);
  cursor: pointer;
}

.voice-mute-secondary {
  display: none;
}

@media (max-width: 900px), (max-aspect-ratio: 1/1) {
  .voice-controls {
    position: static;
  }

  .voice-controls-trigger {
    width: 2.5rem;
    min-width: 2.5rem;
    min-height: 2.75rem;
  }

  .voice-controls-panel {
    position: fixed;
    z-index: 92;
    top: max(3.85rem, calc(env(safe-area-inset-top) + 3.35rem));
    right: 0.85rem;
    display: grid;
    grid-template-columns: 4rem repeat(4, minmax(2.75rem, auto));
    min-height: 2.75rem;
  }

  :global([data-stage-mode='dialogue']) .voice-controls-panel,
  :global([data-stage-mode='fragment']) .voice-controls-panel,
  :global(.ending) .voice-controls-panel {
    right: auto;
    left: 0.85rem;
  }

  .voice-state,
  .voice-control-action,
  .voice-volume {
    min-height: 2.75rem;
  }

  .voice-state {
    min-width: 0;
    padding: 0 0.5rem;
  }

  .voice-control-action {
    min-width: 2.75rem;
    padding: 0 0.45rem;
  }

  .voice-mute-secondary {
    display: block;
  }

  .voice-volume {
    grid-column: 1 / -1;
    grid-template-columns: auto minmax(8rem, 1fr);
    border-top: 1px solid rgba(215, 196, 162, 0.11);
    border-left: 0;
  }

  .voice-volume input {
    width: 100%;
    min-height: 2.75rem;
  }
}

@media (max-width: 760px) {
  .voice-controls-panel {
    right: auto;
    left: 0.75rem;
    width: 10.5rem;
    grid-template-columns: 1fr 1fr;
  }

  :global([data-stage-mode='dialogue']) .voice-controls-panel,
  :global([data-stage-mode='fragment']) .voice-controls-panel,
  :global(.ending) .voice-controls-panel {
    right: auto;
    left: 0.75rem;
  }

  .voice-state {
    grid-column: 1 / -1;
  }

  .voice-control-action {
    font-size: 0.56rem;
  }
}

@media (prefers-reduced-motion: reduce) {
  .voice-controls-trigger,
  .voice-control-action {
    transition: none;
  }
}
</style>
