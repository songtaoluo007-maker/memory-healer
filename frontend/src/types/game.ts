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
  transition_in?: string
  transition_out?: string
  fallback_asset: string
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
  status: 'hidden' | 'revealed' | 'collected'
  collected: boolean
  revealed: boolean
  scene: string
}

export interface DialogueMessage {
  role: 'player' | 'npc' | 'system'
  content: string
  npc_id?: string | null
  emotion?: string | null
}

export interface KeyChoiceRecord {
  choice_id: string
  scene_id: string
  made_at_revision: number
}

export interface GameState {
  schema_version: 1
  game_id: string
  revision: number
  current_scene: string
  visited_scenes: string[]
  collected_fragments: string[]
  revealed_fragments: string[]
  fragment_states: Record<string, FragmentState>
  npc_trust: Record<string, number>
  npc_emotions: Record<string, string>
  key_choices: KeyChoiceRecord[]
  butterfly_choices: Record<string, string>
  dialogue_history: DialogueMessage[]
  current_mood: string
  play_time_seconds: number
  started_at: string
  chapter: number
  ending: string | null
}

export interface NpcSummary {
  id: string
  name: string
  title: string
  avatar: string
  initial_trust: number
}

export interface SceneFragment {
  id: string
  name: string
  scene: string
  description: string
  unlock_method: string
  unlock_hint: string
  memory_text: string
  is_revealed: boolean
  is_collected: boolean
}

export interface Hotspot {
  id: string
  scene_id: string
  label: string
  x: number
  y: number
  radius: number
  fragment_id: string | null
  npc_id: string | null
  interaction: 'inspect' | 'collect' | 'talk'
  presentation_event: string
}

export interface ChoiceEffects {
  trust_changes: Record<string, number>
  reveal_fragments: string[]
  current_mood: string | null
}

export interface Choice {
  id: string
  scene_id: string
  label: string
  target_scene: string | null
  is_key: boolean
  effects: ChoiceEffects
}

export interface SceneView {
  scene: Scene
  npcs: NpcSummary[]
  fragments: SceneFragment[]
  hotspots: Hotspot[]
  choices: Choice[]
  content_version: number
}

export interface PresentationEvent {
  type: string
  content_id: string | null
  payload: Record<string, unknown>
}

export interface ActionResult {
  state: GameState
  events: PresentationEvent[]
}

export interface NewGameResponse {
  state: GameState
  scene_view: SceneView
  content_version: number
}

export interface DialogueRequest {
  npc_id: string
  player_input: string
  game_state: GameState
  expected_revision: number
}

export interface DialogueResponse {
  state: GameState
  reply: string
  fragment_revealed: string | null
  fragment_data: Fragment | null
  trust_change: number
  npc_mood: string
  inner_thought: string
  degraded: boolean
}

export interface EndingContent {
  id: EndingType
  title: string
  description: string
  priority: number
  conditions: {
    min_collected_ratio: number
    min_key_choices: number
    required_npc_trust: Record<string, number>
  }
}

export interface SaveSlot {
  slot_id: number
  slot_name: string
  scene_id: string
  play_time: number
  save_revision: number
  state_revision: number
  saved_at: string
  created_at: string
  updated_at: string
}

export interface SaveMutationResult extends SaveSlot {
  success: boolean
}

export interface LoadedSave extends SaveSlot {
  game_state: GameState
}

export interface ChatMessage {
  role: 'player' | 'npc' | 'system'
  content: string
  npcName?: string
  npcId?: string
  emotion?: string
  trustChange?: number
}

export interface AuthUser {
  user_id: number
  username: string
  nickname: string
}

export type EndingType = 'hope' | 'bittersweet' | 'tragic' | 'legacy'

// 场景ID类型
export type SceneId = 'scene_1972' | 'scene_1990' | 'scene_2024' | 'scene_2050' | 'scene_2089'
