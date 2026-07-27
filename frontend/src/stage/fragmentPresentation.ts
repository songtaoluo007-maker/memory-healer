import trainTicket1990 from '../assets/cinematic/fragment-1990-train-ticket.webp'
import xiaoyuLetter2024 from '../assets/cinematic/fragment-2024-xiaoyu-letter.webp'
import awardTrophy2050 from '../assets/cinematic/fragment-2050-award-trophy.webp'
import lastPuppet2089 from '../assets/cinematic/fragment-2089-last-puppet.webp'

export interface FragmentPresentation {
  id: string
  image: string
  alt: string
  focus: string
}

const presentations: Record<string, FragmentPresentation> = {
  train_ticket_fragment: {
    id: 'train_ticket_fragment',
    image: trainTicket1990,
    alt: '被汗水浸皱的南下硬座车票，背景是绿皮火车与皮影木箱。',
    focus: '50% 50%',
  },
  fragment_letter: {
    id: 'fragment_letter',
    image: xiaoyuLetter2024,
    alt: '被反复折叠的小雨来信，放在旧刻刀和泛黄皮影剧照旁。',
    focus: '50% 50%',
  },
  award_trophy_fragment: {
    id: 'award_trophy_fragment',
    image: awardTrophy2050,
    alt: '折射暖金光晕的水晶奖杯，内部映出一枚皮影轮廓。',
    focus: '50% 48%',
  },
  fragment_last_puppet: {
    id: 'fragment_last_puppet',
    image: lastPuppet2089,
    alt: '陈守义最后制作的孙悟空皮影人偶，在青紫实验室中透出暖色记忆光。',
    focus: '50% 50%',
  },
}

export function getFragmentPresentation(fragmentId: string): FragmentPresentation | null {
  return presentations[fragmentId] ?? null
}
