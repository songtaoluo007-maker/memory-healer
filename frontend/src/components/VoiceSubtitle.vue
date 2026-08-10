<script setup lang="ts">
import type { VoiceCue } from '../types/game'

defineProps<{
  cue: VoiceCue | null
}>()
</script>

<template>
  <div v-if="cue" class="voice-subtitle" data-voice-subtitle role="status" aria-live="polite">
    {{ cue.text }}
  </div>
</template>

<style scoped>
.voice-subtitle {
  position: fixed;
  z-index: 72;
  bottom: max(1.25rem, calc(env(safe-area-inset-bottom) + 0.75rem));
  left: 50%;
  width: min(38rem, calc(100vw - 24rem));
  padding: 0.55rem 1rem 0.65rem;
  border-top: 1px solid rgba(214, 173, 102, 0.48);
  color: rgba(248, 239, 220, 0.96);
  font-size: clamp(0.78rem, 1.05vw, 0.94rem);
  line-height: 1.75;
  letter-spacing: 0.08em;
  text-align: center;
  text-shadow: 0 2px 10px #000;
  background: linear-gradient(90deg, transparent, rgba(3, 4, 3, 0.78) 18% 82%, transparent);
  transform: translateX(-50%);
  pointer-events: none;
}

@media (max-width: 900px), (max-aspect-ratio: 1/1) {
  .voice-subtitle {
    bottom: calc(max(7.2rem, env(safe-area-inset-bottom) + 6.7rem));
    width: min(30rem, calc(100vw - 2rem));
    padding-right: 0.6rem;
    padding-left: 0.6rem;
  }
}
</style>
