import { describe, expect, it } from 'vitest'
import {
  buildReasoningSnapshot,
  isSceneDecisionUnlocked,
  resolveHypothesisSubmission,
  toggleEvidenceSelection,
  toggleReasoningEvidenceSelection,
} from '../domain/memoryReasoning'
import type { Choice, GameState, Hypothesis, PresentationEvent, SceneFragment } from '../types/game'

const hypothesis: Hypothesis = {
  id: 'hypothesis_1972_legacy',
  scene_id: 'scene_1972',
  question: '陈守义为什么仍想把皮影传下去？',
  statement: '刻刀与戏幕共同指向一段仍能被讲述的生活。',
  evidence_ids: ['fragment_grandpa_knife', 'fragment_shadow_puppet'],
  resolution: '两条记忆互相印证。',
}

const knife: SceneFragment = {
  id: 'fragment_grandpa_knife',
  name: '爷爷的刻刀',
  scene: 'scene_1972',
  description: '磨损的刻刀。',
  unlock_method: 'explore',
  unlock_hint: '检查工具箱',
  memory_text: '刻刀从不离身。',
  unlock_npc_id: null,
  minimum_trust: null,
  dialogue_prompt: null,
  dialogue_trust_reward: 0,
  is_revealed: true,
  is_collected: true,
}

const stage: SceneFragment = {
  id: 'fragment_shadow_puppet',
  name: '皮影戏台',
  scene: 'scene_1972',
  description: '仍有余温的戏幕。',
  unlock_method: 'dialogue',
  unlock_hint: '询问陈守义',
  memory_text: '戏台仍在发光。',
  unlock_npc_id: 'chen_shouyi_young',
  minimum_trust: 30,
  dialogue_prompt: null,
  dialogue_trust_reward: 0,
  is_revealed: false,
  is_collected: false,
}

const makeChoice = (requirements: Choice['requirements']): Choice => ({
  id: 'talk_to_stranger',
  scene_id: 'scene_1990',
  label: '打开木箱',
  target_scene: 'scene_2024',
  is_key: true,
  effects: {
    trust_changes: {},
    reveal_fragments: [],
    current_mood: null,
  },
  requirements,
})

const makeRequirementState = (
  overrides: Partial<
    Pick<GameState, 'confirmed_hypotheses' | 'collected_fragments' | 'npc_trust'>
  > = {},
) => ({
  confirmed_hypotheses: {},
  collected_fragments: [],
  npc_trust: {},
  ...overrides,
})

