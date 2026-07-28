<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import endingBackdrop from '../assets/cinematic/scene-1972-xian-alley.png'
import chenPortrait from '../assets/cinematic/chen-shouyi-1972-solid.webp'
import { useGameState } from '../composables/useGameState'
import { useVoiceRouteLifecycle } from '../composables/useScene'
import { useVoicePlayback } from '../composables/useVoicePlayback'
import type { EndingType } from '../types/game'

const props = defineProps<{
  endingType: EndingType
  voicePlayback?: ReturnType<typeof useVoicePlayback>
}>()

const emit = defineEmits<{
  restart: []
}>()

const { collectedCount, totalFragments } = useGameState()
const voice = props.voicePlayback ?? useVoicePlayback()
useVoiceRouteLifecycle(voice)
const phase = ref(0)
const shareStatus = ref('')
const timers: number[] = []

onMounted(() => {
  timers.push(
    window.setTimeout(() => (phase.value = 1), 400),
    window.setTimeout(() => (phase.value = 2), 1700),
    window.setTimeout(() => (phase.value = 3), 3300),
  )
})

onUnmounted(() => timers.forEach(window.clearTimeout))

const endingData = computed(() => {
  const endings = {
    hope: {
      serial: 'ENDING / 01',
      mark: '光',
      title: '光',
      subtitle: '记忆不是数据，而是仍有温度的重逢。',
      mood: '温暖 · 感动 · 希望',
      description: `所有记忆碎片收集完毕。陈爷爷在梦中重新走过了1972年的西安老巷、2024年的深圳城中村，最终在2089年的实验室里睁开了眼睛。

他看着小雨，眼眶湿润：“小雨……爷爷想起来了。那个孙悟空的皮影人偶……爷爷还没送给你。”

小雨紧紧握住爷爷的手，泪水滑落。

那些被遗忘的光影、刻刀与锣鼓声回来了。不是作为冰冷的数据，而是作为温暖的记忆。`,
    },
    bittersweet: {
      serial: 'ENDING / 02',
      mark: '温',
      title: '余温',
      subtitle: '有些名字被忘记了，手掌却还记得它的形状。',
      mood: '苦涩 · 温暖 · 遗憾',
      description: `部分记忆碎片被找回。陈爷爷在梦中看到模糊的画面——1972年的皮影戏台，那把刻着“陈”字的刻刀。

他醒来后，沉默了很久。

“我好像……想起了什么。但又不太清楚。”

小雨把孙悟空的皮影人偶放在爷爷手心。爷爷的手指摩挲着人偶，嘴角微微上扬。

虽然记忆不再完整，但那份温暖还在。`,
    },
    tragic: {
      serial: 'ENDING / 03',
      mark: '散',
      title: '消散',
      subtitle: '记忆沉入黑暗，身体仍替灵魂守住最后的习惯。',
      mood: '悲伤 · 遗憾 · 深沉',
      description: `记忆碎片太少，修复失败了。

陈爷爷在梦中看到一些碎片——光影、锣鼓、一把刻刀。但它们太模糊，像水中的倒影，一碰就散。

他醒来后，看着小雨，眼神空洞。

“你是……谁？”

小雨没有哭。她把孙悟空的皮影人偶放在爷爷面前：“爷爷，我是小雨。我来看你了。”

爷爷接过人偶，手指下意识地摩挲着。他不记得了，但他的手记得。`,
    },
    legacy: {
      serial: 'ENDING / 04',
      mark: '承',
      title: '传承',
      subtitle: '一个人的记忆，最终成为所有人共同守护的光。',
      mood: '荣耀 · 传承 · 圆满',
      description: `跨越五个时代的记忆被完整修复。

从1972年西安老巷的皮影戏台，到1990年深圳火车站的绿皮火车，到2024年城中村的刻刀、2050年颁奖典礼的水晶奖杯，再到2089年实验室的全息投影——陈守义的一生，如同一出完整的皮影戏。

小雨在颁奖典礼上说：“爷爷的记忆不只属于我们家。它属于所有热爱皮影戏的人，属于所有不该被遗忘的手艺。”

全息投影中，年轻的陈守义正在表演《三英战吕布》。掌声响起。

记忆修复成功了。不只是修复，而是传承。`,
    },
  }
  return endings[props.endingType]
})

