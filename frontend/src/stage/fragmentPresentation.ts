import trainTicket1990 from '../assets/cinematic/fragment-1990-train-ticket.webp'

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
}

export function getFragmentPresentation(fragmentId: string): FragmentPresentation | null {
  return presentations[fragmentId] ?? null
}
