<script setup lang="ts">
import { Application, Assets, Container, Graphics, Sprite, type Ticker } from 'pixi.js'
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { getScenePresentation } from '../stage/presentation'

const props = defineProps<{
  sceneId: string
  activeNpcId?: string | null
}>()

const host = ref<HTMLDivElement | null>(null)
const presentation = computed(() => getScenePresentation(props.sceneId))
let app: Application | null = null
let resizeObserver: ResizeObserver | null = null
let generation = 0
let cleanupStage: (() => void) | null = null

const destroyStage = () => {
  generation += 1
  cleanupStage?.()
  cleanupStage = null
  resizeObserver?.disconnect()
  resizeObserver = null
  if (app) {
    app.destroy(true, { children: true })
    app = null
  }
}

const buildStage = async () => {
  destroyStage()
  const target = host.value
  const scene = presentation.value
  if (!target || !scene) return

  const currentGeneration = generation
  const nextApp = new Application()
  await nextApp.init({
    width: Math.max(target.clientWidth, 1),
    height: Math.max(target.clientHeight, 1),
    backgroundAlpha: 0,
    antialias: true,
    autoDensity: true,
    resolution: Math.min(window.devicePixelRatio || 1, 1.5),
    powerPreference: 'high-performance',
  })

  if (currentGeneration !== generation || !host.value) {
    nextApp.destroy(true, { children: true })
    return
  }

  app = nextApp
  nextApp.canvas.className = 'cinematic-canvas'
  nextApp.canvas.setAttribute('aria-hidden', 'true')
  target.replaceChildren(nextApp.canvas)

  const texture = await Assets.load(scene.background)
  if (currentGeneration !== generation || app !== nextApp) return

  const world = new Container()
  const background = new Sprite(texture)
  world.addChild(background)
  nextApp.stage.addChild(world)

  const dust = Array.from({ length: 26 }, (_, index) => {
    const mote = new Graphics()
      .circle(0, 0, 0.7 + (index % 4) * 0.35)
      .fill({ color: 0xe6c084, alpha: 0.08 + (index % 5) * 0.025 })
    mote.x = ((index * 137.5) % 1000) / 1000
    mote.y = ((index * 83.7) % 1000) / 1000
    nextApp.stage.addChild(mote)
    return mote
  })

  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  let pointerX = 0
  let pointerY = 0
  let elapsed = 0

  const layout = () => {
    if (!app || app !== nextApp || !host.value) return
    const width = host.value.clientWidth
    const height = host.value.clientHeight
    nextApp.renderer.resize(Math.max(width, 1), Math.max(height, 1))
    const scale = Math.max(width / texture.width, height / texture.height) * 1.035
    background.scale.set(scale)
    const mobile = width / Math.max(height, 1) < 0.85
    const [focusX, focusY] = mobile ? scene.composition.mobileFocus : scene.composition.desktopFocus
    background.x = width * 0.5 - texture.width * scale * focusX
    background.y = height * 0.5 - texture.height * scale * focusY
    dust.forEach((mote, index) => {
      mote.x = (((index * 137.5) % 1000) / 1000) * width
      mote.y = (((index * 83.7) % 1000) / 1000) * height
    })
  }

  const onPointerMove = (event: PointerEvent) => {
    if (reducedMotion || !host.value) return
    const rect = host.value.getBoundingClientRect()
    pointerX = (event.clientX - rect.left) / rect.width - 0.5
    pointerY = (event.clientY - rect.top) / rect.height - 0.5
  }

  const tick = (ticker: Ticker) => {
    if (reducedMotion) return
    elapsed += ticker.deltaMS
    world.x += (pointerX * -10 - world.x) * 0.025
    world.y += (pointerY * -6 - world.y) * 0.025
    dust.forEach((mote, index) => {
      mote.y -= ticker.deltaMS * (0.002 + (index % 3) * 0.001)
      mote.alpha = 0.35 + Math.sin(elapsed * 0.0005 + index) * 0.2
      if (mote.y < -4) mote.y = nextApp.screen.height + 4
    })
  }

  layout()
  resizeObserver = new ResizeObserver(layout)
  resizeObserver.observe(target)
  target.addEventListener('pointermove', onPointerMove, { passive: true })
  nextApp.ticker.add(tick)
  cleanupStage = () => {
    target.removeEventListener('pointermove', onPointerMove)
    nextApp.ticker.remove(tick)
  }
}