const fragmentsPercent = computed(() => {
  if (!totalFragments.value) return 0
  return Math.round((collectedCount.value / totalFragments.value) * 100)
})

const shareEnding = async () => {
  const text = `我在《拾忆》中达成了「${endingData.value.title}」结局，记忆完整度 ${fragmentsPercent.value}%。`
  try {
    if (navigator.share) {
      await navigator.share({ title: '拾忆 · 记忆修复师', text, url: window.location.href })
      shareStatus.value = '结局已分享。'
    } else {
      await navigator.clipboard.writeText(text)
      shareStatus.value = '结局文字已复制。'
    }
  } catch {
    shareStatus.value = '分享已取消。'
  }
}
</script>

<template>
  <main class="ending" :class="`ending-${endingType}`" aria-labelledby="ending-title">
    <img class="ending-backdrop" :src="endingBackdrop" alt="" aria-hidden="true" />
    <div class="ending-grade" aria-hidden="true" />
    <img
      v-if="endingType === 'hope' || endingType === 'legacy'"
      class="ending-portrait"
      :src="chenPortrait"
      alt=""
      aria-hidden="true"
    />

    <header class="ending-topline">
      <span>拾忆 / MEMORY RESTORATION RESULT</span>
      <strong>{{ endingData.serial }}</strong>
    </header>

    <section class="ending-heading" :class="{ visible: phase >= 1 }">
      <span class="ending-serial">{{ endingData.serial }}</span>
      <div class="ending-mark" aria-hidden="true">{{ endingData.mark }}</div>
      <h1 id="ending-title">{{ endingData.title }}</h1>
      <p>{{ endingData.subtitle }}</p>
      <span class="ending-mood">{{ endingData.mood }}</span>
    </section>

    <section class="ending-story" :class="{ visible: phase >= 2 }" aria-label="结局故事">
      <span class="story-label">FINAL MEMORY TRANSCRIPT</span>
      <div class="story-scroll">
        <p v-for="line in endingData.description.split('\n\n')" :key="line">{{ line }}</p>
      </div>
    </section>

    <section class="ending-result" :class="{ visible: phase >= 3 }" aria-label="修复结果">
      <div class="stat">
        <span>ARCHIVED FRAGMENTS</span>
        <strong>{{ String(collectedCount).padStart(2, '0') }}</strong>
        <i>/ {{ String(totalFragments).padStart(2, '0') }}</i>
      </div>
      <div class="stat">
        <span>MEMORY INTEGRITY</span>
        <strong>{{ String(fragmentsPercent).padStart(2, '0') }}</strong>
        <i>%</i>
      </div>
      <div class="ending-actions">
        <button type="button" @click="emit('restart')">
          <span>返回首页</span><span aria-hidden="true">→</span>
        </button>
        <button type="button" @click="shareEnding">
          <span>分享结局</span><span aria-hidden="true">↗</span>
        </button>
      </div>
      <p v-if="shareStatus" role="status">{{ shareStatus }}</p>
    </section>

    <footer class="ending-footer">
      <span>END OF MEMORY 001</span><i /><span>拾回所爱，留下所忆</span>
    </footer>
  </main>
</template>

<style scoped>
.ending {
  position: fixed;
  z-index: 300;
  inset: 0;
  overflow: hidden;
  color: var(--paper-100);
  background: #030403;
}

.ending-backdrop,
.ending-grade,
.ending-portrait {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}

.ending-backdrop {
  object-fit: cover;
  object-position: center;
  filter: saturate(0.56) contrast(1.12);
}

.ending-grade {
  background:
    linear-gradient(90deg, rgba(3, 4, 3, 0.92), rgba(3, 4, 3, 0.52) 48%, rgba(3, 4, 3, 0.9)),
    linear-gradient(180deg, rgba(3, 4, 3, 0.64), transparent 35%, rgba(3, 4, 3, 0.9));
}

