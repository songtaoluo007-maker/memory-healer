import { describe, expect, it } from 'vitest'
import { getScenePresentation } from '../stage/presentation'

describe('cinematic scene presentation registry', () => {
  it('registers a complete 1972 Xi’an art direction package', () => {
    const scene = getScenePresentation('scene_1972')

    expect(scene).toMatchObject({
      id: 'scene_1972',
      eraLabel: '壬子年 · 冬',
      locationLabel: '西安 · 南院门',
      palette: 'amber',
      composition: {
        desktopFocus: [0.38, 0.46],
        mobileFocus: [0.34, 0.5],
      },
    })
    expect(scene?.background).toContain('scene-1972-xian-alley')
    expect(scene?.portraits).toEqual({
      chen_shouyi_young: expect.stringContaining('chen-shouyi-1972'),
    })
    expect(scene).not.toHaveProperty('portrait')
    expect(scene).not.toHaveProperty('portraitNpcIds')
    expect(scene?.alt.length).toBeGreaterThan(20)
  })

  it('falls back cleanly for eras that do not have final cinematic art yet', () => {
    expect(getScenePresentation('scene_2024')).toBeNull()
    expect(getScenePresentation('scene_2089')).toBeNull()
  })
})
