<script setup lang="ts">
/**
 * 水墨粒子系统
 * - 场景切换：墨入水扩散
 * - 碎片收集：墨迹绽放
 * - 环境粒子：漂浮墨点
 */
import { ref, onMounted, onUnmounted, watch } from 'vue'

const props = defineProps<{
  sceneId: string
  trigger?: 'idle' | 'transition' | 'collect' // 触发模式
}>()

const emit = defineEmits<{
  complete: []
}>()

const canvasRef = ref<HTMLCanvasElement | null>(null)
let ctx: CanvasRenderingContext2D | null = null
let animId = 0
let particles: InkParticle[] = []

interface InkParticle {
  x: number
  y: number
  vx: number
  vy: number
  size: number
  alpha: number
  decay: number
  color: string
  type: 'ink' | 'splash' | 'float'
  life: number
  maxLife: number
  rotation: number
  rotationSpeed: number
}

const sceneColors: Record<string, string[]> = {
  scene_1972: ['40, 30, 20', '80, 60, 30', '120, 90, 40'],
  scene_1990: ['30, 40, 60', '50, 70, 100', '80, 100, 140'],
  scene_2024: ['50, 40, 60', '80, 60, 90', '110, 80, 120'],
  scene_2050: ['20, 40, 60', '40, 70, 100', '60, 100, 140'],
  scene_2089: ['60, 40, 30', '100, 70, 40', '140, 100, 50'],
}

function getColors(): string[] {
  return sceneColors[props.sceneId] || sceneColors.scene_1972
}

// 创建墨入水扩散效果
function createInkBurst(cx: number, cy: number, count: number = 30) {
  const colors = getColors()
  for (let i = 0; i < count; i++) {
    const angle = (Math.PI * 2 * i) / count + Math.random() * 0.5
    const speed = 1 + Math.random() * 3
    const size = 3 + Math.random() * 12
    particles.push({
      x: cx,
      y: cy,
      vx: Math.cos(angle) * speed,
      vy: Math.sin(angle) * speed,
      size,
      alpha: 0.6 + Math.random() * 0.4,
      decay: 0.005 + Math.random() * 0.01,
      color: colors[Math.floor(Math.random() * colors.length)],
      type: 'splash',
      life: 0,
      maxLife: 80 + Math.random() * 60,
      rotation: Math.random() * Math.PI * 2,
      rotationSpeed: (Math.random() - 0.5) * 0.1,
    })
  }
}

// 创建场景切换墨幕
function createInkCurtain(cx: number, cy: number) {
  const colors = getColors()
  for (let i = 0; i < 80; i++) {
    const angle = Math.random() * Math.PI * 2
    const dist = Math.random() * 200
    particles.push({
      x: cx + Math.cos(angle) * dist * 0.3,
      y: cy + Math.sin(angle) * dist * 0.3,
      vx: Math.cos(angle) * (2 + Math.random() * 4),
      vy: Math.sin(angle) * (2 + Math.random() * 4),
      size: 8 + Math.random() * 25,
      alpha: 0.8 + Math.random() * 0.2,
      decay: 0.003 + Math.random() * 0.005,
      color: colors[Math.floor(Math.random() * colors.length)],
      type: 'ink',
      life: 0,
      maxLife: 120 + Math.random() * 80,
      rotation: Math.random() * Math.PI * 2,
      rotationSpeed: (Math.random() - 0.5) * 0.05,
    })
  }
}

// 环境漂浮粒子
function spawnFloatParticle(w: number, h: number) {
  const colors = getColors()
  particles.push({
    x: Math.random() * w,
    y: h + 10,
    vx: (Math.random() - 0.5) * 0.5,
    vy: -0.3 - Math.random() * 0.5,
    size: 1 + Math.random() * 3,
    alpha: 0.1 + Math.random() * 0.2,
    decay: 0,
    color: colors[Math.floor(Math.random() * colors.length)],
    type: 'float',
    life: 0,
    maxLife: 300 + Math.random() * 200,
    rotation: 0,
    rotationSpeed: 0,
  })
}

