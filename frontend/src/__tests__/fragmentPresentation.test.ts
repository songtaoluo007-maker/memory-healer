import { describe, expect, it } from 'vitest'
import { getFragmentPresentation } from '../stage/fragmentPresentation'

describe('fragment presentation registry', () => {
  it('registers the 1990 train-ticket insert', () => {
    const fragment = getFragmentPresentation('train_ticket_fragment')

    expect(fragment).not.toBeNull()
    if (fragment) {
      expect(fragment.image).toContain('fragment-1990-train-ticket')
      expect(fragment.alt).toContain('车票')
    }
  })

  it('registers the 2024 Xiaoyu letter insert', () => {
    const fragment = getFragmentPresentation('fragment_letter')

    expect(fragment).not.toBeNull()
    if (fragment) {
      expect(fragment.image).toContain('fragment-2024-xiaoyu-letter')
      expect(fragment.alt).toContain('小雨来信')
    }
  })

  it('registers the 2050 award-trophy insert', () => {
    const fragment = getFragmentPresentation('award_trophy_fragment')

    expect(fragment).not.toBeNull()
    if (fragment) {
      expect(fragment.image).toContain('fragment-2050-award-trophy')
      expect(fragment.alt).toContain('水晶奖杯')
    }
  })

  it('registers the 2089 final-puppet insert', () => {
    const fragment = getFragmentPresentation('fragment_last_puppet')

    expect(fragment).not.toBeNull()
    if (fragment) {
      expect(fragment.image).toContain('fragment-2089-last-puppet')
      expect(fragment.alt).toContain('孙悟空皮影')
    }
  })

  it('registers exactly the four approved representative inserts', () => {
    const ids = [
      'train_ticket_fragment',
      'fragment_letter',
      'award_trophy_fragment',
      'fragment_last_puppet',
    ]

    expect(ids.every((id) => getFragmentPresentation(id) !== null)).toBe(true)
  })

  it('returns null for a fragment without bespoke art', () => {
    expect(getFragmentPresentation('fragment_grandpa_knife')).toBeNull()
  })
})
