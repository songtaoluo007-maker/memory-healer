import { computed, ref } from 'vue'
import { describe, expect, it } from 'vitest'
import { buildFragmentGraph } from '../domain/fragmentGraph'
import { useMemoryReasoningSelection } from '../domain/memoryReasoning'
import { useHotspots } from '../composables/useHotspots'
import { useScene } from '../composables/useScene'
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
  hypotheses:
    sceneId === 'scene_1972'
      ? [
          {
            id: 'hypothesis_1972_legacy',
            scene_id: 'scene_1972',
            question: '陈守义为什么仍想把皮影传下去？',
            statement: '刻刀与戏幕共同指向传承。',
            evidence_ids: ['fragment_grandpa_knife', 'fragment_shadow_puppet'],
            resolution: '两条记忆互相印证。',
          },
        ]
      : sceneId === 'scene_1990'
        ? [
            {
              id: 'hypothesis_1990_survival',
              scene_id: 'scene_1990',
              question: '陈守义南下是否意味着他准备抛下皮影？',
              statement: '生存压力迫使他离开。',
              evidence_ids: ['train_ticket_fragment', 'farewell_letter_fragment'],
              resolution: '犹豫不能证明放弃。',
            },
            {
              id: 'hypothesis_1990_modern_story',
              scene_id: 'scene_1990',
              question: '陈守义为什么带着整箱皮影来到深圳？',
              statement: '他在为皮影寻找新讲法。',
              evidence_ids: ['puppet_trunk_fragment', 'station_clock_fragment'],
              resolution: '他带着皮影走进了新生活。',
            },
          ]
        : [],
  applied_consequences: [],
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

  it('exposes only the current scene hypotheses without retaining the prior act', () => {
    const { hypotheses, replaceSceneView } = useScene()

    replaceSceneView(makeSceneView('scene_1972', 'hotspot_1972_shadow_stage'))
    expect(hypotheses.value.map((hypothesis) => hypothesis.id)).toEqual(['hypothesis_1972_legacy'])

    replaceSceneView(makeSceneView('scene_1990', 'hotspot_1990_train_ticket'))
    expect(hypotheses.value.map((hypothesis) => hypothesis.id)).toEqual([
      'hypothesis_1990_survival',
      'hypothesis_1990_modern_story',
    ])
  })

  it('retains canonical consequences while selecting only the active scene target', () => {
    const scene = useScene()
    const view = makeSceneView('scene_1990', 'hotspot_1990_train_ticket')
    view.applied_consequences = [
      {
        id: 'consequence_1972_legacy_carried',
        source_choice_id: 'encourage_art',
        target_scene_id: 'scene_1990',
        variant: 'legacy_carried',
        scene_text: '木箱敞开着，现代皮影清楚可见。',
        npc_context: { chen_shouyi_1990: '他愿意谈一谈新的故事。' },
      },
      {
        id: 'consequence_future_echo',
        source_choice_id: 'future_choice',
        target_scene_id: 'scene_2050',
        variant: 'future_echo',
        scene_text: '这条后果不属于当前场景。',
        npc_context: {},
      },
    ]

    scene.replaceSceneView(view)
    view.applied_consequences[0].scene_text = '调用方随后篡改的文本'

    expect(scene.sceneView.value?.applied_consequences).toHaveLength(2)
    expect(scene.sceneView.value?.applied_consequences[0].scene_text).toBe(
      '木箱敞开着，现代皮影清楚可见。',
    )
    expect(scene.activeConsequence.value?.id).toBe('consequence_1972_legacy_carried')
  })

  it('clears stale candidate, evidence, and rejection state when the scene view changes', () => {
    const scene = useScene()
    scene.replaceSceneView(makeSceneView('scene_1972', 'hotspot_1972_shadow_stage'))
    const selection = useMemoryReasoningSelection(scene.sceneView)
    selection.selectedEvidenceIds.value = ['fragment_grandpa_knife']
    selection.rejectedFeedback.value = '旧幕反馈'

    scene.replaceSceneView(makeSceneView('scene_1990', 'hotspot_1990_train_ticket'))

    expect(selection.selectedHypothesisId.value).toBe('hypothesis_1990_survival')
    expect(selection.selectedEvidenceIds.value).toEqual([])
    expect(selection.rejectedFeedback.value).toBeNull()
  })
})
