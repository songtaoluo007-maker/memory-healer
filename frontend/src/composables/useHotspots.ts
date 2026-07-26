import { computed, ref, watch, type ComputedRef } from 'vue'
import type { Hotspot, SceneView } from '../types/game'

export type { Hotspot } from '../types/game'

export function useHotspots(sceneView: ComputedRef<SceneView | null>) {
  const exploredIds = ref<Set<string>>(new Set())
  const activeHotspot = ref<Hotspot | null>(null)

  const hotspots = computed(() => sceneView.value?.hotspots ?? [])
  const unexploredHotspots = computed(() =>
    hotspots.value.filter((hotspot) => !exploredIds.value.has(hotspot.id)),
  )

  const markExplored = (hotspotId: string): Hotspot | null => {
    const hotspot = hotspots.value.find((candidate) => candidate.id === hotspotId)
    if (!hotspot) return null
    exploredIds.value.add(hotspotId)
    activeHotspot.value = hotspot
    return hotspot
  }

  const isExplored = (hotspotId: string) => exploredIds.value.has(hotspotId)

  const explorationProgress = computed(() => {
    if (hotspots.value.length === 0) return 100
    const exploredInScene = hotspots.value.filter((hotspot) =>
      exploredIds.value.has(hotspot.id),
    ).length
    return Math.round((exploredInScene / hotspots.value.length) * 100)
  })

  watch(
    () => sceneView.value?.scene.id,
    () => {
      activeHotspot.value = null
    },
  )

  return {
    hotspots,
    unexploredHotspots,
    activeHotspot,
    exploredIds,
    markExplored,
    isExplored,
    explorationProgress,
  }
}
