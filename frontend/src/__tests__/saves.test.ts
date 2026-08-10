import { createApp, nextTick } from 'vue'
import { afterEach, describe, expect, it, vi } from 'vitest'
import Saves from '../views/Saves.vue'
import { listSaves } from '../api'

vi.mock('../api', () => ({
  deleteSave: vi.fn(),
  listSaves: vi.fn(),
}))

const mockedListSaves = vi.mocked(listSaves)

const flushPromises = () => new Promise((resolve) => window.setTimeout(resolve, 0))

describe('Saves', () => {
  afterEach(() => {
    document.body.replaceChildren()
    vi.resetAllMocks()
  })

  it('renders canonical titles for every later-era save and preserves unknown IDs', async () => {
    mockedListSaves.mockResolvedValue({
      data: {
        saves: [
          {
            slot_id: 1,
            slot_name: '深圳初到',
            scene_id: 'scene_1990',
            play_time: 0,
            save_revision: 1,
            state_revision: 1,
            saved_at: '2026-08-02T00:00:00Z',
            created_at: '2026-08-02T00:00:00Z',
            updated_at: '2026-08-02T00:00:00Z',
          },
          {
            slot_id: 2,
            slot_name: '颁奖之夜',
            scene_id: 'scene_2050',
            play_time: 0,
            save_revision: 1,
            state_revision: 1,
            saved_at: '2026-08-02T00:00:00Z',
            created_at: '2026-08-02T00:00:00Z',
            updated_at: '2026-08-02T00:00:00Z',
          },
          {
            slot_id: 3,
            slot_name: '未知坐标',
            scene_id: 'scene_unknown',
            play_time: 0,
            save_revision: 1,
            state_revision: 1,
            saved_at: '2026-08-02T00:00:00Z',
            created_at: '2026-08-02T00:00:00Z',
            updated_at: '2026-08-02T00:00:00Z',
          },
        ],
      },
    } as Awaited<ReturnType<typeof listSaves>>)
    const host = document.createElement('div')
    const app = createApp(Saves)
    app.mount(host)
    document.body.append(host)

    await flushPromises()
    await nextTick()

    expect(host.textContent).toContain('1990 · 深圳火车站')
    expect(host.textContent).toContain('2050 · 颁奖典礼')
    expect(host.textContent).toContain('scene_unknown')

    app.unmount()
  })
})
