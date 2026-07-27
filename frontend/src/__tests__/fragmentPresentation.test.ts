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

  it('returns null for a fragment without bespoke art', () => {
    expect(getFragmentPresentation('fragment_grandpa_knife')).toBeNull()
  })
})
