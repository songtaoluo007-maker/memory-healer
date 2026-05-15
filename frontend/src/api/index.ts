import axios from 'axios'
import type {
  DialogueRequest,
  DialogueResponse,
  SceneDetail,
  NarrativeResult,
  GameState,
  SaveSlot,
} from '../types/game'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  timeout: 60000,
})

// 对话
export const chatWithNpc = (data: DialogueRequest) =>
  api.post<DialogueResponse>('/api/dialogue/chat', data)

// 场景
export const getSceneDetail = (sceneId: string, gameState: GameState) =>
  api.post<SceneDetail>('/api/scene/detail', { scene_id: sceneId, game_state: gameState })

export const advanceNarrative = (action: string, gameState: GameState) =>
  api.post<NarrativeResult>('/api/scene/advance', { action, game_state: gameState })

export const getInitialState = () =>
  api.get<GameState>('/api/scene/initial-state')

// 存档
export const saveGame = (slotId: number, slotName: string, gameState: GameState, sceneId: string, playTime: number) =>
  api.post('/api/save/save', { slot_id: slotId, slot_name: slotName, game_state: gameState, scene_id: sceneId, play_time: playTime })

export const loadGame = (slotId: number) =>
  api.post<{ game_state: GameState; scene_id: string; play_time: number; slot_name: string; saved_at: string }>(`/api/save/load`, { slot_id: slotId })

export const listSaves = () =>
  api.get<{ saves: SaveSlot[] }>('/api/save/list')

export const deleteSave = (slotId: number) =>
  api.delete(`/api/save/delete/${slotId}`)

// 健康检查
export const healthCheck = () =>
  api.get<{ status: string; game: string; has_ai_key: boolean }>('/api/health')

// SSE 流式对话
export function chatWithNpcStream(
  data: DialogueRequest,
  onToken: (token: string) => void,
  onDone: (result: DialogueResponse) => void,
  onError: (msg: string) => void,
) {
  const baseURL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
  const controller = new AbortController()

  fetch(`${baseURL}/api/dialogue/chat/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
    signal: controller.signal,
  }).then(async (res) => {
    if (!res.ok) {
      onError(`HTTP ${res.status}`)
      return
    }
    const reader = res.body?.getReader()
    if (!reader) return
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        try {
          const msg = JSON.parse(line.slice(6))
          if (msg.type === 'token') onToken(msg.content)
          else if (msg.type === 'done') onDone(msg as DialogueResponse)
          else if (msg.type === 'error') onError(msg.content)
        } catch {}
      }
    }
  }).catch((err) => {
    if (err.name !== 'AbortError') onError(err.message)
  })

  return controller
}
