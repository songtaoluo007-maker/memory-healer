import { describe, expect, it } from 'vitest'
import { FRAGMENT_PRESENTATION_IDS, getFragmentPresentation } from '../stage/fragmentPresentation'

const canonicalFragmentIds = [
  'audience_reactions_fragment',
  'award_trophy_fragment',
  'farewell_letter_fragment',
  'fragment_certificate',
  'fragment_family_photo',
  'fragment_grandpa_knife',
  'fragment_last_puppet',
  'fragment_last_show',
  'fragment_letter',
  'fragment_old_photos',
  'fragment_shadow_puppet',
  'fragment_three_kings',
  'hologram_stage_fragment',
  'old_photos_wall_fragment',
  'puppet_trunk_fragment',
  'station_clock_fragment',
  'train_ticket_fragment',
].sort()

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

  it('registers exactly all seventeen canonical fragment inserts', () => {
    expect(FRAGMENT_PRESENTATION_IDS).toEqual(canonicalFragmentIds)
    expect(canonicalFragmentIds.every((id) => getFragmentPresentation(id) !== null)).toBe(true)
    expect(getFragmentPresentation('unknown_fragment')).toBeNull()
  })

  it('registers all three 1972 interaction inserts', () => {
    const expected = {
      fragment_shadow_puppet: 'fragment-1972-shadow-stage',
      fragment_grandpa_knife: 'fragment-1972-carving-knife',
      fragment_three_kings: 'fragment-1972-three-kings',
    }

    for (const [id, filename] of Object.entries(expected)) {
      expect(getFragmentPresentation(id)?.image).toContain(filename)
    }
  })

  it('registers all three additional 1990 interaction inserts', () => {
    const expected = {
      puppet_trunk_fragment: 'fragment-1990-puppet-trunk',
      farewell_letter_fragment: 'fragment-1990-farewell-letter',
      station_clock_fragment: 'fragment-1990-station-clock',
    }

    for (const [id, filename] of Object.entries(expected)) {
      expect(getFragmentPresentation(id)?.image).toContain(filename)
    }
  })

  it('registers both additional 2024 interaction inserts', () => {
    const expected = {
      fragment_old_photos: 'fragment-2024-old-photos',
      fragment_last_show: 'fragment-2024-last-show-poster',
    }

    for (const [id, filename] of Object.entries(expected)) {
      expect(getFragmentPresentation(id)?.image).toContain(filename)
    }
  })

  it('registers all three additional 2050 interaction inserts', () => {
    const expected = {
      old_photos_wall_fragment: 'fragment-2050-photo-wall',
      hologram_stage_fragment: 'fragment-2050-hologram-stage',
      audience_reactions_fragment: 'fragment-2050-audience-tears',
    }

    for (const [id, filename] of Object.entries(expected)) {
      expect(getFragmentPresentation(id)?.image).toContain(filename)
    }
  })

  it('registers both additional 2089 interaction inserts', () => {
    const expected = {
      fragment_family_photo: 'fragment-2089-family-photo',
      fragment_certificate: 'fragment-2089-heritage-certificate',
    }

    for (const [id, filename] of Object.entries(expected)) {
      expect(getFragmentPresentation(id)?.image).toContain(filename)
    }
  })
})
