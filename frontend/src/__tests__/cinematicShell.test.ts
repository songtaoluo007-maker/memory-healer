import { beforeEach, describe, expect, it } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { routes } from '../router'
import { useUiStore } from '../stores/ui'

describe('cinematic application shell', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('defines the complete route-level story flow', () => {
    expect(routes.map((route) => route.name)).toEqual([
      'home',
      'prologue',
      'tutorial',
      'memory',
      'saves',
      'ending',
    ])
  })

  it('keeps cinematic overlays mutually exclusive', () => {
    const ui = useUiStore()

    ui.openOverlay('inventory')
    expect(ui.activeOverlay).toBe('inventory')

    ui.openOverlay('memory')
    expect(ui.activeOverlay).toBe('memory')

    ui.closeOverlay('inventory')
    expect(ui.activeOverlay).toBe('memory')

    ui.closeOverlay('memory')
    expect(ui.activeOverlay).toBeNull()
  })

  it('tracks the current stage mode independently from game rules', () => {
    const ui = useUiStore()

    ui.setStageMode('dialogue')

    expect(ui.stageMode).toBe('dialogue')
    expect(ui.activeOverlay).toBeNull()
  })
})
