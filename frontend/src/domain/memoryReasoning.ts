import { computed, ref, watch, type Ref } from 'vue'
import type {
  Choice,
  GameState,
  Hypothesis,
  PresentationEvent,
  SceneFragment,
  SceneView,
} from '../types/game'

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

export interface HypothesisSubmission {
  status: 'confirmed' | 'rejected' | 'unchanged'
  feedback: string | null
}

type ChoiceRequirementState = Pick<
  GameState,
  'confirmed_hypotheses' | 'collected_fragments' | 'npc_trust'
>

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

export function toggleReasoningEvidenceSelection(
  selectedIds: readonly string[],
  evidenceId: string,
  activeHypothesis: Hypothesis | null,
  collectedIds: readonly string[],
  confirmed: boolean,
): string[] {
  if (confirmed || !activeHypothesis || !collectedIds.includes(evidenceId)) {
    return [...selectedIds]
  }
  return toggleEvidenceSelection(selectedIds, evidenceId, activeHypothesis.evidence_ids)
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
  choices: readonly Choice[],
  state: ChoiceRequirementState,
): boolean {
  const sceneChoices = choices.filter((choice) => choice.scene_id === sceneId)
  if (sceneChoices.length === 0) return true
  return sceneChoices.some((choice) => isChoiceUnlocked(choice, state))
}

export function isChoiceUnlocked(choice: Choice, state: ChoiceRequirementState): boolean {
  return choice.requirements.every((requirement) => {
    switch (requirement.kind) {
      case 'hypothesis_confirmed':
        return state.confirmed_hypotheses?.[choice.scene_id] === requirement.hypothesis_id
      case 'fragment_collected':
        return state.collected_fragments.includes(requirement.fragment_id)
      case 'npc_trust_at_least':
        return (state.npc_trust[requirement.npc_id] ?? 0) >= requirement.minimum
    }
  })
}

export function resolveHypothesisSubmission(
  events: readonly PresentationEvent[],
  hypothesisId: string,
): HypothesisSubmission {
  const event = events.find(
    (candidate) =>
      candidate.content_id === hypothesisId &&
      (candidate.type === 'hypothesis.confirmed' || candidate.type === 'hypothesis.rejected'),
  )
  if (event?.type === 'hypothesis.confirmed') {
    return { status: 'confirmed', feedback: null }
  }
  if (event?.type === 'hypothesis.rejected') {
    return {
      status: 'rejected',
      feedback: typeof event.payload.feedback === 'string' ? event.payload.feedback : null,
    }
  }
  return { status: 'unchanged', feedback: null }
}

export function useMemoryReasoningSelection(sceneView: Readonly<Ref<SceneView | null>>) {
  const selectedHypothesisId = ref<string | null>(null)
  const selectedEvidenceIds = ref<string[]>([])
  const rejectedFeedback = ref<string | null>(null)
  const currentSceneHypotheses = computed(() => {
    const view = sceneView.value
    if (!view) return []
    return (view.hypotheses ?? []).filter((candidate) => candidate.scene_id === view.scene.id)
  })
  const activeHypothesis = computed(
    () =>
      currentSceneHypotheses.value.find(
        (candidate) => candidate.id === selectedHypothesisId.value,
      ) ?? null,
  )

  const resetForCurrentScene = () => {
    selectedHypothesisId.value = currentSceneHypotheses.value[0]?.id ?? null
    selectedEvidenceIds.value = []
    rejectedFeedback.value = null
  }

  watch(
    sceneView,
    (nextView, previousView) => {
      if (!nextView || nextView.scene.id !== previousView?.scene.id) {
        resetForCurrentScene()
        return
      }
      const selected = currentSceneHypotheses.value.find(
        (candidate) => candidate.id === selectedHypothesisId.value,
      )
      if (!selected) {
        resetForCurrentScene()
        return
      }
      selectedEvidenceIds.value = selectedEvidenceIds.value.filter((evidenceId) =>
        selected.evidence_ids.includes(evidenceId),
      )
    },
    { flush: 'sync', immediate: true },
  )

  const selectHypothesis = (hypothesisId: string) => {
    const candidate = currentSceneHypotheses.value.find((item) => item.id === hypothesisId)
    if (!candidate) return
    selectedHypothesisId.value = candidate.id
    selectedEvidenceIds.value = selectedEvidenceIds.value.filter((evidenceId) =>
      candidate.evidence_ids.includes(evidenceId),
    )
    rejectedFeedback.value = null
  }

  const toggleEvidence = (
    evidenceId: string,
    collectedIds: readonly string[],
    confirmed: boolean,
  ) => {
    selectedEvidenceIds.value = toggleReasoningEvidenceSelection(
      selectedEvidenceIds.value,
      evidenceId,
      activeHypothesis.value,
      collectedIds,
      confirmed,
    )
  }

  return {
    currentSceneHypotheses,
    activeHypothesis,
    selectedHypothesisId,
    selectedEvidenceIds,
    rejectedFeedback,
    selectHypothesis,
    toggleEvidence,
  }
}
