import scene1972Background from '../assets/cinematic/scene-1972-xian-alley.png'
import chenShouyi1972Portrait from '../assets/cinematic/chen-shouyi-1972.png'

export type CinematicPalette = 'amber' | 'neon' | 'memory'

export interface ScenePresentation {
  id: string
  eraLabel: string
  locationLabel: string
  palette: CinematicPalette
  background: string
  portrait: string | null
  portraitNpcIds: readonly string[]
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
    portrait: chenShouyi1972Portrait,
    portraitNpcIds: ['chen_shouyi_young'],
    alt: '1972年冬日的西安老巷，青砖院墙被暮色笼罩，窗内暖光映出皮影艺人的剪影。',
    composition: {
      desktopFocus: [0.38, 0.46],
      mobileFocus: [0.34, 0.5],
    },
  },
}

export function getScenePresentation(sceneId: string): ScenePresentation | null {
  return presentations[sceneId] ?? null
}
