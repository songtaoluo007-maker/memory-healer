import { ref, computed } from 'vue'

type Lang = 'zh' | 'en'
const currentLang = ref<Lang>('zh')

const messages: Record<Lang, Record<string, string>> = {
  zh: {
    // 通用
    'app.title': '拾忆',
    'app.subtitle': '一部关于遗忘与记忆的互动叙事',
    'nav.back': '返回',
    'nav.home': '首页',
    'nav.saves': '存档',

    // 首页
    'home.start': '开始旅程',
    'home.continue': '继续旅程',
    'home.saves': '存档管理',
    'home.intro': '你将进入一段跨越百年的记忆。每一个选择，都会在时间的长河中激起涟漪。',

    // 游戏
    'game.narrative': '叙事',
    'game.dialogue': '对话',
    'game.memory': '记忆碎片',
    'game.ending': '结局',
    'game.continue': '继续',
    'game.skip': '跳过',
    'game.collect': '收集',

    // 结局
    'ending.hope': '希望',
    'ending.bittersweet': '苦涩',
    'ending.tragic': '悲剧',
    'ending.legacy': '传承',
    'ending.replay': '重新体验',
    'ending.share': '分享故事',

    // 存档
    'saves.empty': '暂无存档',
    'saves.save': '保存',
    'saves.load': '加载',
    'saves.delete': '删除',
    'saves.confirm': '确定删除此存档？',

    // 场景
    'scene.1972': '1972年·西安',
    'scene.1990': '1990年·深圳',
    'scene.2024': '2024年·深圳',
    'scene.2050': '2050年·北京',
    'scene.2089': '2089年·记忆研究所',

    // NPC
    'npc.master': '师父',
    'npc.stranger': '陌生人',
    'npc.xiaoyu': '小雨',
    'npc.journalist': '记者',

    // 信物
    'artifact.shadow_puppet': '皮影人偶',
    'artifact.train_ticket': '单程车票',
    'artifact.namecard': '名片',
    'artifact.photo': '全家福',
    'artifact.crystal': '水晶奖杯',
    'artifact.album': '全息相册',

    // 无障碍
    'a11y.scene': '场景插画',
    'a11y.npc': 'NPC头像',
    'a11y.hotspot': '可点击区域',
    'a11y.dialogue': '对话面板',
    'a11y.narrative': '叙事文本',
    'a11y.language': '语言切换',
  },
  en: {
    // General
    'app.title': 'Memory Healer',
    'app.subtitle': 'An interactive narrative about forgetting and memory',
    'nav.back': 'Back',
    'nav.home': 'Home',
    'nav.saves': 'Saves',

    // Home
    'home.start': 'Begin Journey',
    'home.continue': 'Continue Journey',
    'home.saves': 'Save Files',
    'home.intro': 'You are about to enter a century-spanning memory. Every choice creates ripples through the river of time.',

    // Game
    'game.narrative': 'Narrative',
    'game.dialogue': 'Dialogue',
    'game.memory': 'Memory Fragments',
    'game.ending': 'Ending',
    'game.continue': 'Continue',
    'game.skip': 'Skip',
    'game.collect': 'Collect',

    // Endings
    'ending.hope': 'Hope',
    'ending.bittersweet': 'Bittersweet',
    'ending.tragic': 'Tragedy',
    'ending.legacy': 'Legacy',
    'ending.replay': 'Replay',
    'ending.share': 'Share Story',

    // Saves
    'saves.empty': 'No saves yet',
    'saves.save': 'Save',
    'saves.load': 'Load',
    'saves.delete': 'Delete',
    'saves.confirm': 'Delete this save?',

    // Scenes
    'scene.1972': '1972 · Xi\'an',
    'scene.1990': '1990 · Shenzhen',
    'scene.2024': '2024 · Shenzhen',
    'scene.2050': '2050 · Beijing',
    'scene.2089': '2089 · Memory Lab',

    // NPCs
    'npc.master': 'Master',
    'npc.stranger': 'Stranger',
    'npc.xiaoyu': 'Xiaoyu',
    'npc.journalist': 'Journalist',

    // Artifacts
    'artifact.shadow_puppet': 'Shadow Puppet',
    'artifact.train_ticket': 'One-Way Ticket',
    'artifact.namecard': 'Business Card',
    'artifact.photo': 'Family Photo',
    'artifact.crystal': 'Crystal Trophy',
    'artifact.album': 'Holographic Album',

    // A11y
    'a11y.scene': 'Scene illustration',
    'a11y.npc': 'NPC avatar',
    'a11y.hotspot': 'Clickable area',
    'a11y.dialogue': 'Dialogue panel',
    'a11y.narrative': 'Narrative text',
    'a11y.language': 'Language switch',
  }
}

export function useI18n() {
  function t(key: string): string {
    return messages[currentLang.value][key] || key
  }

  function setLang(lang: Lang) {
    currentLang.value = lang
    localStorage.setItem('mh_lang', lang)
  }

  function toggleLang() {
    setLang(currentLang.value === 'zh' ? 'en' : 'zh')
  }

  // 初始化
  const saved = localStorage.getItem('mh_lang') as Lang | null
  if (saved && (saved === 'zh' || saved === 'en')) {
    currentLang.value = saved
  }

  return {
    lang: computed(() => currentLang.value),
    t,
    setLang,
    toggleLang
  }
}
