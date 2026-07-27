<script setup lang="ts">
import { Application, Assets, Container, Graphics, Sprite, type Ticker } from 'pixi.js'
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { getScenePresentation } from '../stage/presentation'

const props = defineProps<{
  sceneId: string
  activeNpcId?: string | null
}>()

const host = ref<HTMLDivElement | null>(null)
const assetFailed = ref(false)
const presentation = computed(() => getScenePresentation(props.sceneId))
const activePortrait = computed(() => {
  if (!props.activeNpcId) return null
  return presentation.value?.portraits[props.activeNpcId] ?? null
})
const characterTreatment = computed(() =>
  props.sceneId === 'scene_2089' && props.activeNpcId === 'xiaoyu' ? 'projection' : 'solid',
)
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
  assetFailed.value = false
  await nextTick()
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

  let texture
  try {
    texture = await Assets.load(scene.background)
  } catch {
    if (currentGeneration === generation && app === nextApp) {
      assetFailed.value = true
      destroyStage()
    }
    return
  }
  if (currentGeneration !== generation || app !== nextApp) return

  const world = new Container()
  const background = new Sprite(texture)
  world.addChild(background)
  nextApp.stage.addChild(world)

  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  const lowEffects =
    reducedMotion ||
    window.matchMedia('(max-width: 900px)').matches ||
    (navigator.hardwareConcurrency > 0 && navigator.hardwareConcurrency <= 4)
  nextApp.ticker.maxFPS = lowEffects ? 30 : 60

  const dust = Array.from({ length: lowEffects ? 14 : 26 }, (_, index) => {
    const mote = new Graphics()
      .circle(0, 0, 0.7 + (index % 4) * 0.35)
      .fill({ color: 0xe6c084, alpha: 0.08 + (index % 5) * 0.025 })
    mote.x = ((index * 137.5) % 1000) / 1000
    mote.y = ((index * 83.7) % 1000) / 1000
    nextApp.stage.addChild(mote)
    return mote
  })

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

  const syncPlayback = () => {
    if (document.hidden || reducedMotion) {
      nextApp.ticker.stop()
    } else {
      nextApp.ticker.start()
    }
  }

  layout()
  resizeObserver = new ResizeObserver(layout)
  resizeObserver.observe(target)
  target.addEventListener('pointermove', onPointerMove, { passive: true })
  document.addEventListener('visibilitychange', syncPlayback)
  nextApp.ticker.add(tick)
  syncPlayback()
  cleanupStage = () => {
    target.removeEventListener('pointermove', onPointerMove)
    document.removeEventListener('visibilitychange', syncPlayback)
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
    <div v-if="presentation && !assetFailed" ref="host" class="canvas-host" />
    <div v-else class="legacy-stage">
      <slot />
    </div>
    <div class="stage-grade" aria-hidden="true" />
    <div class="stage-vignette" aria-hidden="true" />
    <div class="stage-grain" aria-hidden="true" />
    <Transition name="portrait-reveal">
      <img
        v-if="activePortrait"
        class="character-portrait"
        :data-character-treatment="characterTreatment"
        :src="activePortrait"
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

.palette-rail .stage-grade {
  background:
    radial-gradient(circle at 70% 35%, rgba(221, 153, 68, 0.13), transparent 24%),
    linear-gradient(112deg, rgba(9, 18, 14, 0.58) 0%, rgba(40, 54, 42, 0.12) 48%, transparent 76%),
    linear-gradient(180deg, rgba(6, 10, 8, 0.2), transparent 34%, rgba(4, 7, 5, 0.64));
}

.palette-rain .stage-grade {
  background:
    radial-gradient(circle at 42% 69%, rgba(213, 139, 58, 0.1), transparent 22%),
    linear-gradient(118deg, rgba(6, 20, 34, 0.58) 0%, rgba(24, 62, 87, 0.12) 55%, transparent 78%),
    linear-gradient(180deg, rgba(8, 27, 43, 0.18), transparent 30%, rgba(3, 8, 13, 0.7));
}

.palette-ceremony .stage-grade {
  background:
    radial-gradient(circle at 52% 42%, rgba(255, 238, 188, 0.16), transparent 38%),
    linear-gradient(
      110deg,
      rgba(36, 16, 12, 0.32) 0%,
      transparent 31%,
      rgba(124, 22, 22, 0.08) 88%
    ),
    linear-gradient(180deg, rgba(255, 245, 218, 0.04), transparent 48%, rgba(15, 8, 7, 0.42));
  mix-blend-mode: soft-light;
}

.palette-memory .stage-grade {
  background:
    radial-gradient(circle at 50% 48%, rgba(225, 145, 54, 0.13), transparent 17%),
    radial-gradient(circle at 31% 38%, rgba(38, 196, 209, 0.1), transparent 31%),
    radial-gradient(circle at 72% 42%, rgba(116, 67, 196, 0.14), transparent 36%),
    linear-gradient(180deg, rgba(3, 10, 18, 0.16), transparent 42%, rgba(3, 4, 12, 0.62));
  mix-blend-mode: screen;
}

.stage-vignette {
  box-shadow:
    inset 0 0 15vw 4vw rgba(0, 0, 0, 0.72),
    inset 0 -10rem 9rem rgba(0, 0, 0, 0.52);
}

.palette-rail .stage-vignette {
  box-shadow:
    inset 0 0 17vw 5vw rgba(1, 7, 4, 0.75),
    inset 0 -11rem 10rem rgba(0, 0, 0, 0.58);
}

.palette-rain .stage-vignette {
  box-shadow:
    inset 0 0 19vw 6vw rgba(0, 4, 10, 0.8),
    inset 0 -12rem 10rem rgba(0, 2, 7, 0.68);
}

.palette-ceremony .stage-vignette {
  box-shadow:
    inset 0 0 10vw 2vw rgba(25, 10, 8, 0.42),
    inset 0 -8rem 8rem rgba(8, 4, 3, 0.38);
}

.palette-memory .stage-vignette {
  box-shadow:
    inset 0 0 16vw 4vw rgba(0, 2, 10, 0.72),
    inset 0 -10rem 9rem rgba(1, 1, 9, 0.6);
}

.stage-grain {
  opacity: 0.045;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 180 180' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.8' numOctaves='3' stitchTiles='stitchTiles'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='.7'/%3E%3C/svg%3E");
  animation: grain 320ms steps(2) infinite;
}

.character-portrait {
  position: absolute;
  right: clamp(-2.5rem, -1vw, -0.5rem);
  bottom: -2vh;
  width: min(34vw, 30rem);
  height: 88vh;
  object-fit: contain;
  object-position: bottom right;
  opacity: 1;
  filter: drop-shadow(-1.25rem 1.5rem 1.6rem rgba(0, 0, 0, 0.52))
    drop-shadow(-0.15rem 0 0.45rem rgba(224, 177, 103, 0.18));
  mask-image: linear-gradient(to bottom, #000 0%, #000 88%, transparent 100%);
  pointer-events: none;
}

.character-portrait[data-character-treatment='projection'] {
  opacity: 0.92;
  filter: drop-shadow(-1rem 1.4rem 1.5rem rgba(0, 0, 0, 0.46))
    drop-shadow(0 0 0.65rem rgba(96, 198, 221, 0.24))
    drop-shadow(0 0 1.15rem rgba(139, 92, 196, 0.2));
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
    transform 760ms var(--ease-cinema);
}

.portrait-reveal-enter-from,
.portrait-reveal-leave-to {
  opacity: 0;
  transform: translateX(2rem);
}

@media (max-aspect-ratio: 4/5) {
  .character-portrait {
    right: -3.5rem;
    bottom: 20vh;
    width: min(68vw, 24rem);
    height: 61vh;
  }
}

@media (prefers-reduced-motion: reduce) {
  .stage-grain {
    animation: none;
  }

  .portrait-reveal-enter-active,
  .portrait-reveal-leave-active {
    transition: none;
  }
}
</style>
