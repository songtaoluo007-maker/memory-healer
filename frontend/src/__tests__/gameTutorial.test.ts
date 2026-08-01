import { createApp, nextTick } from 'vue'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import GameTutorial from '../components/GameTutorial.vue'

describe('GameTutorial', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    localStorage.removeItem('mh_tutorial_done')
  })

  afterEach(() => {
    document.body.replaceChildren()
    vi.useRealTimers()
  })

  it('teaches the physical scan markers without reviving the old glowing-orb language', async () => {
    const host = document.createElement('div')
    const app = createApp(GameTutorial)
    app.mount(host)
    document.body.append(host)

    await vi.advanceTimersByTimeAsync(300)
    await nextTick()

    const scanStep = host.querySelector<HTMLButtonElement>(
      'button[aria-label="第 2 步：观察记忆场"]',
    )
    expect(scanStep).not.toBeNull()
    scanStep?.click()
    await nextTick()

    expect(host.textContent).toContain('取景标记')
    expect(host.textContent).toContain('进入扫描')
    expect(host.textContent).not.toContain('暖色光点')

    app.unmount()
  })
})
