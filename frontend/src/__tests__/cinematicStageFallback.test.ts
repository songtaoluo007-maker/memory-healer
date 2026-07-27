/* eslint-disable vue/one-component-per-file */
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

afterEach(() => {
  app?.unmount()
  app = null
  assetLoad.mockReset()
})

describe('CinematicStage fallback', () => {
  it('uses the legacy illustration when cinematic artwork fails to load', async () => {
    assetLoad.mockRejectedValueOnce(new Error('asset unavailable'))
    const host = document.createElement('div')
    app = createApp({
      render: () =>
        h(
          CinematicStage,
          { sceneId: 'scene_1990' },
          { default: () => h('div', { class: 'legacy-art' }, 'legacy illustration') },
        ),
    })

    app.mount(host)
    await nextTick()
    await new Promise((resolve) => window.setTimeout(resolve, 0))
    await nextTick()

    expect(assetLoad).toHaveBeenCalledTimes(1)
    expect(host.querySelector('.legacy-art')?.textContent).toBe('legacy illustration')
    expect(host.querySelector('.canvas-host')).toBeNull()
  })

  it('uses the legacy illustration for an unknown scene ID', async () => {
    const host = document.createElement('div')
    app = createApp({
      render: () =>
        h(
          CinematicStage,
          { sceneId: 'unknown_scene' },
          { default: () => h('div', { class: 'legacy-art' }, 'legacy illustration') },
        ),
    })

    app.mount(host)
    await nextTick()

    expect(assetLoad).not.toHaveBeenCalled()
    expect(host.querySelector('.legacy-art')).not.toBeNull()
  })
})
