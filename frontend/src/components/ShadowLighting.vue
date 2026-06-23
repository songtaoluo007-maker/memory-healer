<script setup lang="ts">
/**
 * 皮影戏光影引擎 - Canvas实时渲染
 * 烛光摇曳 + 幕布透光 + 皮影剪影
 */
import { ref, onMounted, onUnmounted, watch } from 'vue'

const props = defineProps<{
  sceneId: string
  intensity?: number // 0-1, 光影强度
}>()

const canvasRef = ref<HTMLCanvasElement | null>(null)
let ctx: CanvasRenderingContext2D | null = null
let animId = 0
let time = 0

// 烛光参数
const candles = [
  { x: 0.15, y: 0.3, size: 1.0, phase: 0 },
  { x: 0.85, y: 0.25, size: 0.8, phase: 1.5 },
  { x: 0.5, y: 0.1, size: 0.6, phase: 3.0 },
]

// 皮影剪影数据（简化的人物轮廓）
const silhouettePaths: Record<string, Array<{ x: number; y: number; scale: number }>> = {
  scene_1972: [
    { x: 0.3, y: 0.5, scale: 0.8 },
    { x: 0.7, y: 0.55, scale: 0.6 },
  ],
  scene_1990: [
    { x: 0.2, y: 0.45, scale: 0.7 },
    { x: 0.5, y: 0.5, scale: 0.9 },
    { x: 0.8, y: 0.48, scale: 0.5 },
  ],
  scene_2024: [
    { x: 0.4, y: 0.5, scale: 0.7 },
    { x: 0.6, y: 0.52, scale: 0.65 },
  ],
  scene_2050: [
    { x: 0.5, y: 0.4, scale: 1.0 },
  ],
  scene_2089: [
    { x: 0.5, y: 0.5, scale: 0.85 },
  ],
}

// 烛光火焰绘制
function drawFlame(ctx: CanvasRenderingContext2D, x: number, y: number, size: number, t: number) {
  const flicker = Math.sin(t * 3.7) * 0.15 + Math.sin(t * 7.3) * 0.08 + Math.cos(t * 11.1) * 0.05
  const sway = Math.sin(t * 2.1) * 3 + Math.cos(t * 5.3) * 1.5

  ctx.save()
  ctx.translate(x + sway, y)

  // 外层光晕
  const glowRadius = size * (60 + flicker * 30)
  const glow = ctx.createRadialGradient(0, 0, 0, 0, 0, glowRadius)
  glow.addColorStop(0, `rgba(255, 200, 80, ${0.12 * (props.intensity || 0.6)})`)
  glow.addColorStop(0.3, `rgba(255, 160, 40, ${0.06 * (props.intensity || 0.6)})`)
  glow.addColorStop(0.7, `rgba(255, 100, 20, ${0.02 * (props.intensity || 0.6)})`)
  glow.addColorStop(1, 'transparent')
  ctx.fillStyle = glow
  ctx.fillRect(-glowRadius, -glowRadius, glowRadius * 2, glowRadius * 2)

  // 火焰主体
  const flameH = size * (18 + flicker * 8)
  const flameW = size * (6 + flicker * 2)
  ctx.beginPath()
  ctx.moveTo(0, -flameH)
  ctx.bezierCurveTo(
    flameW * 0.5, -flameH * 0.6,
    flameW, -flameH * 0.2,
    flameW * 0.3, flameH * 0.3
  )
  ctx.bezierCurveTo(
    flameW * 0.1, flameH * 0.1,
    -flameW * 0.1, flameH * 0.1,
    -flameW * 0.3, flameH * 0.3
  )
  ctx.bezierCurveTo(
    -flameW, -flameH * 0.2,
    -flameW * 0.5, -flameH * 0.6,
    0, -flameH
  )
  const flameGrad = ctx.createLinearGradient(0, -flameH, 0, flameH * 0.3)
  flameGrad.addColorStop(0, 'rgba(255, 240, 200, 0.9)')
  flameGrad.addColorStop(0.3, 'rgba(255, 180, 60, 0.7)')
  flameGrad.addColorStop(0.7, 'rgba(255, 100, 20, 0.4)')
  flameGrad.addColorStop(1, 'rgba(200, 60, 10, 0)')
  ctx.fillStyle = flameGrad
  ctx.fill()

  // 灯芯
  ctx.beginPath()
  ctx.moveTo(-1, flameH * 0.3)
  ctx.lineTo(1, flameH * 0.3)
  ctx.lineTo(0.5, -flameH * 0.1)
  ctx.lineTo(-0.5, -flameH * 0.1)
  ctx.fillStyle = 'rgba(60, 40, 20, 0.8)'
  ctx.fill()

  ctx.restore()
}

