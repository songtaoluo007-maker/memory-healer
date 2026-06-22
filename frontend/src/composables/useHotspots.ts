/**
 * 热区探索系统
 * 在SceneIllustration叠加可点击热区，点击后触发探索对话/碎片发现
 */

import { ref, computed } from 'vue'

export interface Hotspot {
  id: string
  x: number        // SVG坐标 (基于800x600画布)
  y: number
  radius: number
  fragment_id: string | null
  hint: string
  npc_id?: string  // 关联NPC，点击时可能触发NPC对话
  color?: string   // 热区光圈颜色
  scene: string
}

// ── 各场景热区配置 ──
const allHotspots: Record<string, Hotspot[]> = {
  scene_1972: [
    {
      id: 'tool_box',
      x: 340, y: 310, radius: 25,
      fragment_id: 'fragment_grandpa_knife',
      hint: '戏台旁的工具箱，里面好像有什么东西……',
      scene: 'scene_1972',
      color: '#f59e0b',
    },
    {
      id: 'window',
      x: 110, y: 280, radius: 20,
      fragment_id: null,
      hint: '纸窗里透出暖光，能听到巷子里传来的秦腔声。',
      scene: 'scene_1972',
      color: '#f59e0b',
    },
    {
      id: 'shadow_screen',
      x: 400, y: 170, radius: 30,
      fragment_id: 'fragment_shadow_puppet',
      hint: '皮影戏幕布！上面还残留着"三英战吕布"的影子。',
      scene: 'scene_1972',
      color: '#f59e0b',
    },
    {
      id: 'bench',
      x: 580, y: 340, radius: 22,
      fragment_id: null,
      hint: '一条旧长凳，坐上去还能感受到余温。有人刚离开？',
      scene: 'scene_1972',
      color: '#f59e0b',
    },
    {
      id: 'old_photo',
      x: 660, y: 250, radius: 18,
      fragment_id: 'fragment_childhood_photo',
      hint: '墙上挂着一张泛黄的照片……',
      npc_id: 'chen_shouyi_young',
      scene: 'scene_1972',
      color: '#f59e0b',
    },
  ],
  scene_2024: [
    {
      id: 'desk_medicine',
      x: 260, y: 290, radius: 22,
      fragment_id: 'fragment_medicine_label',
      hint: '桌上散落着几瓶药，标签上的字已经模糊了……',
      scene: 'scene_2024',
      color: '#60a5fa',
    },
    {
      id: 'photo_wall',
      x: 140, y: 240, radius: 28,
      fragment_id: 'fragment_wedding_photo',
      hint: '墙上挂满了照片，有一张婚纱照格外显眼。',
      scene: 'scene_2024',
      color: '#60a5fa',
    },
    {
      id: 'teacup',
      x: 440, y: 310, radius: 18,
      fragment_id: null,
      hint: '一杯温热的茶，茶水还在微微冒着热气。',
      npc_id: 'chen_shouyi_old',
      scene: 'scene_2024',
      color: '#60a5fa',
    },
    {
      id: 'neon_window',
      x: 680, y: 190, radius: 25,
      fragment_id: null,
      hint: '窗外是深圳的霓虹灯海，远处传来城中村的嘈杂声。',
      scene: 'scene_2024',
      color: '#60a5fa',
    },
    {
      id: 'letter_box',
      x: 560, y: 280, radius: 20,
      fragment_id: 'fragment_xiaoyu_letter',
      hint: '抽屉里好像有一封信……',
      npc_id: 'xiaoyu',
      scene: 'scene_2024',
      color: '#60a5fa',
    },
  ],
  scene_2089: [
    {
      id: 'hologram',
      x: 400, y: 190, radius: 35,
      fragment_id: 'fragment_shadow_puppet',
      hint: '全息投影仪，正在播放一段模糊的皮影戏影像……',
      scene: 'scene_2089',
      color: '#a78bfa',
    },
    {
      id: 'neural_device',
      x: 220, y: 270, radius: 22,
      fragment_id: 'fragment_su_family_letter',
      hint: '神经修复仪的控制面板，上面显示着记忆碎片数据。',
      scene: 'scene_2089',
      color: '#a78bfa',
    },
    {
      id: 'memory_tank',
      x: 580, y: 250, radius: 28,
      fragment_id: null,
      hint: '记忆存储舱，里面漂浮着光点般的记忆碎片。',
      scene: 'scene_2089',
      color: '#a78bfa',
    },
    {
      id: 'photo_frame',
      x: 680, y: 320, radius: 18,
      fragment_id: 'fragment_childhood_photo',
      hint: '桌上放着一个相框，照片已经褪色了……',
      scene: 'scene_2089',
      color: '#a78bfa',
    },
  ],
}

export function useHotspots(sceneId: string) {
  const exploredIds = ref<Set<string>>(new Set())
  const activeHotspot = ref<Hotspot | null>(null)

  const hotspots = computed(() => allHotspots[sceneId] || [])

  const unexploredHotspots = computed(() =>
    hotspots.value.filter(h => !exploredIds.value.has(h.id))
  )

  const exploreHotspot = (hotspotId: string): Hotspot | null => {
    const hotspot = hotspots.value.find(h => h.id === hotspotId)
    if (!hotspot) return null
    exploredIds.value.add(hotspotId)
    activeHotspot.value = hotspot
    return hotspot
  }

  const isExplored = (hotspotId: string) => exploredIds.value.has(hotspotId)

  const explorationProgress = computed(() => {
    if (hotspots.value.length === 0) return 100
    return Math.round((exploredIds.value.size / hotspots.value.length) * 100)
  })

  return {
    hotspots,
    unexploredHotspots,
    activeHotspot,
    exploredIds,
    exploreHotspot,
    isExplored,
    explorationProgress,
  }
}
