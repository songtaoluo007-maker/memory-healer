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
      x: 337, y: 406, radius: 22,
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
      x: 400, y: 335, radius: 30,
      fragment_id: 'fragment_shadow_puppet',
      hint: '皮影戏幕布！上面还残留着"三英战吕布"的影子。',
      scene: 'scene_1972',
      color: '#f59e0b',
    },
    {
      id: 'bench',
      x: 590, y: 353, radius: 20,
      fragment_id: null,
      hint: '一条旧长凳，坐上去还能感受到余温。有人刚离开？',
      scene: 'scene_1972',
      color: '#f59e0b',
    },
    {
      id: 'old_photo',
      x: 665, y: 249, radius: 16,
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
      x: 255, y: 296, radius: 20,
      fragment_id: 'fragment_medicine_label',
      hint: '桌上散落着几瓶药，标签上的字已经模糊了……',
      scene: 'scene_2024',
      color: '#60a5fa',
    },
    {
      id: 'photo_wall',
      x: 145, y: 245, radius: 24,
      fragment_id: 'fragment_wedding_photo',
      hint: '墙上挂满了照片，有一张婚纱照格外显眼。',
      scene: 'scene_2024',
      color: '#60a5fa',
    },
    {
      id: 'teacup',
      x: 445, y: 306, radius: 16,
      fragment_id: null,
      hint: '一杯温热的茶，茶水还在微微冒着热气。',
      npc_id: 'chen_shouyi_old',
      scene: 'scene_2024',
      color: '#60a5fa',
    },
    {
      id: 'neon_window',
      x: 688, y: 192, radius: 22,
      fragment_id: null,
      hint: '窗外是深圳的霓虹灯海，远处传来城中村的嘈杂声。',
      scene: 'scene_2024',
      color: '#60a5fa',
    },
    {
      id: 'letter_box',
      x: 560, y: 297, radius: 20,
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
      x: 400, y: 200, radius: 35,
      fragment_id: 'fragment_shadow_puppet',
      hint: '全息投影仪，正在播放一段模糊的皮影戏影像……',
      scene: 'scene_2089',
      color: '#a78bfa',
    },
    {
      id: 'neural_device',
      x: 225, y: 280, radius: 22,
      fragment_id: 'fragment_su_family_letter',
      hint: '神经修复仪的控制面板，上面显示着记忆碎片数据。',
      scene: 'scene_2089',
      color: '#a78bfa',
    },
    {
      id: 'memory_tank',
      x: 580, y: 270, radius: 28,
      fragment_id: null,
      hint: '记忆存储舱，里面漂浮着光点般的记忆碎片。',
      scene: 'scene_2089',
      color: '#a78bfa',
    },
    {
      id: 'photo_frame',
      x: 682, y: 322, radius: 16,
      fragment_id: 'fragment_childhood_photo',
      hint: '桌上放着一个相框，照片已经褪色了……',
      scene: 'scene_2089',
      color: '#a78bfa',
    },
  ],
  scene_1990: [
    {
      id: 'train_ticket',
      x: 355, y: 206, radius: 22,
      fragment_id: 'train_ticket_fragment',
      hint: '一张皱巴巴的硬座票，西安到深圳，42元。',
      scene: 'scene_1990',
      color: '#d97706',
    },
    {
      id: 'puppet_trunk',
      x: 605, y: 357, radius: 28,
      fragment_id: 'puppet_trunk_fragment',
      hint: '装满皮影道具的旧木箱，里面好像有个穿西装的皮影……',
      scene: 'scene_1990',
      color: '#d97706',
    },
    {
      id: 'farewell_letter',
      x: 154, y: 284, radius: 16,
      fragment_id: 'farewell_letter_fragment',
      hint: '一封信从口袋里露出一角，收信人是“师父”。',
      scene: 'scene_1990',
      color: '#d97706',
    },
    {
      id: 'station_clock',
      x: 400, y: 80, radius: 25,
      fragment_id: 'station_clock_fragment',
      hint: '巨大的圆形时钟，指针指向下午3:47。',
      scene: 'scene_1990',
      color: '#d97706',
    },
    {
      id: 'stranger',
      x: 700, y: 393, radius: 18,
      fragment_id: null,
      hint: '一个穿夹克的年轻人正在张望，看起来也是来深圳的。',
      npc_id: 'stranger_1990',
      scene: 'scene_1990',
      color: '#d97706',
    },
  ],
  scene_2050: [
    {
      id: 'award_trophy',
      x: 400, y: 305, radius: 20,
      fragment_id: 'award_trophy_fragment',
      hint: '水晶奖杯折射着七彩光芒，底座刻着“非遗传承杰出贡献奖”。',
      scene: 'scene_2050',
      color: '#eab308',
    },
    {
      id: 'old_photos_wall',
      x: 205, y: 210, radius: 28,
      fragment_id: 'old_photos_wall_fragment',
      hint: '照片墙上挂满了跨越半个世纪的照片。',
      scene: 'scene_2050',
      color: '#eab308',
    },
    {
      id: 'hologram_stage',
      x: 620, y: 310, radius: 35,
      fragment_id: 'hologram_stage_fragment',
      hint: '全息投影正在表演皮影戏——三英战吕布！',
      scene: 'scene_2050',
      color: '#eab308',
    },
    {
      id: 'audience_reactions',
      x: 300, y: 400, radius: 25,
      fragment_id: 'audience_reactions_fragment',
      hint: '观众席中一位白发老人悄悄擦眼泪，手里拿着旧皮影。',
      scene: 'scene_2050',
      color: '#eab308',
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
