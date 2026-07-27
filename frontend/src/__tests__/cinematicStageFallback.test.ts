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

let app: ReturnType<typeof createApp> | null = null

const mountStage = (sceneId: string, activeNpcId?: string) => {
  const host = document.createElement('div')
  app = createApp({
    render: () =>
      h(
        CinematicStage,
        { sceneId, activeNpcId },
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

  it('marks 2089 Xiaoyu as the restrained projection exception', async () => {
    assetLoad.mockImplementationOnce(() => new Promise(() => undefined))
    const host = mountStage('scene_2089', 'xiaoyu')
    await nextTick()

    expect(
      host.querySelector('.character-portrait')?.getAttribute('data-character-treatment'),
    ).toBe('projection')
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