.ending-tragic .ending-backdrop {
  filter: grayscale(0.8) brightness(0.48) contrast(1.2);
}

.ending-bittersweet .ending-backdrop {
  filter: sepia(0.16) saturate(0.48) brightness(0.72);
}

.ending-legacy .ending-grade {
  background:
    radial-gradient(circle at 69% 38%, rgba(166, 109, 44, 0.1), transparent 26%),
    linear-gradient(90deg, rgba(3, 4, 3, 0.94), rgba(3, 4, 3, 0.52) 52%, rgba(3, 4, 3, 0.78)),
    linear-gradient(180deg, rgba(3, 4, 3, 0.62), transparent 34%, rgba(3, 4, 3, 0.88));
}

.ending-portrait {
  inset: 5vh -4vw -8vh auto;
  width: min(45vw, 38rem);
  height: 103vh;
  object-fit: contain;
  object-position: right bottom;
  opacity: 0.45;
  filter: saturate(0.65) contrast(1.08);
  mask-image: linear-gradient(to right, transparent 0%, black 30%);
}

.ending-topline {
  position: absolute;
  z-index: 3;
  top: max(1.5rem, env(safe-area-inset-top));
  right: var(--safe-inline);
  left: var(--safe-inline);
  display: flex;
  justify-content: space-between;
  color: rgba(215, 196, 162, 0.42);
  font:
    500 0.5rem/1 ui-monospace,
    monospace;
  letter-spacing: 0.22em;
}

.ending-topline strong {
  color: var(--gold-300);
  font-weight: 500;
}

.ending-heading {
  position: absolute;
  z-index: 4;
  top: 50%;
  left: var(--safe-inline);
  width: min(29rem, 34vw);
  opacity: 0;
  transform: translateY(-45%) translateX(-1.5rem);
  transition:
    opacity 1.2s ease,
    transform 1.5s var(--ease-cinema);
}

.ending-heading.visible {
  opacity: 1;
  transform: translateY(-45%) translateX(0);
}

.ending-serial,
.story-label,
.stat > span,
.ending-footer {
  color: var(--gold-300);
  font:
    600 0.52rem/1.2 ui-monospace,
    monospace;
  letter-spacing: 0.22em;
}

.ending-mark {
  position: absolute;
  top: -6rem;
  right: 0;
  color: rgba(214, 173, 102, 0.07);
  font-size: clamp(10rem, 19vw, 17rem);
  line-height: 1;
}

.ending-heading h1 {
  position: relative;
  margin: 0.8rem 0;
  font-size: clamp(4rem, 8vw, 7.5rem);
  font-weight: 400;
  line-height: 1;
  letter-spacing: 0.08em;
}

.ending-heading p {
  position: relative;
  margin: 0;
  padding-top: 1rem;
  border-top: 1px solid rgba(214, 173, 102, 0.34);
  color: rgba(241, 229, 206, 0.68);
  font-size: 0.82rem;
  line-height: 1.9;
  letter-spacing: 0.1em;
}

.ending-mood {
  display: block;
  margin-top: 1rem;
  color: rgba(215, 196, 162, 0.42);
  font-size: 0.65rem;
  letter-spacing: 0.18em;
}

.ending-story {
  position: absolute;
  z-index: 5;
  top: 15vh;
  right: var(--safe-inline);
  width: min(40rem, 50vw);
  height: 53vh;
  opacity: 0;
  transform: translateY(1.5rem);
  transition:
    opacity 1.2s ease,
    transform 1.5s var(--ease-cinema);
}

.ending-story.visible {
  opacity: 1;
  transform: translateY(0);
}

.story-label {
  display: block;
  padding-bottom: 0.8rem;
  border-bottom: 1px solid rgba(214, 173, 102, 0.35);
}

.story-scroll {
  height: calc(100% - 2rem);
  overflow-y: auto;
  padding: 1.1rem 1rem 1rem 0;
}

