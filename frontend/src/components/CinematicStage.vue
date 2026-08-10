<script setup lang="ts">
import { Application, Assets, Container, Graphics, Sprite, type Ticker } from 'pixi.js'
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { resolvePresentableConsequence } from '../domain/consequences'
import { getScenePresentation, resolveCharacterMode } from '../stage/presentation'
import type { AppliedConsequence } from '../types/game'

const props = defineProps<{
  sceneId: string
  activeNpcId?: string | null
  consequence?: AppliedConsequence | null
}>()

const host = ref<HTMLDivElement | null>(null)
const assetFailed = ref(false)
const portraitFailed = ref(false)
const presentation = computed(() => getScenePresentation(props.sceneId))
const activePortrait = computed(() => {
  if (!props.activeNpcId) return null
  return presentation.value?.portraits[props.activeNpcId] ?? null
})
const characterTreatment = computed(() =>
  resolveCharacterMode(props.sceneId, props.activeNpcId ?? ''),
)
const renderedConsequence = computed(() =>
  resolvePresentableConsequence(props.sceneId, props.consequence),
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
watch(activePortrait, () => {
  portraitFailed.value = false
})

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
    <div
      v-if="renderedConsequence"
      class="stage-consequence"
      :data-consequence-variant="renderedConsequence.variant"
      aria-hidden="true"
    >
      <span class="trunk-practical-light" />
      <div class="trunk-prop">
        <span class="trunk-cavity">
          <span class="modern-puppet">
            <i class="puppet-head" />
            <i class="puppet-torso" />
            <i class="puppet-arm puppet-arm-left" />
            <i class="puppet-arm puppet-arm-right" />
          </span>
        </span>
        <span class="trunk-front"><i /></span>
        <span class="trunk-lid"><i /></span>
        <span v-if="renderedConsequence.variant === 'legacy_suppressed'" class="trunk-latch" />
        <span v-if="renderedConsequence.variant === 'legacy_suppressed'" class="trunk-occlusion" />
        <span v-if="renderedConsequence.variant === 'legacy_carried'" class="paper-note">
          手艺不该被埋没
        </span>
      </div>
    </div>
    <Transition v-if="!portraitFailed" name="portrait-reveal">
      <img
        v-if="activePortrait && !portraitFailed"
        class="character-portrait"
        :data-character-treatment="characterTreatment"
        :src="activePortrait"
        alt=""
        aria-hidden="true"
        @error="portraitFailed = true"
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

.stage-consequence {
  position: absolute;
  z-index: 2;
  top: 60%;
  left: 76%;
  width: clamp(10rem, 19vw, 18rem);
  height: clamp(7rem, 19vh, 11rem);
  pointer-events: none;
  transform: translate(-50%, -50%);
  animation: consequence-settle 720ms var(--ease-cinema) both;
}

.trunk-practical-light {
  position: absolute;
  inset: -38% -22% -14% -24%;
  clip-path: polygon(18% 0, 100% 8%, 82% 100%, 0 76%);
  background: linear-gradient(118deg, transparent 5%, rgba(221, 164, 79, 0.3) 52%, transparent 94%);
  filter: blur(0.85rem);
}

.trunk-prop {
  position: absolute;
  inset: 8% 3% 2%;
  filter: drop-shadow(0.8rem 1.1rem 0.85rem rgba(0, 0, 0, 0.68));
  transform: perspective(28rem) rotateY(-6deg) rotateZ(-1deg);
}

.trunk-cavity,
.trunk-front,
.trunk-lid,
.trunk-occlusion {
  position: absolute;
  right: 2%;
  left: 2%;
  border: 1px solid rgba(59, 34, 17, 0.9);
}

.trunk-cavity {
  z-index: 1;
  top: 28%;
  bottom: 17%;
  overflow: hidden;
  background: linear-gradient(100deg, rgba(73, 39, 18, 0.78), transparent 38%), #100c08;
  box-shadow: inset 0 0 1.25rem rgba(0, 0, 0, 0.94);
}

.trunk-front {
  z-index: 4;
  right: 0;
  bottom: 0;
  left: 0;
  height: 40%;
  overflow: hidden;
  background:
    linear-gradient(92deg, rgba(35, 17, 8, 0.78), transparent 32%, rgba(237, 177, 93, 0.08)),
    linear-gradient(180deg, #5b341b, #2b180d);
  border-color: rgba(32, 16, 7, 0.96);
  box-shadow:
    inset 0 1px rgba(222, 158, 83, 0.25),
    inset 0 -0.7rem 1.1rem rgba(0, 0, 0, 0.42);
}

.trunk-front > i,
.trunk-lid > i {
  position: absolute;
  inset: 0;
  opacity: 0.42;
  background: repeating-linear-gradient(
    3deg,
    transparent 0 0.55rem,
    rgba(239, 185, 110, 0.12) 0.6rem 0.66rem,
    transparent 0.7rem 1.15rem
  );
}

.trunk-lid {
  z-index: 3;
  top: 15%;
  height: 24%;
  overflow: hidden;
  background:
    linear-gradient(100deg, rgba(25, 13, 7, 0.66), transparent 45%),
    linear-gradient(180deg, #724323, #351e10);
  box-shadow:
    inset 0 1px rgba(234, 183, 108, 0.22),
    0 0.55rem 0.65rem rgba(0, 0, 0, 0.5);
  transform-origin: left bottom;
}

.modern-puppet {
  position: absolute;
  z-index: 2;
  top: 2%;
  left: 52%;
  width: 28%;
  height: 92%;
  color: #18140f;
  filter: drop-shadow(0 0 0.25rem rgba(231, 181, 105, 0.32));
  transform: rotate(4deg);
}

.modern-puppet > i {
  position: absolute;
  display: block;
  background: currentColor;
}

.puppet-head {
  top: 0;
  left: 34%;
  width: 31%;
  height: 18%;
  clip-path: polygon(18% 0, 80% 4%, 100% 38%, 72% 100%, 20% 91%, 0 42%);
}

.puppet-torso {
  top: 16%;
  left: 25%;
  width: 50%;
  height: 65%;
  clip-path: polygon(18% 0, 82% 0, 100% 100%, 0 100%);
}

.puppet-torso::after {
  position: absolute;
  top: 8%;
  left: 42%;
  width: 16%;
  height: 82%;
  content: '';
  background: rgba(222, 182, 116, 0.52);
  clip-path: polygon(50% 0, 100% 18%, 65% 100%, 30% 100%, 0 18%);
}

.puppet-arm {
  top: 24%;
  width: 14%;
  height: 55%;
  transform-origin: top;
}

.puppet-arm-left {
  left: 12%;
  transform: rotate(17deg);
}

.puppet-arm-right {
  right: 12%;
  transform: rotate(-19deg);
}

.trunk-latch {
  position: absolute;
  z-index: 8;
  bottom: 23%;
  left: 47%;
  width: 9%;
  height: 24%;
  border: 1px solid rgba(32, 27, 20, 0.94);
  background: linear-gradient(90deg, #574b36, #a28d63 46%, #423726);
  box-shadow: 0.18rem 0.28rem 0.3rem rgba(0, 0, 0, 0.62);
}

.trunk-occlusion {
  z-index: 5;
  top: 30%;
  bottom: 29%;
  border: 0;
  background: linear-gradient(180deg, rgba(19, 19, 17, 0.88), rgba(10, 10, 9, 0.55));
  clip-path: polygon(0 8%, 100% 0, 100% 72%, 0 100%);
}

.paper-note {
  position: absolute;
  z-index: 7;
  top: 41%;
  left: 8%;
  width: 44%;
  padding: 0.38rem 0.5rem 0.34rem;
  color: rgba(55, 35, 20, 0.92);
  background:
    repeating-linear-gradient(2deg, transparent 0 0.72rem, rgba(84, 55, 28, 0.1) 0.76rem), #d9c49d;
  box-shadow: 0.25rem 0.4rem 0.4rem rgba(0, 0, 0, 0.48);
  font-family: 'Noto Serif SC', serif;
  font-size: clamp(0.45rem, 0.62vw, 0.63rem);
  letter-spacing: 0.08em;
  line-height: 1.55;
  transform: rotate(-5deg);
}

[data-consequence-variant='legacy_carried'] .trunk-lid {
  transform: translateY(-42%) rotate(-13deg) skewX(-2deg);
}

[data-consequence-variant='legacy_carried'] .modern-puppet {
  opacity: 0.98;
}

[data-consequence-variant='legacy_suppressed'] .trunk-practical-light {
  opacity: 0.5;
  background: linear-gradient(
    118deg,
    transparent 5%,
    rgba(118, 133, 126, 0.21) 52%,
    transparent 94%
  );
}

[data-consequence-variant='legacy_suppressed'] .trunk-prop {
  filter: drop-shadow(0.8rem 1.1rem 0.85rem rgba(0, 0, 0, 0.82)) saturate(0.64);
}

[data-consequence-variant='legacy_suppressed'] .trunk-lid {
  z-index: 6;
  top: 25%;
  height: 31%;
  transform: rotate(-2deg);
}

[data-consequence-variant='legacy_suppressed'] .modern-puppet {
  opacity: 0.24;
  transform: translateY(15%) rotate(8deg);
}

.character-portrait {
  position: absolute;
  z-index: 3;
  right: clamp(-2.5rem, -1vw, -0.5rem);
  bottom: -1%;
  width: min(31vw, 27rem);
  height: 96%;
  object-fit: contain;
  object-position: bottom right;
  opacity: 1;
  filter: drop-shadow(-1.25rem 1.5rem 1.6rem rgba(0, 0, 0, 0.52))
    drop-shadow(-0.15rem 0 0.45rem rgba(224, 177, 103, 0.18));
  mask-image: linear-gradient(to bottom, #000 0%, #000 88%, transparent 100%);
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

@keyframes consequence-settle {
  from {
    opacity: 0;
    transform: translate(-47%, -46%) scale(0.97);
  }
  to {
    opacity: 1;
    transform: translate(-50%, -50%) scale(1);
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
  .stage-consequence {
    top: 66%;
    left: 67%;
    width: clamp(9rem, 43vw, 15rem);
    height: clamp(6.5rem, 17vh, 9.5rem);
  }

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

  .stage-consequence {
    animation: none;
  }
}
</style>
