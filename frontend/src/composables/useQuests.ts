/**
 * 主线任务系统 — 引导玩家推进故事
 *
 * 设计理念：
 * 1. 三幕式叙事结构（探索→理解→选择）
 * 2. 每幕有明确目标和完成条件
 * 3. 支线任务补充角色深度
 * 4. 动态提示下一步该做什么
 */
import { ref, computed, watch } from 'vue'
import type { Ref } from 'vue'

export interface Quest {
  id: string
  title: string
  description: string
  type: 'main' | 'side'
  act: 1 | 2 | 3
  scene: string
  objectives: QuestObjective[]
  hints: string[]           // 玩家卡住时的提示
  unlockCondition: () => boolean
  onComplete?: () => void
  reward?: string           // 完成后解锁的内容
}

export interface QuestObjective {
  id: string
  text: string
  completed: boolean
  condition: () => boolean
}

interface QuestState {
  activeQuests: string[]
  completedQuests: string[]
  currentObjectiveHint: string
  act: 1 | 2 | 3
}

export function useQuests(
  collectedFragments: Ref<string[]>,
  revealedFragments: Ref<string[]>,
  npcTrust: Ref<Record<string, number>>,
  currentScene: Ref<string>,
  dialogueHistory: Ref<Array<{ role: string; content: string }>>
) {
  const questState = ref<QuestState>({
    activeQuests: ['q_prologue'],
    completedQuests: [],
    currentObjectiveHint: '你醒来在一个陌生的地方……先看看周围吧',
    act: 1,
  })

  // ═══════════════════════════════════════
  //  任务定义
  // ═══════════════════════════════════════

  const quests: Record<string, Quest> = {
    // ── 序章：醒来 ──
    q_prologue: {
      id: 'q_prologue',
      title: '陌生的光',
      description: '你在一片温暖的光晕中醒来，周围是老旧的砖墙和一张白色幕布。这是哪里？',
      type: 'main',
      act: 1,
      scene: 'scene_1972',
      objectives: [
        { id: 'explore_1972', text: '探索周围的环境', completed: false, condition: () => collectedFragments.value.length >= 1 },
        { id: 'talk_first_npc', text: '找到一个可以交谈的人', completed: false, condition: () => dialogueHistory.value.length >= 2 },
      ],
      hints: [
        '试试点击场景中发光的物品',
        '幕布旁边好像有什么东西在闪……',
      ],
      unlockCondition: () => true,
      onComplete: () => { activateQuest('q_act1_explore') },
    },

    // ── 第一幕：寻找记忆碎片 ──
    q_act1_explore: {
      id: 'q_act1_explore',
      title: '碎片的呼唤',
      description: '这些发光的碎片是什么？每一块都像是被遗忘的记忆。你需要找到更多，才能理解这一切。',
      type: 'main',
      act: 1,
      scene: '',
      objectives: [
        { id: 'collect_3', text: '收集 3 个记忆碎片', completed: false, condition: () => collectedFragments.value.length >= 3 },
        { id: 'talk_chen_young', text: '和年轻时的陈守义谈谈', completed: false, condition: () => (npcTrust.value['chen_shouyi_young'] || 0) >= 20 },
        { id: 'visit_2024', text: '去 2024 年看看', completed: false, condition: () => currentScene.value === 'scene_2024' },
      ],
      hints: [
        '每个场景都有发光的物品可以点击',
        '点击NPC头像可以和他们对话',
        '试试选择不同的回答，信任度会影响故事走向',
      ],
      unlockCondition: () => questState.value.completedQuests.includes('q_prologue'),
      onComplete: () => { activateQuest('q_act1_shadow') },
      reward: '解锁"记忆回溯"功能 — 可以查看已收集碎片的完整故事',
    },

    // ── 第一幕支线：皮影的秘密 ──
    q_act1_shadow: {
      id: 'q_act1_shadow',
      title: '幕布后面',
      description: '1972年的皮影戏台后面藏着什么？陈守义年轻时到底经历了什么？',
      type: 'main',
      act: 1,
      scene: 'scene_1972',
      objectives: [
        { id: 'collect_shadow', text: '找到"三英战吕布"的记忆碎片', completed: false, condition: () => collectedFragments.value.includes('fragment_shadow_puppet') },
        { id: 'collect_knife', text: '找到陈守义刻刀的记忆碎片', completed: false, condition: () => collectedFragments.value.includes('fragment_grandpa_knife') },
        { id: 'trust_50', text: '让陈守义信任度达到 50', completed: false, condition: () => (npcTrust.value['chen_shouyi_young'] || 0) >= 50 },
      ],
      hints: [
        '戏台旁边的工具箱里可能有什么',
        '幕布上的皮影剪影……点击它试试',
        '和陈守义多聊几次，选择尊重皮影戏的回答',
      ],
      unlockCondition: () => collectedFragments.value.length >= 3,
      onComplete: () => {
        questState.value.act = 2
        activateQuest('q_act2_truth')
      },
      reward: '进入第二幕 — 了解真相',
    },

    // ── 第二幕：理解真相 ──
    q_act2_truth: {
      id: 'q_act2_truth',
      title: '出走的代价',
      description: '1990年，深圳。陈守义离开了西安，放弃了皮影戏。为什么？你需要找到答案。',
      type: 'main',
      act: 2,
      scene: 'scene_1990',
      objectives: [
        { id: 'visit_1990', text: '去 1990 年的深圳火车站', completed: false, condition: () => currentScene.value === 'scene_1990' },
        { id: 'collect_ticket', text: '找到那张火车票', completed: false, condition: () => collectedFragments.value.includes('train_ticket_fragment') },
        { id: 'talk_stranger', text: '和车站的陌生人聊聊', completed: false, condition: () => (npcTrust.value['stranger_1990'] || 0) >= 20 },
        { id: 'collect_letter', text: '找到告别信', completed: false, condition: () => collectedFragments.value.includes('farewell_letter_fragment') },
      ],
      hints: [
        '火车站的地上好像有一张车票',
        '那个穿夹克的年轻人看起来知道些什么',
        '口袋里露出一角的信……',
      ],
      unlockCondition: () => questState.value.completedQuests.includes('q_act1_shadow'),
      onComplete: () => { activateQuest('q_act2_family') },
    },

    // ── 第二幕：家庭的重量 ──
    q_act2_family: {
      id: 'q_act2_family',
      title: '家的重量',
      description: '陈守义离开皮影戏不只是为了钱。他的妻子、女儿……家庭的重担让他做出了选择。',
      type: 'main',
      act: 2,
      scene: 'scene_2024',
      objectives: [
        { id: 'collect_wedding', text: '找到婚纱照碎片', completed: false, condition: () => collectedFragments.value.includes('fragment_wedding_photo') },
        { id: 'collect_medicine', text: '找到药瓶标签碎片', completed: false, condition: () => collectedFragments.value.includes('fragment_medicine_label') },
        { id: 'collect_letter2', text: '找到小雨的信', completed: false, condition: () => collectedFragments.value.includes('fragment_xiaoyu_letter') },
        { id: 'talk_xiaoyu', text: '和小雨谈谈', completed: false, condition: () => (npcTrust.value['xiaoyu'] || 0) >= 30 },
      ],
      hints: [
        '2024年的房间里，墙上挂满了照片',
        '桌上散落着药瓶……标签上写着什么？',
        '抽屉里好像有一封信',
      ],
      unlockCondition: () => collectedFragments.value.includes('farewell_letter_fragment'),
      onComplete: () => {
        questState.value.act = 3
        activateQuest('q_act3_choice')
      },
      reward: '进入第三幕 — 最终选择',
    },

    // ── 第三幕：选择命运 ──
    q_act3_choice: {
      id: 'q_act3_choice',
      title: '拾忆',
      description: '你已经知道了陈守义的一生。现在，在2089年的实验室里，你将帮他做出最后的选择。',
      type: 'main',
      act: 3,
      scene: 'scene_2089',
      objectives: [
        { id: 'visit_2089', text: '去 2089 年的拾忆实验室', completed: false, condition: () => currentScene.value === 'scene_2089' },
        { id: 'collect_all_main', text: '收集所有关键碎片（至少 10 个）', completed: false, condition: () => collectedFragments.value.length >= 10 },
        { id: 'talk_all_npcs', text: '与所有关键NPC交谈过', completed: false, condition: () => Object.keys(npcTrust.value).length >= 4 },
        { id: 'make_choice', text: '做出你的选择', completed: false, condition: () => collectedFragments.value.length >= 12 },
      ],
      hints: [
        '2089年的实验室里，全息投影正在播放什么',
        '收集更多碎片，了解完整的故事',
        '每个NPC都有不同的视角，都听听',
      ],
      unlockCondition: () => questState.value.completedQuests.includes('q_act2_family'),
      reward: '解锁结局',
    },

    // ── 支线：小雨的秘密 ──
    q_side_xiaoyu: {
      id: 'q_side_xiaoyu',
      title: '女儿的心事',
      description: '小雨一直对父亲有复杂的感情。了解她的故事。',
      type: 'side',
      act: 2,
      scene: 'scene_2024',
      objectives: [
        { id: 'xiaoyu_trust_60', text: '让小雨信任度达到 60', completed: false, condition: () => (npcTrust.value['xiaoyu'] || 0) >= 60 },
        { id: 'collect_xiaoyu_letter', text: '找到小雨写给父亲的信', completed: false, condition: () => collectedFragments.value.includes('fragment_xiaoyu_letter') },
      ],
      hints: ['小雨需要时间才会敞开心扉', '选择理解她的回答'],
      unlockCondition: () => (npcTrust.value['xiaoyu'] || 0) >= 20,
    },

    // ── 支线：陌生人是谁 ──
    q_side_stranger: {
      id: 'q_side_stranger',
      title: '站台上的故人',
      description: '1990年火车站的那个陌生人，看起来并不完全陌生……',
      type: 'side',
      act: 2,
      scene: 'scene_1990',
      objectives: [
        { id: 'stranger_trust_50', text: '让陌生人信任度达到 50', completed: false, condition: () => (npcTrust.value['stranger_1990'] || 0) >= 50 },
        { id: 'stranger_reveal', text: '了解陌生人的真实身份', completed: false, condition: () => (npcTrust.value['stranger_1990'] || 0) >= 70 },
      ],
      hints: ['他对皮影戏似乎很了解', '问问他认识的人'],
      unlockCondition: () => currentScene.value === 'scene_1990',
    },
  }

  // ═══════════════════════════════════════
  //  任务操作
  // ═══════════════════════════════════════

  function activateQuest(questId: string) {
    if (!questState.value.activeQuests.includes(questId) &&
        !questState.value.completedQuests.includes(questId)) {
      questState.value.activeQuests.push(questId)
    }
  }

  function checkQuestProgress() {
    for (const questId of [...questState.value.activeQuests]) {
      const quest = quests[questId]
      if (!quest) continue

      // 更新每个目标的完成状态
      let allComplete = true
      for (const obj of quest.objectives) {
        obj.completed = obj.condition()
        if (!obj.completed) allComplete = false
      }

      // 任务完成
      if (allComplete) {
        questState.value.completedQuests.push(questId)
        questState.value.activeQuests = questState.value.activeQuests.filter(id => id !== questId)
        quest.onComplete?.()
      }
    }

    // 检查支线任务解锁
    for (const [id, quest] of Object.entries(quests)) {
      if (quest.type === 'side' &&
          !questState.value.activeQuests.includes(id) &&
          !questState.value.completedQuests.includes(id) &&
          quest.unlockCondition()) {
        activateQuest(id)
      }
    }

    // 更新当前提示
    updateHint()
  }

  function updateHint() {
    const activeQuest = quests[questState.value.activeQuests[0]]
    if (!activeQuest) {
      questState.value.currentObjectiveHint = '所有任务已完成……了吗？'
      return
    }

    // 找到第一个未完成的目标
    const nextObj = activeQuest.objectives.find(o => !o.completed)
    if (nextObj) {
      questState.value.currentObjectiveHint = nextObj.text
    } else {
      questState.value.currentObjectiveHint = activeQuest.description
    }
  }

  // ═══════════════════════════════════════
  //  计算属性
  // ═══════════════════════════════════════

  const currentMainQuest = computed(() => {
    const mainQuestId = questState.value.activeQuests.find(id => quests[id]?.type === 'main')
    return mainQuestId ? quests[mainQuestId] : null
  })

  const currentSideQuests = computed(() => {
    return questState.value.activeQuests
      .filter(id => quests[id]?.type === 'side')
      .map(id => quests[id])
  })

  const allActiveQuests = computed(() => {
    return questState.value.activeQuests.map(id => quests[id]).filter(Boolean)
  })

  const completedQuestCount = computed(() => questState.value.completedQuests.length)
  const totalQuestCount = computed(() => Object.keys(quests).length)

  const currentHint = computed(() => questState.value.currentObjectiveHint)

  const currentAct = computed(() => questState.value.act)

  const actTitle = computed(() => {
    switch (questState.value.act) {
      case 1: return '第一幕 · 寻找'
      case 2: return '第二幕 · 理解'
      case 3: return '第三幕 · 选择'
    }
  })

  // ═══════════════════════════════════════
  //  监听变化，自动检查进度
  // ═══════════════════════════════════════

  watch([collectedFragments, npcTrust, currentScene, dialogueHistory], () => {
    checkQuestProgress()
  }, { deep: true })

  return {
    questState,
    quests,
    currentMainQuest,
    currentSideQuests,
    allActiveQuests,
    completedQuestCount,
    totalQuestCount,
    currentHint,
    currentAct,
    actTitle,
    activateQuest,
    checkQuestProgress,
  }
}
