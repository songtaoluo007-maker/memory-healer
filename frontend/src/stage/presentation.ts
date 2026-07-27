import scene1972Background from '../assets/cinematic/scene-1972-xian-alley.png'
import chenShouyi1972Portrait from '../assets/cinematic/chen-shouyi-1972.png'
import scene1990Background from '../assets/cinematic/scene-1990-shenzhen-station.webp'
import chenShouyi1990Portrait from '../assets/cinematic/chen-shouyi-1990.webp'
import stranger1990Portrait from '../assets/cinematic/stranger-1990.webp'

export type CinematicPalette = 'amber' | 'rail' | 'neon' | 'memory'

export interface ScenePresentation {
  id: string
  eraLabel: string
  locationLabel: string
  palette: CinematicPalette
  background: string
  portraits: Readonly<Record<string, string>>
  alt: string
  composition: {
    desktopFocus: readonly [number, number]
    mobileFocus: readonly [number, number]
  }
}

const presentations: Record<string, ScenePresentation> = {
  scene_1972: {
    id: 'scene_1972',
    eraLabel: '壬子年 · 冬',
    locationLabel: '西安 · 南院门',
    palette: 'amber',
    background: scene1972Background,
    portraits: {
      chen_shouyi_young: chenShouyi1972Portrait,
    },
    alt: '1972年冬日的西安老巷，青砖院墙被暮色笼罩，窗内暖光映出皮影艺人的剪影。',
    composition: {
      desktopFocus: [0.38, 0.46],
      mobileFocus: [0.34, 0.5],
    },
  },
  scene_1990: {
    id: 'scene_1990',
    eraLabel: '庚午年 · 秋',
    locationLabel: '深圳 · 火车站',
    palette: 'rail',
    background: scene1990Background,
    portraits: {
      chen_shouyi_1990: chenShouyi1990Portrait,
      stranger_1990: stranger1990Portrait,
    },
    alt: '1990年深圳火车站，绿皮火车驶入煤烟笼罩的站台，旧木箱与南下人群等待新的生活。',
    composition: {
      desktopFocus: [0.5, 0.48],
      mobileFocus: [0.52, 0.5],
    },
  },
}

export function getScenePresentation(sceneId: string): ScenePresentation | null {
  return presentations[sceneId] ?? null
}