.story-scroll p {
  margin: 0 0 1rem;
  color: rgba(241, 229, 206, 0.72);
  font-size: clamp(0.78rem, 1vw, 0.92rem);
  line-height: 1.95;
  letter-spacing: 0.07em;
}

.ending-result {
  position: absolute;
  z-index: 6;
  right: var(--safe-inline);
  bottom: max(4rem, calc(env(safe-area-inset-bottom) + 3.5rem));
  display: grid;
  grid-template-columns: 9rem 9rem minmax(15rem, 1fr);
  gap: 1rem;
  width: min(40rem, 50vw);
  padding-top: 1rem;
  border-top: 1px solid rgba(215, 196, 162, 0.12);
  opacity: 0;
  transition: opacity 1s ease;
}

.ending-result.visible {
  opacity: 1;
}

.stat {
  display: grid;
  grid-template-columns: auto 1fr;
  align-items: end;
}

.stat > span {
  grid-column: 1 / 3;
  margin-bottom: 0.35rem;
  color: rgba(215, 196, 162, 0.42);
  font-size: 0.45rem;
}

.stat strong {
  color: var(--gold-300);
  font:
    400 2rem/1 ui-monospace,
    monospace;
}

.stat i {
  margin-bottom: 0.15rem;
  color: rgba(215, 196, 162, 0.42);
  font:
    500 0.62rem/1 ui-monospace,
    monospace;
  font-style: normal;
}

.ending-actions {
  display: flex;
  gap: 0.45rem;
  justify-content: flex-end;
}

.ending-actions button {
  display: flex;
  min-width: 7.6rem;
  min-height: 3rem;
  align-items: center;
  justify-content: space-between;
  padding: 0 0.8rem;
  border: 1px solid rgba(215, 196, 162, 0.16);
  color: rgba(241, 229, 206, 0.68);
  background: rgba(5, 6, 6, 0.58);
  cursor: pointer;
}

.ending-actions button:hover {
  border-color: rgba(214, 173, 102, 0.55);
  color: var(--paper-100);
}

.ending-result > p {
  grid-column: 1 / 4;
  margin: 0;
  color: rgba(214, 173, 102, 0.68);
  font-size: 0.65rem;
  text-align: right;
}

.ending-footer {
  position: absolute;
  z-index: 4;
  right: var(--safe-inline);
  bottom: max(1.4rem, env(safe-area-inset-bottom));
  left: var(--safe-inline);
  display: flex;
  align-items: center;
  gap: 0.7rem;
  color: rgba(215, 196, 162, 0.36);
}

.ending-footer i {
  width: 3rem;
  height: 1px;
  background: rgba(214, 173, 102, 0.22);
}

@media (max-width: 800px), (max-aspect-ratio: 4/5) {
  .ending-grade {
    background: rgba(3, 4, 3, 0.78);
  }

  .ending-topline {
    right: 1rem;
    left: 1rem;
  }

  .ending-heading {
    top: 5.5rem;
    right: 1rem;
    left: 1rem;
    width: auto;
    transform: translateX(-1rem);
  }

  .ending-heading.visible {
    transform: none;
  }

  .ending-heading h1 {
    font-size: 3.6rem;
  }

  .ending-heading p {
    max-width: 24rem;
  }

  .ending-mark {
    top: -2rem;
    font-size: 9rem;
  }

  .ending-story {
    top: 18rem;
    right: 1rem;
    left: 1rem;
    width: auto;
    height: calc(100vh - 31rem);
    min-height: 9rem;
  }

  .ending-result {
    right: 1rem;
    bottom: max(4rem, calc(env(safe-area-inset-bottom) + 3.5rem));
    left: 1rem;
    grid-template-columns: 1fr 1fr;
    width: auto;
  }

  .ending-actions {
    grid-column: 1 / 3;
    justify-content: stretch;
  }

  .ending-actions button {
    flex: 1;
  }

  .ending-result > p {
    grid-column: 1 / 3;
  }

  .ending-portrait {
    right: -30vw;
    width: 95vw;
    opacity: 0.18;
  }

  .ending-footer {
    right: 1rem;
    left: 1rem;
  }
}
</style>
