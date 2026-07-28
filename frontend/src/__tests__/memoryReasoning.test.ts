import { describe, expect, it } from 'vitest'
import {
  buildReasoningSnapshot,
  isSceneDecisionUnlocked,
  toggleEvidenceSelection,
} from '../domain/memoryReasoning'
import type { Hypothesis, SceneFragment } from '../types/game'

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
  is_revealed: false,
  is_collected: false,
}

describe('memory reasoning', () => {
  it('keeps only collected configured evidence selectable', () => {
    const snapshot = buildReasoningSnapshot(
      hypothesis,
      [knife, stage],
      ['fragment_grandpa_knife', 'fragment_shadow_puppet'],
      false,
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

  it('does not select evidence that is unavailable to the current hypothesis', () => {
    expect(
      toggleEvidenceSelection(
        ['fragment_grandpa_knife'],
        'fragment_three_kings',
        hypothesis.evidence_ids,
      ),
    ).toEqual(['fragment_grandpa_knife'])
  })

  it('unlocks the scene decision only after the configured hypothesis is confirmed', () => {
    expect(isSceneDecisionUnlocked('scene_1972', [hypothesis], {})).toBe(false)
    expect(
      isSceneDecisionUnlocked('scene_1972', [hypothesis], {
        scene_1972: 'hypothesis_1972_legacy',
      }),
    ).toBe(true)
    expect(isSceneDecisionUnlocked('scene_1990', [], {})).toBe(true)
  })
})
