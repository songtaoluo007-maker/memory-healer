/* eslint-disable vue/one-component-per-file */
import { createApp, h, nextTick, ref } from 'vue'
import { afterEach, describe, expect, it } from 'vitest'
import FragmentArtwork from '../components/FragmentArtwork.vue'
import type { FragmentPresentation } from '../stage/fragmentPresentation'

const presentation: FragmentPresentation = {
  id: 'test_fragment',
  image: '/test-fragment.webp',
  alt: '测试记忆碎片',
  focus: '40% 50%',
}

let app: ReturnType<typeof createApp> | null = null

afterEach(() => {
  app?.unmount()
  app = null
})

describe('FragmentArtwork', () => {
  it('renders the cinematic insert with accessible copy and focal point', () => {
    const host = document.createElement('div')
    app = createApp(FragmentArtwork, { presentation })
    app.mount(host)

    const image = host.querySelector('img')
    expect(image?.getAttribute('src')).toBe('/test-fragment.webp')
    expect(image?.getAttribute('alt')).toBe('测试记忆碎片')
    expect(image?.style.objectPosition).toBe('40% 50%')
  })

  it('self-hides after an image error so popup controls remain usable', async () => {
    const host = document.createElement('div')
    app = createApp(FragmentArtwork, { presentation })
    app.mount(host)

    host.querySelector('img')?.dispatchEvent(new Event('error'))
    await nextTick()

    expect(host.querySelector('figure')).toBeNull()
    expect(host.querySelector('img')).toBeNull()
  })

  it('renders the next fragment after a previous image failed', async () => {
    const host = document.createElement('div')
    const current = ref(presentation)
    app = createApp({
      render: () => h(FragmentArtwork, { presentation: current.value }),
    })
    app.mount(host)

    host.querySelector('img')?.dispatchEvent(new Event('error'))
    await nextTick()
    expect(host.querySelector('img')).toBeNull()

    current.value = {
      id: 'next_fragment',
      image: '/next-fragment.webp',
      alt: '下一张记忆碎片',
      focus: '50% 50%',
    }
    await nextTick()

    expect(host.querySelector('img')?.getAttribute('src')).toBe('/next-fragment.webp')
  })
})
