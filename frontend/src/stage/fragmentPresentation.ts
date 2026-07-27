import trainTicket1990 from '../assets/cinematic/fragment-1990-train-ticket.webp'
import xiaoyuLetter2024 from '../assets/cinematic/fragment-2024-xiaoyu-letter.webp'

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
}

export function getFragmentPresentation(fragmentId: string): FragmentPresentation | null {
  return presentations[fragmentId] ?? null
}
