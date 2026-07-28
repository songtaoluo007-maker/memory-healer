import type { Hypothesis, SceneFragment } from '../types/game'

export interface ReasoningEvidence {
  id: string
  name: string
  description: string
  memoryText: string
  available: boolean
  selected: boolean
}

export interface ReasoningSnapshot {
  evidence: ReasoningEvidence[]
  canConfirm: boolean
  confirmed: boolean
  progressLabel: string
}

export function toggleEvidenceSelection(
  selectedIds: readonly string[],
  evidenceId: string,
  allowedIds: readonly string[],
): string[] {
  if (!allowedIds.includes(evidenceId)) return [...selectedIds]
  if (selectedIds.includes(evidenceId)) {
    return selectedIds.filter((candidate) => candidate !== evidenceId)
  }
  return [...selectedIds, evidenceId]
}

export function buildReasoningSnapshot(
  hypothesis: Hypothesis,
  fragments: readonly SceneFragment[],
  selectedIds: readonly string[],
  confirmed: boolean,
  collectedIds?: readonly string[],
): ReasoningSnapshot {
  const fragmentById = new Map(fragments.map((fragment) => [fragment.id, fragment]))
  const authoritativeCollectedIds = new Set(
    collectedIds ??
      fragments.filter((fragment) => fragment.is_collected).map((fragment) => fragment.id),
  )
  const evidence = hypothesis.evidence_ids.map((evidenceId) => {
    const fragment = fragmentById.get(evidenceId)
    const available = authoritativeCollectedIds.has(evidenceId)
    return {
      id: evidenceId,
      name: fragment?.name ?? '未识别证据',
      description: fragment?.description ?? '这段记忆仍被遮蔽。',
      memoryText: fragment?.memory_text ?? '',
      available,
      selected: available && selectedIds.includes(evidenceId),
    }
  })
  const selectedCount = evidence.filter((item) => item.selected).length

  return {
    evidence,
    canConfirm: !confirmed && evidence.length > 0 && selectedCount === evidence.length,
    confirmed,
    progressLabel: `${String(selectedCount).padStart(2, '0')} / ${String(evidence.length).padStart(2, '0')}`,
  }
}

export function isSceneDecisionUnlocked(
  sceneId: string,
  hypotheses: readonly Hypothesis[],
  confirmedHypotheses: Readonly<Record<string, string>>,
): boolean {
  const hypothesis = hypotheses.find((candidate) => candidate.scene_id === sceneId)
  if (!hypothesis) return true
  return confirmedHypotheses[sceneId] === hypothesis.id
}
