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
  baseURL: '/api',
  timeout: 60000,
  withCredentials: true,
})

// 响应拦截器：Cookie 会话失效时清除本地展示缓存。
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('mh_user')
    }
    return Promise.reject(err)
  },
)

// 对话
export const chatWithNpc = (data: DialogueRequest) =>
  api.post<DialogueResponse>('/dialogue/chat', data)

// 场景
export const getSceneDetail = (sceneId: string, gameState: GameState) =>
  api.post<SceneDetail>('/scene/detail', { scene_id: sceneId, game_state: gameState })

export const advanceNarrative = (action: string, gameState: GameState) =>
  api.post<NarrativeResult>('/scene/advance', { action, game_state: gameState })

export const getInitialState = () => api.get<GameState>('/scene/initial-state')

// 存档
export const saveGame = (
  slotId: number,
  slotName: string,
  gameState: GameState,
  sceneId: string,
  playTime: number,
) =>
  api.post('/save/save', {
    slot_id: slotId,
    slot_name: slotName,
    game_state: gameState,
    scene_id: sceneId,
    play_time: playTime,
  })

export const loadGame = (slotId: number) =>
  api.post<{
    game_state: GameState
    scene_id: string
    play_time: number
    slot_name: string
    saved_at: string
  }>('/save/load', { slot_id: slotId })

export const listSaves = () => api.get<{ saves: SaveSlot[] }>('/save/list')

export const deleteSave = (slotId: number) => api.delete(`/save/delete/${slotId}`)

// 健康检查
export const healthCheck = () =>
  api.get<{ status: string; game: string; has_ai_key: boolean }>('/health')

// 结局评估
export const evaluateEnding = (gameState: GameState) =>
  api.post<{
    type: string
    collected: number
    total: number
    percent: number
    butterfly_triggered: number
    butterfly_total: number
    key_trust_met: boolean
  }>('/ending/evaluate', { game_state: gameState })

export const getEndingHint = (gameState: GameState) =>
  api.post<{ hint: string }>('/ending/hint', { game_state: gameState })

// 蝴蝶效应: 记录玩家选择
export const recordChoice = (scene: string, choice: string, gameState: GameState) =>
  api.post('/dialogue/choice', { scene, choice, game_state: gameState })

// SSE 流式对话（带重连）
export function chatWithNpcStream(
  data: DialogueRequest,
  onToken: (token: string) => void,
  onDone: (result: DialogueResponse) => void,
  onError: (msg: string) => void,
  maxRetries = 2,
) {
  const controller = new AbortController()

  const attempt = (retriesLeft: number) => {
    const headers: Record<string, string> = { 'Content-Type': 'application/json' }

    fetch('/api/dialogue/chat/stream', {
      method: 'POST',
      headers,
      body: JSON.stringify(data),
      signal: controller.signal,
      credentials: 'include',
    })
      .then(async (res) => {
        if (!res.ok) {
          if (res.status >= 500 && retriesLeft > 0) {
            setTimeout(() => attempt(retriesLeft - 1), 1000)
            return
          }
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
            } catch {
              // Ignore malformed SSE frames and continue reading the stream.
            }
          }
        }
      })
      .catch((err) => {
        if (err.name === 'AbortError') return
        if (retriesLeft > 0) {
          setTimeout(() => attempt(retriesLeft - 1), 1000)
        } else {
          onError(err.message)
        }
      })
  }

  attempt(maxRetries)
  return controller
}
