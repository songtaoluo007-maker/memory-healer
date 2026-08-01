import type { AppliedConsequence } from '../types/game'

const presentationSceneByVariant: ReadonlyMap<string, string> = new Map([
  ['legacy_carried', 'scene_1990'],
  ['legacy_suppressed', 'scene_1990'],
])

export const resolvePresentableConsequence = (
  sceneId: string | null | undefined,
  ...candidates: readonly (AppliedConsequence | null | undefined)[]
): AppliedConsequence | null => {
  if (!sceneId) return null
  return (
    candidates.find(
      (candidate) =>
        candidate?.target_scene_id === sceneId &&
        presentationSceneByVariant.get(candidate.variant) === sceneId,
    ) ?? null
  )
}
