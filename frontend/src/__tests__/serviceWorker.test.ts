import { afterEach, describe, expect, it, vi } from 'vitest'
import { syncServiceWorker } from '../serviceWorker'

describe('service worker environment boundary', () => {
  afterEach(() => vi.unstubAllGlobals())

  it('removes stale registrations in development', async () => {
    const unregister = vi.fn().mockResolvedValue(true)
    const getRegistrations = vi.fn().mockResolvedValue([{ unregister }])
    const register = vi.fn()
    vi.stubGlobal('navigator', { serviceWorker: { getRegistrations, register } })

    await syncServiceWorker(false)

    expect(getRegistrations).toHaveBeenCalledOnce()
    expect(unregister).toHaveBeenCalledOnce()
    expect(register).not.toHaveBeenCalled()
  })

  it('registers the offline worker only in production', async () => {
    const getRegistrations = vi.fn()
    const register = vi.fn().mockResolvedValue({})
    vi.stubGlobal('navigator', { serviceWorker: { getRegistrations, register } })

    await syncServiceWorker(true)

    expect(register).toHaveBeenCalledWith('/sw.js')
    expect(getRegistrations).not.toHaveBeenCalled()
  })
})
