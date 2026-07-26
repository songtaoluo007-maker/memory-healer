import axios from 'axios'
import type {
  ActionResult,
  DialogueRequest,
  DialogueResponse,
  EndingContent,
  GameState,
  LoadedSave,
  NewGameResponse,
  SaveMutationResult,
  SaveSlot,
  SceneView,
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

// 权威游戏与对话
export const getNewGame = () => api.get<NewGameResponse>('/game/new')

export const getSceneView = (gameState: GameState) =>
  api.post<SceneView>('/game/scene', { game_state: gameState })

export const exploreHotspot = (hotspotId: string, gameState: GameState, expectedRevision: number) =>
  api.post<ActionResult>('/game/explore', {
    hotspot_id: hotspotId,
    game_state: gameState,
    expected_revision: expectedRevision,
  })

export const recordChoice = (choiceId: string, gameState: GameState, expectedRevision: number) =>
  api.post<ActionResult>('/game/choice', {
    choice_id: choiceId,
    game_state: gameState,
    expected_revision: expectedRevision,
  })

export const chatWithNpc = (data: DialogueRequest) =>
  api.post<DialogueResponse>('/dialogue/chat', data)

// 存档
export const saveGame = (
  slotId: number,
  slotName: string,
  gameState: GameState,
  expectedRevision: number,
) =>
  api.post<SaveMutationResult>('/save/save', {
    slot_id: slotId,
    slot_name: slotName,
    game_state: gameState,
    expected_revision: expectedRevision,
  })

export const loadGame = (slotId: number) => api.post<LoadedSave>('/save/load', { slot_id: slotId })

export const listSaves = () => api.get<{ saves: SaveSlot[] }>('/save/list')

export const deleteSave = (slotId: number) => api.delete(`/save/delete/${slotId}`)

// 健康检查
export const healthCheck = () =>
  api.get<{ status: string; service: string; version: string; database: string }>('/health')

// 权威结局评估
export const evaluateEnding = (gameState: GameState) =>
  api.post<{ ending: EndingContent }>('/game/ending', { game_state: gameState })

export const getEndingHint = (gameState: GameState) =>
  api.post<{ hint: string }>('/ending/hint', { game_state: gameState })
