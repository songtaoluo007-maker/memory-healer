import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 60000,
})

export interface DialogueRequest {
  npc_id: string
  player_input: string
  game_state: Record<string, unknown>
}

export interface DialogueResponse {
  reply: string
  fragment_revealed: string | null
  fragment_data: Record<string, unknown> | null
  trust_change: number
  npc_mood: string
}

export interface SceneDetail {
  scene: {
    id: string
    title: string
    description: string
    mood: string
    time_period: string
    location: string
  }
  npcs: Array<{ id: string; name: string; title: string; avatar: string }>
  fragments: Array<Record<string, unknown>>
}

export interface NarrativeResult {
  scene_description: string
  available_actions: string[]
  mood: string
  hints: string
  trigger_event: string | null
}

// 对话
export const chatWithNpc = (data: DialogueRequest) =>
  api.post<DialogueResponse>('/api/dialogue/chat', data)

// 场景
export const getSceneDetail = (sceneId: string, gameState: Record<string, unknown>) =>
  api.post<SceneDetail>('/api/scene/detail', { scene_id: sceneId, game_state: gameState })

export const advanceNarrative = (action: string, gameState: Record<string, unknown>) =>
  api.post<NarrativeResult>('/api/scene/advance', { action, game_state: gameState })

export const getInitialState = () => api.get('/api/scene/initial-state')

// 存档
export const saveGame = (slotId: number, slotName: string, gameState: Record<string, unknown>, sceneId: string, playTime: number) =>
  api.post('/api/save/save', { slot_id: slotId, slot_name: slotName, game_state: gameState, scene_id: sceneId, play_time: playTime })

export const loadGame = (slotId: number) => api.post('/api/save/load', { slot_id: slotId })

export const listSaves = () => api.get('/api/save/list')

export const deleteSave = (slotId: number) => api.delete(`/api/save/delete/${slotId}`)

// 健康检查
export const healthCheck = () => api.get('/api/health')