// 皮影人物绘制
function drawSilhouette(ctx: CanvasRenderingContext2D, x: number, y: number, scale: number, t: number) {
  const sway = Math.sin(t * 0.8 + x) * 2

  ctx.save()
  ctx.translate(x + sway, y)
  ctx.scale(scale, scale)

  // 人物剪影（简化版皮影人偶）
  ctx.beginPath()
  // 头
  ctx.arc(0, -60, 12, 0, Math.PI * 2)
  // 身体
  ctx.moveTo(-10, -48)
  ctx.lineTo(-15, -10)
  ctx.lineTo(-25, 30)
  ctx.lineTo(-15, 30)
  ctx.lineTo(-8, 5)
  ctx.lineTo(8, 5)
  ctx.lineTo(15, 30)
  ctx.lineTo(25, 30)
  ctx.lineTo(15, -10)
  ctx.lineTo(10, -48)
  // 手臂
  ctx.moveTo(-10, -35)
  ctx.lineTo(-30, -15 + Math.sin(t * 1.2) * 3)
  ctx.lineTo(-35, 0 + Math.sin(t * 1.5) * 2)
  ctx.moveTo(10, -35)
  ctx.lineTo(30, -15 + Math.cos(t * 1.3) * 3)
  ctx.lineTo(35, 0 + Math.cos(t * 1.6) * 2)

  ctx.fillStyle = 'rgba(20, 15, 10, 0.35)'
  ctx.fill()

  // 关节连接线（皮影特色）
  ctx.strokeStyle = 'rgba(232, 180, 80, 0.08)'
  ctx.lineWidth = 1
  ctx.beginPath()
  ctx.arc(0, -35, 3, 0, Math.PI * 2) // 颈关节
  ctx.moveTo(-10, -35)
  ctx.arc(-10, -35, 2, 0, Math.PI * 2) // 肩关节
  ctx.moveTo(10, -35)
  ctx.arc(10, -35, 2, 0, Math.PI * 2)
  ctx.stroke()

  ctx.restore()
}

// 幕布纹理
function drawCurtainTexture(ctx: CanvasRenderingContext2D, w: number, h: number, t: number) {
  // 横向幕布条纹
  ctx.strokeStyle = `rgba(200, 160, 80, ${0.02 + Math.sin(t * 0.5) * 0.01})`
  ctx.lineWidth = 1
  for (let y = 0; y < h; y += 40) {
    const wave = Math.sin(y * 0.01 + t * 0.3) * 3
    ctx.beginPath()
    ctx.moveTo(0, y + wave)
    ctx.lineTo(w, y + wave * 0.7)
    ctx.stroke()
  }
}

function render() {
  if (!ctx || !canvasRef.value) return
  const w = canvasRef.value.width
  const h = canvasRef.value.height
  const t = time

  ctx.clearRect(0, 0, w, h)

  // 幕布纹理
  drawCurtainTexture(ctx, w, h, t)

  // 烛光
  for (const c of candles) {
    drawFlame(ctx, c.x * w, c.y * h, c.size, t + c.phase)
  }

  // 皮影人物
  const silhouettes = silhouettePaths[props.sceneId] || silhouettePaths.scene_1972
  for (const s of silhouettes) {
    drawSilhouette(ctx, s.x * w, s.y * h, s.scale * (w / 800), t)
  }

  // 光线穿透效果（幕布透光）
  const lightX = w * 0.5 + Math.sin(t * 0.7) * w * 0.1
  const lightY = h * 0.3 + Math.cos(t * 0.5) * h * 0.05
  const lightGrad = ctx.createRadialGradient(lightX, lightY, 0, lightX, lightY, w * 0.4)
  lightGrad.addColorStop(0, `rgba(255, 220, 150, ${0.04 * (props.intensity || 0.6)})`)
  lightGrad.addColorStop(0.5, `rgba(255, 180, 100, ${0.02 * (props.intensity || 0.6)})`)
  lightGrad.addColorStop(1, 'transparent')
  ctx.fillStyle = lightGrad
  ctx.fillRect(0, 0, w, h)

  time += 0.016
  animId = requestAnimationFrame(render)
}

function resize() {
  if (!canvasRef.value) return
  const parent = canvasRef.value.parentElement
  if (!parent) return
  canvasRef.value.width = parent.clientWidth
  canvasRef.value.height = parent.clientHeight
}

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
  time = 0
})
</script>

<template>
  <canvas
    ref="canvasRef"
    class="shadow-lighting"
    aria-hidden="true"
  />
</template>

<style scoped>
.shadow-lighting {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  mix-blend-mode: screen;
  opacity: 0.8;
}
</style>
