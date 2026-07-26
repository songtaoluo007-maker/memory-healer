<script setup lang="ts">
import { computed } from 'vue'
import { buildFragmentGraph } from '../domain/fragmentGraph'
import type { FragmentState } from '../types/game'

const props = defineProps<{
  fragmentStates: Record<string, FragmentState>
  currentScene: string
}>()

const graph = computed(() => buildFragmentGraph(props.fragmentStates))
const nodeById = computed(() => new Map(graph.value.nodes.map((node) => [node.id, node] as const)))
const linkStates = computed(() =>
  graph.value.links.flatMap((link) => {
    const from = nodeById.value.get(link.from)
    const to = nodeById.value.get(link.to)
    if (!from || !to) return []
    return [
      {
        ...link,
        from,
        to,
        active: from.collected && to.collected,
        partial: from.revealed || to.revealed,
      },
    ]
  }),
)
const stats = computed(() => {
  const nodes = graph.value.nodes
  const collected = nodes.filter((node) => node.collected).length
  return {
    total: nodes.length,
    collected,
    percent: nodes.length > 0 ? Math.round((collected / nodes.length) * 100) : 0,
  }
})

function eraColor(scene: string): string {
  return graph.value.eras.find((era) => era.scene === scene)?.color ?? '#8a91a3'
}
</script>

<template>
  <div class="fragment-graph">
    <div class="graph-header">
      <h3 class="graph-title">记忆碎片关联图</h3>
      <div class="graph-stats">
        <span>{{ stats.collected }}/{{ stats.total }} 已收集</span>
        <strong>{{ stats.percent }}%</strong>
      </div>
    </div>

    <div class="graph-scroll">
      <svg viewBox="0 0 920 440" class="graph-svg" aria-label="五个时代的记忆碎片图">
        <defs>
          <filter id="fragment-glow" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur in="SourceGraphic" stdDeviation="4" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        <g v-for="era in graph.eras" :key="era.scene">
          <rect
            :x="era.x - 74"
            y="28"
            width="148"
            height="382"
            rx="10"
            :fill="era.color"
            fill-opacity="0.08"
            :stroke="era.scene === currentScene ? era.color : 'transparent'"
            stroke-opacity="0.45"
          />
          <text
            :x="era.x"
            y="58"
            text-anchor="middle"
            font-size="13"
            :fill="era.color"
            font-weight="600"
          >
            {{ era.label }}
          </text>
        </g>

        <g v-for="link in linkStates" :key="`${link.from.id}-${link.to.id}`">
          <line
            :x1="link.from.x"
            :y1="link.from.y"
            :x2="link.to.x"
            :y2="link.to.y"
            :stroke="link.active ? '#69c58b' : link.partial ? '#d89a48' : '#59606f'"
            :stroke-width="link.active ? 2.5 : 1.5"
            :stroke-dasharray="link.partial || link.active ? 'none' : '5 6'"
            :opacity="link.active ? 0.85 : 0.45"
          />
        </g>

        <g v-for="node in graph.nodes" :key="node.id">
          <circle
            :cx="node.x"
            :cy="node.y"
            r="22"
            :fill="
              node.collected
                ? 'rgba(105,197,139,.2)'
                : node.revealed
                  ? 'rgba(216,154,72,.18)'
                  : 'rgba(30,33,40,.8)'
            "
            :stroke="node.collected ? '#69c58b' : node.revealed ? eraColor(node.scene) : '#59606f'"
            stroke-width="2"
            :filter="node.collected ? 'url(#fragment-glow)' : undefined"
          />
          <text
            :x="node.x"
            :y="node.y + 5"
            text-anchor="middle"
            font-size="15"
            :fill="node.collected ? '#8ee2ab' : node.revealed ? '#e4b56f' : '#767d8c'"
          >
            {{ node.collected ? '✦' : node.revealed ? '◯' : '?' }}
          </text>
          <text
            :x="node.x"
            :y="node.y + 36"
            text-anchor="middle"
            font-size="10"
            :fill="node.revealed || node.collected ? '#d8d2c6' : '#737887'"
          >
            {{ node.revealed || node.collected ? node.name.slice(0, 8) : '未唤醒' }}
          </text>
        </g>
      </svg>
    </div>

    <div class="graph-legend">
      <span><i class="dot collected"></i>已收集</span>
      <span><i class="dot revealed"></i>已发现</span>
      <span><i class="dot locked"></i>未解锁</span>
    </div>
  </div>
</template>

<style scoped>
.fragment-graph {
  margin: 0 auto;
  max-width: 960px;
  padding: 16px;
  border: 1px solid rgba(211, 174, 104, 0.16);
  border-radius: 12px;
  background: rgba(12, 13, 18, 0.94);
}

.graph-header,
.graph-stats,
.graph-legend {
  display: flex;
  align-items: center;
}

.graph-header {
  justify-content: space-between;
  margin-bottom: 8px;
}

.graph-title {
  margin: 0;
  color: #eee6d8;
  font-family: 'Noto Serif SC', serif;
  font-size: 16px;
}

.graph-stats {
  gap: 12px;
  color: #969aa5;
  font-size: 12px;
}

.graph-stats strong {
  color: #79ca94;
  font-size: 14px;
}

.graph-scroll {
  overflow-x: auto;
}

.graph-svg {
  display: block;
  min-width: 760px;
  width: 100%;
  height: auto;
}

.graph-legend {
  justify-content: center;
  gap: 22px;
  padding-top: 10px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  color: #8f94a0;
  font-size: 11px;
}

.graph-legend span {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
}

.dot.collected {
  background: #69c58b;
}

.dot.revealed {
  background: #d89a48;
}

.dot.locked {
  background: #59606f;
}
</style>
