<script setup lang="ts">
/**
 * NPC动态头像组件
 * 根据NPC ID和情感状态显示不同的SVG头像
 */
import { useI18n } from '../composables/useI18n'

const { t } = useI18n()

const props = defineProps<{
  npcId: string
  emotion?: string
  size?: number
}>()

const avatarSize = props.size || 48

// 情感状态对应的嘴巴和眼睛变化
const emotionMap: Record<string, { mouth: string; eyeOffset: number; blush: boolean }> = {
  neutral: { mouth: 'M38 52 Q44 54 50 52', eyeOffset: 0, blush: false },
  happy: { mouth: 'M36 50 Q44 58 52 50', eyeOffset: -1, blush: true },
  sad: { mouth: 'M38 55 Q44 49 50 55', eyeOffset: 1, blush: false },
  thinking: { mouth: 'M40 52 L48 52', eyeOffset: 0, blush: false },
  touched: { mouth: 'M36 50 Q44 57 52 50', eyeOffset: -1, blush: true },
  nostalgic: { mouth: 'M38 53 Q44 50 50 53', eyeOffset: 0, blush: false },
  worried: { mouth: 'M38 54 Q44 51 50 54', eyeOffset: 1, blush: false },
}

const getEmotion = (e?: string) => emotionMap[e || 'neutral'] || emotionMap.neutral
</script>