describe('memory reasoning', () => {
  it('keeps only collected configured evidence selectable', () => {
    const snapshot = buildReasoningSnapshot(
      hypothesis,
      [{ ...knife, is_collected: false }, stage],
      ['fragment_grandpa_knife', 'fragment_shadow_puppet'],
      false,
      ['fragment_grandpa_knife'],
    )

    expect(snapshot.evidence.map((item) => [item.id, item.available, item.selected])).toEqual([
      ['fragment_grandpa_knife', true, true],
      ['fragment_shadow_puppet', false, false],
    ])
    expect(snapshot.canConfirm).toBe(false)
    expect(snapshot.progressLabel).toBe('01 / 02')
  })

  it('allows confirmation only when every required evidence item is selected', () => {
    const snapshot = buildReasoningSnapshot(
      hypothesis,
      [knife, { ...stage, is_revealed: true, is_collected: true }],
      ['fragment_grandpa_knife', 'fragment_shadow_puppet'],
      false,
    )

    expect(snapshot.canConfirm).toBe(true)
    expect(snapshot.progressLabel).toBe('02 / 02')
  })

  it('builds a 1990 candidate only from its canonical evidence and ignores 1972 selection', () => {
    const modernStory: Hypothesis = {
      id: 'hypothesis_1990_modern_story',
      scene_id: 'scene_1990',
      question: '陈守义为什么带着整箱皮影来到深圳？',
      statement: '他在为皮影寻找新讲法。',
      evidence_ids: ['puppet_trunk_fragment', 'station_clock_fragment'],
      resolution: '他带着皮影走进了新生活。',
    }
    const fragments = [
      {
        ...knife,
        id: 'train_ticket_fragment',
        name: '南下的车票',
        scene: 'scene_1990',
      },
      {
        ...knife,
        id: 'farewell_letter_fragment',
        name: '给师父的信',
        scene: 'scene_1990',
      },
      {
        ...knife,
        id: 'puppet_trunk_fragment',
        name: '皮影道具箱',
        scene: 'scene_1990',
      },
      {
        ...knife,
        id: 'station_clock_fragment',
        name: '站台的时钟',
        scene: 'scene_1990',
      },
    ]

    const snapshot = buildReasoningSnapshot(
      modernStory,
      fragments,
      ['fragment_grandpa_knife', 'train_ticket_fragment', 'puppet_trunk_fragment'],
      false,
      ['train_ticket_fragment', 'puppet_trunk_fragment'],
    )

    expect(snapshot.evidence.map((item) => [item.id, item.available, item.selected])).toEqual([
      ['puppet_trunk_fragment', true, true],
      ['station_clock_fragment', false, false],
    ])
    expect(snapshot.progressLabel).toBe('01 / 02')
  })

  it('does not select evidence that is unavailable to the current hypothesis', () => {
    expect(
      toggleEvidenceSelection(
        ['fragment_grandpa_knife'],
        'fragment_three_kings',
        hypothesis.evidence_ids,
      ),
    ).toEqual(['fragment_grandpa_knife'])
  })

  it('toggles evidence from authoritative collected IDs instead of a stale scene snapshot', () => {
    const modernStory: Hypothesis = {
      id: 'hypothesis_1990_modern_story',
      scene_id: 'scene_1990',
      question: '陈守义为什么带着整箱皮影来到深圳？',
      statement: '他在为皮影寻找新讲法。',
      evidence_ids: ['puppet_trunk_fragment', 'station_clock_fragment'],
      resolution: '他带着皮影走进了新生活。',
    }

    expect(
      toggleReasoningEvidenceSelection(
        [],
        'puppet_trunk_fragment',
        modernStory,
        ['puppet_trunk_fragment'],
        false,
      ),
    ).toEqual(['puppet_trunk_fragment'])
    expect(
      toggleReasoningEvidenceSelection([], 'station_clock_fragment', modernStory, [], false),
    ).toEqual([])
  })

  it('unlocks choices only when their discriminated requirements are satisfied', () => {
    const choice = makeChoice([
      {
        kind: 'hypothesis_confirmed',
        hypothesis_id: 'hypothesis_1990_modern_story',
      },
      { kind: 'fragment_collected', fragment_id: 'station_clock_fragment' },
      { kind: 'npc_trust_at_least', npc_id: 'chen_shouyi_1990', minimum: 35 },
    ])

    expect(
      isSceneDecisionUnlocked(
        'scene_1990',
        [choice],
        makeRequirementState({
          confirmed_hypotheses: { scene_1990: 'hypothesis_1990_survival' },
          collected_fragments: ['station_clock_fragment'],
          npc_trust: { chen_shouyi_1990: 35 },
        }),
      ),
    ).toBe(false)
    expect(
      isSceneDecisionUnlocked(
        'scene_1990',
        [choice],
        makeRequirementState({
          confirmed_hypotheses: { scene_1990: 'hypothesis_1990_modern_story' },
          collected_fragments: ['station_clock_fragment'],
          npc_trust: { chen_shouyi_1990: 35 },
        }),
      ),
    ).toBe(true)
  })

  it('does not infer choice locking from hypothesis order or scene hypotheses', () => {
    expect(isSceneDecisionUnlocked('scene_1990', [makeChoice([])], makeRequirementState())).toBe(
      true,
    )
    expect(
      isSceneDecisionUnlocked(
        'scene_1990',
        [
          makeChoice([
            {
              kind: 'hypothesis_confirmed',
              hypothesis_id: 'hypothesis_1990_modern_story',
            },
          ]),
        ],
        makeRequirementState({
          confirmed_hypotheses: { scene_1990: 'hypothesis_1990_survival' },
        }),
      ),
    ).toBe(false)
  })

  it('reads rejected feedback only from the matching authoritative event', () => {
    const events: PresentationEvent[] = [
      {
        type: 'hypothesis.rejected',
        content_id: 'hypothesis_1990_survival',
        payload: { feedback: '这些犹豫还不能证明他抛下了皮影。' },
      },
    ]

    expect(resolveHypothesisSubmission(events, 'hypothesis_1990_survival')).toEqual({
      status: 'rejected',
      feedback: '这些犹豫还不能证明他抛下了皮影。',
    })
    expect(resolveHypothesisSubmission(events, 'hypothesis_1990_modern_story')).toEqual({
      status: 'unchanged',
      feedback: null,
    })
  })

  it('recognizes confirmation only from the matching authoritative event', () => {
    const events: PresentationEvent[] = [
      {
        type: 'hypothesis.confirmed',
        content_id: 'hypothesis_1990_modern_story',
        payload: { evidence_ids: ['puppet_trunk_fragment', 'station_clock_fragment'] },
      },
    ]

    expect(resolveHypothesisSubmission(events, 'hypothesis_1990_modern_story')).toEqual({
      status: 'confirmed',
      feedback: null,
    })
    expect(resolveHypothesisSubmission(events, 'hypothesis_1990_survival')).toEqual({
      status: 'unchanged',
      feedback: null,
    })
  })
})
