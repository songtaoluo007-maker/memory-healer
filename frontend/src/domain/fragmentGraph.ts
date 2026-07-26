import type { FragmentState } from '../types/game'

const ERA_ORDER = ['scene_1972', 'scene_1990', 'scene_2024', 'scene_2050', 'scene_2089'] as const

const ERA_META: Record<string, { label: string; color: string }> = {
  scene_1972: { label: '1972 · 西安', color: '#d89a48' },
  scene_1990: { label: '1990 · 南下', color: '#c17f4b' },
  scene_2024: { label: '2024 · 深圳', color: '#5c8fb8' },
  scene_2050: { label: '2050 · 传承', color: '#bca14b' },
  scene_2089: { label: '2089 · 记忆实验室', color: '#8d75b8' },
}

export interface FragmentGraphNode {
  id: string
  name: string
  scene: string
  x: number
  y: number
  collected: boolean
  revealed: boolean
}

export interface FragmentGraphLink {
  from: string
  to: string
  label: '同幕记忆' | '时代回响'
}

export interface FragmentGraphEra {
  scene: string
  label: string
  color: string
  x: number
}

export interface FragmentGraph {
  nodes: FragmentGraphNode[]
  links: FragmentGraphLink[]
  eras: FragmentGraphEra[]
}

export function buildFragmentGraph(fragmentStates: Record<string, FragmentState>): FragmentGraph {
  const sceneIds = [
    ...ERA_ORDER,
    ...Object.values(fragmentStates)
      .map((fragment) => fragment.scene)
      .filter(
        (scene, index, all) =>
          !ERA_ORDER.includes(scene as (typeof ERA_ORDER)[number]) && all.indexOf(scene) === index,
      )
      .sort(),
  ]
  const nodes: FragmentGraphNode[] = []
  const links: FragmentGraphLink[] = []
  const eras: FragmentGraphEra[] = []
  let previousSceneLastNode: FragmentGraphNode | undefined

  sceneIds.forEach((scene, sceneIndex) => {
    const fragments = Object.values(fragmentStates)
      .filter((fragment) => fragment.scene === scene)
      .sort((left, right) => left.id.localeCompare(right.id))
    if (fragments.length === 0) return

    const x = 90 + sceneIndex * 180
    const meta = ERA_META[scene] ?? { label: scene, color: '#8a91a3' }
    eras.push({ scene, label: meta.label, color: meta.color, x })

    const sceneNodes = fragments.map((fragment, fragmentIndex) => ({
      id: fragment.id,
      name: fragment.name,
      scene: fragment.scene,
      x,
      y: 110 + fragmentIndex * 78,
      collected: fragment.collected,
      revealed: fragment.revealed,
    }))
    nodes.push(...sceneNodes)

    for (let index = 1; index < sceneNodes.length; index += 1) {
      links.push({
        from: sceneNodes[index - 1].id,
        to: sceneNodes[index].id,
        label: '同幕记忆',
      })
    }
    if (previousSceneLastNode && sceneNodes[0]) {
      links.push({
        from: previousSceneLastNode.id,
        to: sceneNodes[0].id,
        label: '时代回响',
      })
    }
    previousSceneLastNode = sceneNodes.at(-1)
  })

  return { nodes, links, eras }
}
