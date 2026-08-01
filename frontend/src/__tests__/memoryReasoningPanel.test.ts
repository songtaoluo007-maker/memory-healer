import { afterEach, describe, expect, it } from 'vitest'
import { createApp, defineComponent, h, nextTick, ref } from 'vue'
import MemoryReasoningPanel from '../components/MemoryReasoningPanel.vue'
import type { Hypothesis, SceneFragment } from '../types/game'

const hypotheses: Hypothesis[] = [
  {
    id: 'hypothesis_1990_survival',
    scene_id: 'scene_1990',
    question: '陈守义南下是否意味着他准备抛下皮影？',
    statement: '生存压力和愧疚迫使他离开。',
    evidence_ids: ['train_ticket_fragment', 'farewell_letter_fragment'],
    resolution: '这些犹豫还不能证明他抛下了皮影。',
  },
  {
    id: 'hypothesis_1990_modern_story',
    scene_id: 'scene_1990',
    question: '陈守义为什么带着整箱皮影来到深圳？',
    statement: '现代皮影与3:47的决定互相印证。',
    evidence_ids: ['puppet_trunk_fragment', 'station_clock_fragment'],
    resolution: '他在为皮影寻找新讲法。',
  },
]

const fragment = (id: string, name: string): SceneFragment => ({
  id,
  name,
  scene: id.startsWith('fragment_') ? 'scene_1972' : 'scene_1990',
  description: `${name}的细节。`,
  unlock_method: 'explore',
  unlock_hint: '继续观察',
  memory_text: `${name}的记忆。`,
  unlock_npc_id: null,
  minimum_trust: null,
  dialogue_prompt: null,
  dialogue_trust_reward: 0,
  is_revealed: true,
  is_collected: true,
})

const fragments = [
  fragment('train_ticket_fragment', '南下的车票'),
  fragment('farewell_letter_fragment', '给师父的信'),
  fragment('puppet_trunk_fragment', '皮影道具箱'),
  fragment('station_clock_fragment', '站台的时钟'),
]

let app: ReturnType<typeof createApp> | null = null
let host: HTMLDivElement | null = null

afterEach(() => {
  app?.unmount()
  host?.remove()
  app = null
  host = null
})

const mountPanel = (
  options: {
    candidates?: Hypothesis[]
    selectedId?: string
    selectedEvidence?: string[]
    rejectedFeedback?: string | null
  } = {},
) => {
  const candidates = options.candidates ?? hypotheses
  const selectedHypothesisId = ref(options.selectedId ?? candidates[0]?.id ?? '')
  const selectedIds = ref(options.selectedEvidence ?? [])
  const rejectedFeedback = ref(options.rejectedFeedback ?? null)

  app = createApp(
    defineComponent({
      setup() {
        const selectHypothesis = (hypothesisId: string) => {
          const candidate = candidates.find((item) => item.id === hypothesisId)
          if (!candidate) return
          selectedHypothesisId.value = candidate.id
          selectedIds.value = selectedIds.value.filter((id) => candidate.evidence_ids.includes(id))
          rejectedFeedback.value = null
        }

        return () =>
          h(MemoryReasoningPanel, {
            hypotheses: candidates,
            selectedHypothesisId: selectedHypothesisId.value,
            fragments,
            collectedIds: fragments.map((item) => item.id),
            selectedIds: selectedIds.value,
            confirmed: false,
            pending: false,
            scanMode: false,
            rejectedFeedback: rejectedFeedback.value,
            onSelectHypothesis: selectHypothesis,
            onToggleEvidence: (evidenceId: string) => {
              selectedIds.value = selectedIds.value.includes(evidenceId)
                ? selectedIds.value.filter((id) => id !== evidenceId)
                : [...selectedIds.value, evidenceId]
            },
          })
      },
    }),
  )
  host = document.createElement('div')
  document.body.append(host)
  app.mount(host)

  return { host, selectedHypothesisId, selectedIds }
}

describe('MemoryReasoningPanel', () => {
  it('renders both 1990 candidates and announces the active question', () => {
    const mounted = mountPanel()

    const candidateButtons =
      mounted.host.querySelectorAll<HTMLButtonElement>('[data-hypothesis-id]')
    expect([...candidateButtons].map((button) => button.dataset.hypothesisId)).toEqual([
      'hypothesis_1990_survival',
      'hypothesis_1990_modern_story',
    ])
    expect(mounted.host.querySelector('[aria-live="polite"]')?.textContent).toContain(
      '陈守义南下是否意味着他准备抛下皮影？',
    )
  })

  it('switches interpretation and drops evidence incompatible with the next candidate', async () => {
    const mounted = mountPanel({ selectedEvidence: ['train_ticket_fragment'] })
    const modernStoryButton = mounted.host.querySelector<HTMLButtonElement>(
      '[data-hypothesis-id="hypothesis_1990_modern_story"]',
    )

    modernStoryButton?.click()
    await nextTick()

    expect(mounted.selectedHypothesisId.value).toBe('hypothesis_1990_modern_story')
    expect(mounted.selectedIds.value).toEqual([])
    expect(mounted.host.textContent).toContain('皮影道具箱')
    expect(mounted.host.textContent).not.toContain('南下的车票')
  })

  it('shows authoritative rejected feedback without presenting the decision as unlocked', () => {
    const feedback = '这些犹豫还不能证明他抛下了皮影。'
    const mounted = mountPanel({
      selectedEvidence: ['train_ticket_fragment', 'farewell_letter_fragment'],
      rejectedFeedback: feedback,
    })

    expect(mounted.host.querySelector('[data-rejected-feedback]')?.textContent ?? '').toContain(
      feedback,
    )
    expect(mounted.host.textContent).not.toContain('DECISION UNLOCKED')
  })

  it('keeps the one-candidate 1972 evidence flow unchanged', () => {
    const legacy = {
      id: 'hypothesis_1972_legacy',
      scene_id: 'scene_1972',
      question: '陈守义为什么仍想把皮影传下去？',
      statement: '刻刀与戏幕共同指向传承。',
      evidence_ids: ['fragment_grandpa_knife', 'fragment_shadow_puppet'],
      resolution: '两条记忆互相印证。',
    }
    const mounted = mountPanel({ candidates: [legacy], selectedId: legacy.id })

    expect(mounted.host.querySelector('[role="tablist"]')).toBeNull()
    expect(mounted.host.textContent).toContain(legacy.question)
    expect(mounted.host.querySelectorAll('.evidence-card')).toHaveLength(2)
  })
})
