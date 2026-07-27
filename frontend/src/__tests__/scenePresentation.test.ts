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

  it('registers the 1990 scene and both distinct NPC portraits', () => {
    const scene = getScenePresentation('scene_1990')

    expect(scene).not.toBeNull()
    if (scene) {
      expect(scene.background).toContain('scene-1990-shenzhen-station')
      expect(Object.keys(scene.portraits).sort()).toEqual(['chen_shouyi_1990', 'stranger_1990'])
      expect(scene.portraits.chen_shouyi_1990).not.toBe(scene.portraits.stranger_1990)
      expect(scene.composition.mobileFocus).toBeDefined()
    }
  })

  it('registers the rain-soaked 2024 room and elderly Chen Shouyi', () => {
    const scene = getScenePresentation('scene_2024')

    expect(scene).not.toBeNull()
    if (scene) {
      expect(scene.background).toContain('scene-2024-urban-village-room')
      expect(scene.portraits).toHaveProperty('chen_shouyi_old')
      expect(scene.palette).toBe('rain')
      expect(scene.composition.mobileFocus).toEqual([0.57, 0.5])
    }
  })

  it('registers the 2050 ceremony and both interview participants', () => {
    const scene = getScenePresentation('scene_2050')

    expect(scene).not.toBeNull()
    if (scene) {
      expect(scene.background).toContain('scene-2050-award-ceremony')
      expect(Object.keys(scene.portraits).sort()).toEqual(['journalist_2050', 'xiaoyu_2050'])
      expect(scene.portraits.xiaoyu_2050).not.toBe(scene.portraits.journalist_2050)
      expect(scene.palette).toBe('ceremony')
      expect(scene.composition.mobileFocus).toEqual([0.53, 0.48])
    }
  })

  it('registers the 2089 memory lab and Xiaoyu projection', () => {
    const scene = getScenePresentation('scene_2089')

    expect(scene).not.toBeNull()
    if (scene) {
      expect(scene.background).toContain('scene-2089-memory-lab')
      expect(scene.portraits).toHaveProperty('xiaoyu')
      expect(scene.portraits.xiaoyu).toContain('xiaoyu-2089-projection')
      expect(scene.palette).toBe('memory')
    }
  })

  it('covers all five story eras and rejects unknown scenes', () => {
    expect(
      ['scene_1972', 'scene_1990', 'scene_2024', 'scene_2050', 'scene_2089'].every(
        (id) => getScenePresentation(id) !== null,
      ),
    ).toBe(true)
    expect(getScenePresentation('unknown_scene')).toBeNull()
  })
})