watch(
  () => props.sceneId,
  () => void buildStage(),
  { flush: 'post' },
)

onMounted(() => void buildStage())
onBeforeUnmount(destroyStage)
</script>

<template>
  <figure
    class="cinematic-stage"
    :class="`palette-${presentation?.palette ?? 'legacy'}`"
    role="img"
    :aria-label="presentation?.alt || '记忆场景'"
  >
    <div v-if="presentation" ref="host" class="canvas-host" />
    <div v-else class="legacy-stage">
      <slot />
    </div>
    <div class="stage-grade" aria-hidden="true" />
    <div class="stage-vignette" aria-hidden="true" />
    <div class="stage-grain" aria-hidden="true" />
    <Transition name="portrait-reveal">
      <img
        v-if="
          presentation?.portrait && activeNpcId && presentation.portraitNpcIds.includes(activeNpcId)
        "
        class="character-portrait"
        :src="presentation.portrait"
        alt=""
        aria-hidden="true"
      />
    </Transition>
  </figure>
</template>

<style scoped>
.cinematic-stage,
.canvas-host,
.legacy-stage {
  position: absolute;
  inset: 0;
  margin: 0;
  overflow: hidden;
}

.canvas-host :deep(.cinematic-canvas) {
  display: block;
  width: 100%;
  height: 100%;
}

.legacy-stage :deep(.scene-illustration),
.legacy-stage :deep(svg),
.legacy-stage :deep(img) {
  width: 100%;
  height: 100%;
}

.legacy-stage :deep(svg),
.legacy-stage :deep(img) {
  object-fit: cover;
}

.stage-grade,
.stage-vignette,
.stage-grain {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.stage-grade {
  background:
    linear-gradient(110deg, rgba(9, 9, 8, 0.52) 0%, transparent 38%, rgba(8, 7, 6, 0.16) 65%),
    linear-gradient(180deg, rgba(7, 8, 8, 0.28), transparent 32%, rgba(6, 6, 6, 0.56));
  mix-blend-mode: multiply;
}

.palette-amber .stage-grade {
  background:
    radial-gradient(circle at 33% 42%, rgba(212, 139, 48, 0.12), transparent 28%),
    linear-gradient(104deg, rgba(8, 8, 7, 0.54) 0%, transparent 37%, rgba(31, 19, 9, 0.1) 70%),
    linear-gradient(180deg, rgba(7, 8, 8, 0.2), transparent 35%, rgba(5, 5, 5, 0.62));
}

.stage-vignette {
  box-shadow:
    inset 0 0 15vw 4vw rgba(0, 0, 0, 0.72),
    inset 0 -10rem 9rem rgba(0, 0, 0, 0.52);
}

.stage-grain {
  opacity: 0.045;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 180 180' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.8' numOctaves='3' stitchTiles='stitchTiles'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='.7'/%3E%3C/svg%3E");
  animation: grain 320ms steps(2) infinite;
}

.character-portrait {
  position: absolute;
  right: clamp(-5rem, -2vw, -1rem);
  bottom: -7vh;
  width: min(38vw, 34rem);
  height: 92vh;
  object-fit: contain;
  object-position: bottom right;
  opacity: 0.92;
  filter: contrast(1.04) saturate(0.82);
  mask-image: linear-gradient(to bottom, black 66%, transparent 100%);
  pointer-events: none;
}

@keyframes grain {
  0% {
    transform: translate(0, 0);
  }
  50% {
    transform: translate(-1%, 1%);
  }
}

.portrait-reveal-enter-active,
.portrait-reveal-leave-active {
  transition:
    opacity 520ms var(--ease-cinema),
    transform 760ms var(--ease-cinema),
    filter 520ms ease;
}

.portrait-reveal-enter-from,
.portrait-reveal-leave-to {
  opacity: 0;
  filter: blur(8px);
  transform: translateX(3rem);
}

@media (max-aspect-ratio: 4/5) {
  .character-portrait {
    right: -8rem;
    bottom: 17vh;
    width: min(75vw, 29rem);
    height: 67vh;
    opacity: 0.68;
  }
}
</style>
