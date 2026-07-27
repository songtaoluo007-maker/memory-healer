import { defineStore } from 'pinia'
import { ref } from 'vue'

export type CinematicOverlay = 'inventory' | 'memory' | 'butterfly' | 'story' | 'timeline'
export type StageMode = 'observe' | 'explore' | 'dialogue' | 'choice' | 'fragment'

export const useUiStore = defineStore('cinematic-ui', () => {
  const activeOverlay = ref<CinematicOverlay | null>(null)
  const stageMode = ref<StageMode>('observe')

  const openOverlay = (overlay: CinematicOverlay) => {
    activeOverlay.value = overlay
  }

  const closeOverlay = (overlay?: CinematicOverlay) => {
    if (!overlay || activeOverlay.value === overlay) {
      activeOverlay.value = null
    }
  }

  const setStageMode = (mode: StageMode) => {
    stageMode.value = mode
  }

  return {
    activeOverlay,
    stageMode,
    openOverlay,
    closeOverlay,
    setStageMode,
  }
})
