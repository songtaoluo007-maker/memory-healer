import { createApp, h, nextTick } from 'vue'
import { afterEach, describe, expect, it, vi } from 'vitest'

const { assetLoad } = vi.hoisted(() => ({
  assetLoad: vi.fn(),
}))

vi.mock('pixi.js', () => ({
  Application: class {
    canvas = document.createElement('canvas')
    destroy = vi.fn()
    init = vi.fn().mockResolvedValue(undefined)
  },
  Assets: {
    load: assetLoad,
  },
  Container: class {},
  Graphics: class {},
  Sprite: class {},
}))

import CinematicStage from '../components/CinematicStage.vue'
import type { AppliedConsequence } from '../types/game'

let app: ReturnType<typeof createApp> | null = null

const mountStage = (
  sceneId: string,
  activeNpcId?: string,
  consequence?: AppliedConsequence | null,
) => {
  const host = document.createElement('div')
  app = createApp({
    render: () =>
      h(
        CinematicStage,
        { sceneId, activeNpcId, consequence },
        { default: () => h('div', { class: 'legacy-art' }, 'legacy illustration') },
      ),
  })
  app.mount(host)
  return host
}

afterEach(() => {
  app?.unmount()
  app = null
  assetLoad.mockReset()
})

describe('CinematicStage fallback', () => {
  const consequence = (variant: string, targetSceneId = 'scene_1990'): AppliedConsequence => ({
    id: `consequence_${variant}`,
    source_choice_id: 'encourage_art',
    target_scene_id: targetSceneId,
    variant,
    scene_text: '权威因果文本',
    npc_context: {},
  })

  it('uses the legacy illustration when cinematic artwork fails to load', async () => {
    assetLoad.mockRejectedValueOnce(new Error('asset unavailable'))
    const host = mountStage('scene_1990')
    await nextTick()
    await new Promise((resolve) => window.setTimeout(resolve, 0))
    await nextTick()

    expect(assetLoad).toHaveBeenCalledTimes(1)
    expect(host.querySelector('.legacy-art')?.textContent).toBe('legacy illustration')
    expect(host.querySelector('.canvas-host')).toBeNull()
  })

  it('uses the legacy illustration for an unknown scene ID', async () => {
    const host = mountStage('unknown_scene')
    await nextTick()

    expect(assetLoad).not.toHaveBeenCalled()
    expect(host.querySelector('.legacy-art')).not.toBeNull()
  })

  it('marks ordinary characters as solid physical layers', async () => {
    assetLoad.mockImplementationOnce(() => new Promise(() => undefined))
    const host = mountStage('scene_1990', 'stranger_1990')
    await nextTick()

    expect(
      host.querySelector('.character-portrait')?.getAttribute('data-character-treatment'),
    ).toBe('solid')
  })

  it('marks 2089 Xiaoyu as a solid physical layer', async () => {
    assetLoad.mockImplementationOnce(() => new Promise(() => undefined))
    const host = mountStage('scene_2089', 'xiaoyu')
    await nextTick()

    expect(
      host.querySelector('.character-portrait')?.getAttribute('data-character-treatment'),
    ).toBe('solid')
  })

  it('renders an open warm trunk, visible puppet, and paper note for legacy carried', async () => {
    assetLoad.mockImplementationOnce(() => new Promise(() => undefined))
    const host = mountStage('scene_1990', undefined, consequence('legacy_carried'))
    await nextTick()

    const prop = host.querySelector('.stage-consequence')
    expect(prop?.getAttribute('data-consequence-variant')).toBe('legacy_carried')
    expect(prop?.querySelector('.trunk-lid')).not.toBeNull()
    expect(prop?.querySelector('.modern-puppet')).not.toBeNull()
    expect(prop?.querySelector('.paper-note')?.textContent).toContain('手艺不该被埋没')
  })

  it('renders a half-closed latched trunk with an occluded puppet for legacy suppressed', async () => {
    assetLoad.mockImplementationOnce(() => new Promise(() => undefined))
    const host = mountStage('scene_1990', undefined, consequence('legacy_suppressed'))
    await nextTick()

    const prop = host.querySelector('.stage-consequence')
    expect(prop?.getAttribute('data-consequence-variant')).toBe('legacy_suppressed')
    expect(prop?.querySelector('.trunk-lid')).not.toBeNull()
    expect(prop?.querySelector('.trunk-latch')).not.toBeNull()
    expect(prop?.querySelector('.modern-puppet')).not.toBeNull()
    expect(prop?.querySelector('.paper-note')).toBeNull()
  })

  it.each([
    ['unknown variant', consequence('future_variant')],
    ['different target scene', consequence('legacy_carried', 'scene_2050')],
    ['no consequence', null],
  ])('leaves the base stage unchanged for %s', async (_label, appliedConsequence) => {
    assetLoad.mockImplementationOnce(() => new Promise(() => undefined))
    const host = mountStage('scene_1990', undefined, appliedConsequence)
    await nextTick()

    expect(host.querySelector('.stage-consequence')).toBeNull()
  })

  it('hides a failed character image without removing the stage', async () => {
    assetLoad.mockRejectedValueOnce(new Error('background unavailable'))
    const host = mountStage('scene_1990', 'stranger_1990')
    await nextTick()
    await new Promise((resolve) => window.setTimeout(resolve, 0))
    await nextTick()

    host.querySelector<HTMLImageElement>('.character-portrait')?.dispatchEvent(new Event('error'))
    await nextTick()

    expect(host.querySelector('.cinematic-stage')).not.toBeNull()
    expect(host.querySelector('.legacy-art')).not.toBeNull()
    expect(host.querySelector('.character-portrait')).toBeNull()
  })
})
