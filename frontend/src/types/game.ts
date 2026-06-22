/** 拾忆 - 游戏类型定义 */

export interface Scene {
  id: string
  title: string
  description: string
  mood: string
  time_period: string
  location: string
  bgm?: string
  npcs: string[]
  fragments: string[]
  exits?: Record<string, string>
  triggers?: Record<string, string>
}

export interface Npc {
  id: string
  name: string
  title: string
  age: number
  scene: string
  avatar: string
  personality: string
  background: string
  system_prompt: string
  initial_trust: number
  fragments_to_reveal: string[]
}

export interface Fragment {
  id: string
  name: string
  scene: string
  description: string
  unlock_method: string
  unlock_hint: string
  memory_text: string
  collected: boolean
}

export interface FragmentState {
  id: string
  name: string
  collected: boolean
  revealed: boolean
  scene: string
}

export interface GameState {
  current_scene: string
  collected_fragments: string[]
  revealed_fragments: string[]
  fragment_states: Record<string, FragmentState>
  npc_trust: Record<string, number>
  key_choices: string[]
  dialogue_history: Array<{ role: string; content: string }>
  current_mood: string
  play_time: number
  chapter: number
  ending: string | null
}

export interface NpcSummary {
  id: string
  name: string
  title: string
  avatar: string
}

export interface SceneDetail {
  scene: Scene
  npcs: NpcSummary[]
  fragments: Array<Fragment & { is_collected: boolean }>
}

export interface DialogueRequest {
  npc_id: string
  player_input: string
  game_state: GameState
}

export interface DialogueResponse {
  reply: string
  fragment_revealed: string | null
  fragment_data: Fragment | null
  trust_change: number
  npc_mood: string
  inner_thought?: string
}

export interface NarrativeResult {
  scene_description: string
  available_actions: string[]
  mood: string
  hints: string
  trigger_event: string | null
  narrative_callback?: string
}

export interface SaveSlot {
  slot_id: number
  slot_name: string
  scene_id: string
  play_time: number
  saved_at: string
  created_at: string
  updated_at: string
}

export interface ChatMessage {
  role: 'player' | 'npc' | 'system'
  content: string
  npcName?: string
}

export type EndingType = 'hope' | 'bittersweet' | 'tragic'