<template>
  <div class="npc-avatar" :style="{ width: avatarSize + 'px', height: avatarSize + 'px' }" role="img" :aria-label="t('a11y.npc')">
    <!-- 青年陈守义: 黑发、朝气、方脸 -->
    <svg v-if="npcId === 'chen_shouyi_young'" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
      <!-- 背景光晕 -->
      <circle cx="50" cy="50" r="48" fill="#1a1a2e" />
      <circle cx="50" cy="50" r="46" fill="none" stroke="#ffd700" stroke-width="1" opacity="0.3" />
      <!-- 脸 -->
      <ellipse cx="50" cy="48" rx="22" ry="24" fill="#e8c4a0" />
      <!-- 头发 -->
      <path d="M28 38 Q35 18 50 16 Q65 18 72 38 L70 32 Q60 20 50 18 Q40 20 30 32 Z" fill="#1a0a00" />
      <path d="M28 38 Q26 42 28 36" fill="#1a0a00" />
      <path d="M72 38 Q74 42 72 36" fill="#1a0a00" />
      <!-- 眉毛 -->
      <path d="M36 38 Q42 35 48 38" fill="none" stroke="#3a2a1a" stroke-width="1.5" stroke-linecap="round" />
      <path d="M52 38 Q58 35 64 38" fill="none" stroke="#3a2a1a" stroke-width="1.5" stroke-linecap="round" />
      <!-- 眼睛 -->
      <ellipse cx="42" :cy="42 + getEmotion(emotion).eyeOffset" rx="3" ry="3.5" fill="#1a0a00" />
      <ellipse cx="58" :cy="42 + getEmotion(emotion).eyeOffset" rx="3" ry="3.5" fill="#1a0a00" />
      <circle cx="43" :cy="41 + getEmotion(emotion).eyeOffset" r="1" fill="white" opacity="0.8" />
      <circle cx="59" :cy="41 + getEmotion(emotion).eyeOffset" r="1" fill="white" opacity="0.8" />
      <!-- 腮红 -->
      <ellipse v-if="getEmotion(emotion).blush" cx="35" cy="50" rx="5" ry="3" fill="#e8a0a0" opacity="0.3" />
      <ellipse v-if="getEmotion(emotion).blush" cx="65" cy="50" rx="5" ry="3" fill="#e8a0a0" opacity="0.3" />
      <!-- 嘴巴 -->
      <path :d="getEmotion(emotion).mouth" fill="none" stroke="#c47a5a" stroke-width="1.5" stroke-linecap="round" />
      <!-- 衣领 -->
      <path d="M32 70 Q40 65 50 68 Q60 65 68 70 L72 85 L28 85 Z" fill="#4a6a8a" />
      <path d="M44 68 L50 75 L56 68" fill="none" stroke="#3a5a7a" stroke-width="1" />
    </svg>

    <!-- 老年陈守义: 白发、皱纹、沧桑 -->
    <svg v-else-if="npcId === 'chen_shouyi_old'" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
      <circle cx="50" cy="50" r="48" fill="#1a1a2e" />
      <circle cx="50" cy="50" r="46" fill="none" stroke="#60a5fa" stroke-width="1" opacity="0.3" />
      <!-- 脸 -->
      <ellipse cx="50" cy="48" rx="22" ry="24" fill="#d4b490" />
      <!-- 白发 -->
      <path d="M28 38 Q35 16 50 14 Q65 16 72 38 L70 30 Q58 18 50 16 Q42 18 30 30 Z" fill="#aaaaaa" />
      <!-- 皱纹 -->
      <path d="M34 36 Q38 34 42 36" fill="none" stroke="#8a6a4a" stroke-width="0.8" opacity="0.5" />
      <path d="M58 36 Q62 34 66 36" fill="none" stroke="#8a6a4a" stroke-width="0.8" opacity="0.5" />
      <path d="M40 56 Q50 60 60 56" fill="none" stroke="#8a6a4a" stroke-width="0.6" opacity="0.4" />
      <!-- 眉毛（花白） -->
      <path d="M36 38 Q42 35 48 38" fill="none" stroke="#8a8a8a" stroke-width="1.5" stroke-linecap="round" />
      <path d="M52 38 Q58 35 64 38" fill="none" stroke="#8a8a8a" stroke-width="1.5" stroke-linecap="round" />
      <!-- 眼睛（略显空洞） -->
      <ellipse cx="42" :cy="42 + getEmotion(emotion).eyeOffset" rx="3" ry="3" fill="#5a4a3a" />
      <ellipse cx="58" :cy="42 + getEmotion(emotion).eyeOffset" rx="3" ry="3" fill="#5a4a3a" />
      <circle cx="43" :cy="41 + getEmotion(emotion).eyeOffset" r="0.8" fill="white" opacity="0.5" />
      <circle cx="59" :cy="41 + getEmotion(emotion).eyeOffset" r="0.8" fill="white" opacity="0.5" />
      <!-- 眼袋 -->
      <ellipse cx="42" cy="47" rx="4" ry="2" fill="#c4a480" opacity="0.3" />
      <ellipse cx="58" cy="47" rx="4" ry="2" fill="#c4a480" opacity="0.3" />
      <!-- 腮红 -->
      <ellipse v-if="getEmotion(emotion).blush" cx="35" cy="50" rx="5" ry="3" fill="#d4a0a0" opacity="0.25" />
      <ellipse v-if="getEmotion(emotion).blush" cx="65" cy="50" rx="5" ry="3" fill="#d4a0a0" opacity="0.25" />
      <!-- 嘴巴 -->
      <path :d="getEmotion(emotion).mouth" fill="none" stroke="#a47a5a" stroke-width="1.5" stroke-linecap="round" />
      <!-- 衣领 -->
      <path d="M32 70 Q40 65 50 68 Q60 65 68 70 L72 85 L28 85 Z" fill="#5a5a5a" />
    </svg>

    <!-- 小雨: 长发、年轻、微红眼眶 -->
    <svg v-else-if="npcId === 'xiaoyu'" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
      <circle cx="50" cy="50" r="48" fill="#1a1a2e" />
      <circle cx="50" cy="50" r="46" fill="none" stroke="#a78bfa" stroke-width="1" opacity="0.3" />
      <!-- 长发 -->
      <path d="M26 35 Q30 12 50 10 Q70 12 74 35 L74 65 Q70 75 65 70 L65 40 Q60 20 50 18 Q40 20 35 40 L35 70 Q30 75 26 65 Z" fill="#1a0a00" />
      <!-- 脸 -->
      <ellipse cx="50" cy="46" rx="20" ry="22" fill="#f0d0b0" />
      <!-- 刘海 -->
      <path d="M30 38 Q35 28 42 30 Q38 35 35 38" fill="#1a0a00" />
      <path d="M70 38 Q65 28 58 30 Q62 35 65 38" fill="#1a0a00" />
      <!-- 眉毛 -->
      <path d="M38 36 Q42 34 46 36" fill="none" stroke="#3a2a1a" stroke-width="1.2" stroke-linecap="round" />
      <path d="M54 36 Q58 34 62 36" fill="none" stroke="#3a2a1a" stroke-width="1.2" stroke-linecap="round" />
      <!-- 眼睛 -->
      <ellipse cx="42" :cy="40 + getEmotion(emotion).eyeOffset" rx="3" ry="3.5" fill="#2a1a0a" />
      <ellipse cx="58" :cy="40 + getEmotion(emotion).eyeOffset" rx="3" ry="3.5" fill="#2a1a0a" />
      <circle cx="43" :cy="39 + getEmotion(emotion).eyeOffset" r="1.2" fill="white" opacity="0.8" />
      <circle cx="59" :cy="39 + getEmotion(emotion).eyeOffset" r="1.2" fill="white" opacity="0.8" />
      <!-- 红眼眶 -->
      <ellipse cx="42" cy="44" rx="5" ry="2.5" fill="#e8a0a0" opacity="0.2" />
      <ellipse cx="58" cy="44" rx="5" ry="2.5" fill="#e8a0a0" opacity="0.2" />
      <!-- 腮红 -->
      <ellipse v-if="getEmotion(emotion).blush" cx="35" cy="48" rx="5" ry="3" fill="#e8a0a0" opacity="0.3" />
      <ellipse v-if="getEmotion(emotion).blush" cx="65" cy="48" rx="5" ry="3" fill="#e8a0a0" opacity="0.3" />
      <!-- 嘴巴 -->
      <path :d="getEmotion(emotion).mouth" fill="none" stroke="#d47a6a" stroke-width="1.5" stroke-linecap="round" />
      <!-- 衣领 -->
      <path d="M34 68 Q42 63 50 66 Q58 63 66 68 L70 85 L30 85 Z" fill="#8a6a9a" />
    </svg>

    <!-- 未知NPC: 默认圆形 -->
    <svg v-else viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
      <circle cx="50" cy="50" r="48" fill="#1a1a2e" />
      <circle cx="50" cy="50" r="46" fill="none" stroke="#888" stroke-width="1" opacity="0.3" />
      <circle cx="50" cy="42" r="18" fill="#888" />
      <path d="M28 80 Q28 60 50 58 Q72 60 72 80" fill="#888" />
      <text x="50" y="90" text-anchor="middle" fill="#aaa" font-size="14">?</text>
    </svg>
  </div>
</template>

<style scoped>
.npc-avatar {
  display: inline-block;
  border-radius: 50%;
  overflow: hidden;
  flex-shrink: 0;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.4);
  transition: transform 0.2s ease;
  animation: npcBreathe 4s ease-in-out infinite;
}

.npc-avatar:hover {
  transform: scale(1.08);
  box-shadow: 0 4px 20px rgba(232, 180, 80, 0.3);
}

/* 呼吸动画 */
@keyframes npcBreathe {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.02); }
}

/* 眨眼动画（通过SVG内部opacity实现） */
.npc-avatar svg ellipse[rx="3"] {
  animation: npcBlink 5s ease-in-out infinite;
}

@keyframes npcBlink {
  0%, 42%, 46%, 100% { transform: scaleY(1); }
  44% { transform: scaleY(0.1); }
}

/* 选中状态光环 */
.npc-avatar::after {
  content: '';
  position: absolute;
  inset: -3px;
  border-radius: 50%;
  border: 2px solid rgba(232, 180, 80, 0);
  transition: border-color 0.3s;
}

svg {
  width: 100%;
  height: 100%;
  display: block;
}
</style>
