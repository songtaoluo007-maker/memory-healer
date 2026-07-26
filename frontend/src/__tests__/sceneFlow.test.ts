import { computed, ref } from 'vue'
import { describe, expect, it } from 'vitest'
import { buildFragmentGraph } from '../domain/fragmentGraph'
import { useHotspots } from '../composables/useHotspots'
import type { FragmentState, SceneView } from '../types/game'

const makeSceneView = (sceneId: string, hotspotId: string): SceneView => ({
  scene: {
    id: sceneId,
    title: sceneId,
    description: `${sceneId} description`,
    mood: 'warm',
    time_period: sceneId.replace('scene_', ''),
    location: '记忆场',
    npcs: [],
    fragments: [],
    exits: {},
    triggers: {},
    transition_in: '',
    transition_out: '',
    fallback_asset: `/assets/scenes/${sceneId}.webp`,
  },
  npcs: [],
  fragments: [],
  hotspots: [
    {
      id: hotspotId,
      scene_id: sceneId,
      label: hotspotId,
      x: 0.5,
      y: 0.5,
      radius: 0.05,
      fragment_id: null,
      npc_id: null,
      interaction: 'inspect',
      presentation_event: 'memory.inspect',
    },
  ],
  choices: [],
  content_version: 1,
})

describe('canonical scene flow', () => {
  it('reacts to scene-view replacement without retaining old hotspots', () => {
    const sceneView = ref<SceneView | null>(
      makeSceneView('scene_1972', 'hotspot_1972_shadow_stage'),
    )
    const { hotspots } = useHotspots(computed(() => sceneView.value))

    expect(hotspots.value.map((hotspot) => hotspot.id)).toEqual(['hotspot_1972_shadow_stage'])

    sceneView.value = makeSceneView('scene_1990', 'hotspot_1990_train_ticket')

    expect(hotspots.value.map((hotspot) => hotspot.id)).toEqual(['hotspot_1990_train_ticket'])
    expect(hotspots.value.some((hotspot) => hotspot.id.startsWith('hotspot_1972'))).toBe(false)
  })

  it('builds every graph node from canonical fragment state IDs', () => {
    const fragmentStates: Record<string, FragmentState> = {
      fragment_shadow_puppet: {
        id: 'fragment_shadow_puppet',
        name: '皮影戏幕',
        scene: 'scene_1972',
        status: 'collected',
        collected: true,
        revealed: true,
      },
      train_ticket_fragment: {
        id: 'train_ticket_fragment',
        name: '南下车票',
        scene: 'scene_1990',
        status: 'revealed',
        collected: false,
        revealed: true,
      },
    }

    const graph = buildFragmentGraph(fragmentStates)

    expect(graph.nodes.map((node) => node.id).sort()).toEqual(Object.keys(fragmentStates).sort())
    expect(graph.nodes.some((node) => ['puppet_stage', 'carving_knife'].includes(node.id))).toBe(
      false,
    )
    expect(
      graph.links.every(
        (link) => fragmentStates[link.from] !== undefined && fragmentStates[link.to] !== undefined,
      ),
    ).toBe(true)
  })
})
