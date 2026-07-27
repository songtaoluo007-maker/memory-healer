import scene1972Background from '../assets/cinematic/scene-1972-xian-alley.png'
import chenShouyi1972Portrait from '../assets/cinematic/chen-shouyi-1972-solid.webp'
import scene1990Background from '../assets/cinematic/scene-1990-shenzhen-station.webp'
import chenShouyi1990Portrait from '../assets/cinematic/chen-shouyi-1990-solid.webp'
import stranger1990Portrait from '../assets/cinematic/stranger-1990-solid.webp'
import scene2024Background from '../assets/cinematic/scene-2024-urban-village-room.webp'
import chenShouyi2024Portrait from '../assets/cinematic/chen-shouyi-2024-solid.webp'
import scene2050Background from '../assets/cinematic/scene-2050-award-ceremony.webp'
import xiaoyu2050Portrait from '../assets/cinematic/xiaoyu-2050-solid.webp'
import journalist2050Portrait from '../assets/cinematic/journalist-2050-solid.webp'
import scene2089Background from '../assets/cinematic/scene-2089-memory-lab.webp'
import xiaoyu2089Projection from '../assets/cinematic/xiaoyu-2089-projection-solid.webp'

export type CinematicPalette = 'amber' | 'rail' | 'rain' | 'ceremony' | 'memory'

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
  scene_2024: {
    id: 'scene_2024',
    eraLabel: '甲辰年 · 雨夜',
    locationLabel: '深圳 · 城中村',
    palette: 'rain',
    background: scene2024Background,
    portraits: {
      chen_shouyi_old: chenShouyi2024Portrait,
    },
    alt: '2024年深圳城中村的雨夜出租屋，旧皮影工作台面对被霓虹切开的窗户，信件与泛黄剧照仍留在暗处。',
    composition: {
      desktopFocus: [0.5, 0.5],
      mobileFocus: [0.57, 0.5],
    },
  },
  scene_2050: {
    id: 'scene_2050',
    eraLabel: '庚午年 · 典礼',
    locationLabel: '北京 · 国家大剧院',
    palette: 'ceremony',
    background: scene2050Background,
    portraits: {
      xiaoyu_2050: xiaoyu2050Portrait,
      journalist_2050: journalist2050Portrait,
    },
    alt: '2050年北京的非遗传承颁奖舞台，水晶奖杯、时光照片墙与全息皮影在象牙金灯光中彼此呼应。',
    composition: {
      desktopFocus: [0.5, 0.5],
      mobileFocus: [0.53, 0.48],
    },
  },
  scene_2089: {
    id: 'scene_2089',
    eraLabel: '记忆纪元 · 终幕',
    locationLabel: '深圳 · 拾忆实验室',
    palette: 'memory',
    background: scene2089Background,
    portraits: {
      xiaoyu: xiaoyu2089Projection,
    },
    alt: '2089年拾忆实验室，四个年代的记忆残片在神经接口躺椅上方重组，最后一枚孙悟空皮影守在暖色光核中。',
    composition: {
      desktopFocus: [0.5, 0.5],
      mobileFocus: [0.5, 0.49],
    },
  },
}

export function getScenePresentation(sceneId: string): ScenePresentation | null {
  return presentations[sceneId] ?? null
}