function drawInkDrop(ctx: CanvasRenderingContext2D, p: InkParticle) {
  ctx.save()
  ctx.translate(p.x, p.y)
  ctx.rotate(p.rotation)

  // 墨滴形状（不规则圆）
  ctx.beginPath()
  const points = 8
  for (let i = 0; i <= points; i++) {
    const angle = (Math.PI * 2 * i) / points
    const wobble = 1 + Math.sin(angle * 3 + p.life * 0.05) * 0.3
    const r = p.size * wobble
    const x = Math.cos(angle) * r
    const y = Math.sin(angle) * r
    if (i === 0) ctx.moveTo(x, y)
    else ctx.lineTo(x, y)
  }
  ctx.closePath()

  // 墨迹渐变
  const grad = ctx.createRadialGradient(0, 0, 0, 0, 0, p.size)
  grad.addColorStop(0, `rgba(${p.color}, ${p.alpha * 0.8})`)
  grad.addColorStop(0.6, `rgba(${p.color}, ${p.alpha * 0.4})`)
  grad.addColorStop(1, `rgba(${p.color}, 0)`)
  ctx.fillStyle = grad
  ctx.fill()

  // 墨丝（仅ink类型）
  if (p.type === 'ink' && p.size > 10) {
    ctx.strokeStyle = `rgba(${p.color}, ${p.alpha * 0.2})`
    ctx.lineWidth = 0.5
    for (let i = 0; i < 3; i++) {
      const a = Math.random() * Math.PI * 2
      const len = p.size * (1 + Math.random())
      ctx.beginPath()
      ctx.moveTo(0, 0)
      ctx.quadraticCurveTo(
        Math.cos(a + 0.5) * len * 0.5,
        Math.sin(a + 0.5) * len * 0.5,
        Math.cos(a) * len,
        Math.sin(a) * len
      )
      ctx.stroke()
    }
  }

  ctx.restore()
}

function render() {
  if (!ctx || !canvasRef.value) return
  const w = canvasRef.value.width
  const h = canvasRef.value.height

  ctx.clearRect(0, 0, w, h)

  // 环境粒子生成
  if (props.trigger === 'idle' && Math.random() < 0.03) {
    spawnFloatParticle(w, h)
  }

  // 更新和绘制粒子
  for (let i = particles.length - 1; i >= 0; i--) {
    const p = particles[i]

    // 物理更新
    p.x += p.vx
    p.y += p.vy
    p.rotation += p.rotationSpeed

    // 阻尼
    p.vx *= 0.98
    p.vy *= 0.98

    // 浮力（float类型）
    if (p.type === 'float') {
      p.vx += Math.sin(p.life * 0.02) * 0.02
    }

    // 生命周期
    p.life++
    if (p.type !== 'float') {
      p.alpha *= (1 - p.decay)
      p.size *= 0.995
    } else {
      // float类型渐入渐出
      const fadeIn = Math.min(p.life / 30, 1)
      const fadeOut = Math.max(1 - (p.life - p.maxLife + 60) / 60, 0)
      p.alpha = (0.1 + Math.random() * 0.05) * fadeIn * fadeOut
    }

    // 绘制
    if (p.alpha > 0.01) {
      drawInkDrop(ctx, p)
    }

    // 移除死亡粒子
    if (p.life > p.maxLife || p.alpha < 0.005) {
      particles.splice(i, 1)
    }
  }

  // 检查动画完成
  if (props.trigger !== 'idle' && particles.length === 0) {
    emit('complete')
  }

  animId = requestAnimationFrame(render)
}

function resize() {
  if (!canvasRef.value) return
  const parent = canvasRef.value.parentElement
  if (!parent) return
  canvasRef.value.width = parent.clientWidth
  canvasRef.value.height = parent.clientHeight
}

// 外部触发接口
function triggerCollect(x: number, y: number) {
  createInkBurst(x, y, 40)
}

function triggerTransition() {
  if (!canvasRef.value) return
  createInkCurtain(canvasRef.value.width / 2, canvasRef.value.height / 2)
}

defineExpose({ triggerCollect, triggerTransition })

onMounted(() => {
  if (!canvasRef.value) return
  ctx = canvasRef.value.getContext('2d')
  resize()
  window.addEventListener('resize', resize)
  animId = requestAnimationFrame(render)
})

onUnmounted(() => {
  cancelAnimationFrame(animId)
  window.removeEventListener('resize', resize)
})

watch(() => props.sceneId, () => {
  // 场景切换时清空旧粒子
  particles = []
})
</script>

<template>
  <canvas
    ref="canvasRef"
    class="ink-particles"
    aria-hidden="true"
  />
</template>

<style scoped>
.ink-particles {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  mix-blend-mode: multiply;
  opacity: 0.6;
}
</style>
