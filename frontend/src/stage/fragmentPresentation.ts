import shadowStage1972 from '../assets/cinematic/fragment-1972-shadow-stage.webp'
import carvingKnife1972 from '../assets/cinematic/fragment-1972-carving-knife.webp'
import threeKings1972 from '../assets/cinematic/fragment-1972-three-kings.webp'
import trainTicket1990 from '../assets/cinematic/fragment-1990-train-ticket.webp'
import puppetTrunk1990 from '../assets/cinematic/fragment-1990-puppet-trunk.webp'
import farewellLetter1990 from '../assets/cinematic/fragment-1990-farewell-letter.webp'
import stationClock1990 from '../assets/cinematic/fragment-1990-station-clock.webp'
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
  fragment_shadow_puppet: {
    id: 'fragment_shadow_puppet',
    image: shadowStage1972,
    alt: '暖灯后的皮影戏幕上，手工皮影人物与竹制操纵杆在尘埃中显出轮廓。',
    focus: '50% 50%',
  },
  fragment_grandpa_knife: {
    id: 'fragment_grandpa_knife',
    image: carvingKnife1972,
    alt: '被岁月磨亮手柄的旧刻刀，安静地横在木制皮影工具箱上。',
    focus: '50% 52%',
  },
  fragment_three_kings: {
    id: 'fragment_three_kings',
    image: threeKings1972,
    alt: '三英战吕布的四枚皮影人物在暖色戏幕前定格成一场未完的交锋。',
    focus: '50% 50%',
  },
  train_ticket_fragment: {
    id: 'train_ticket_fragment',
    image: trainTicket1990,
    alt: '被汗水浸皱的南下硬座车票，背景是绿皮火车与皮影木箱。',
    focus: '50% 50%',
  },
  puppet_trunk_fragment: {
    id: 'puppet_trunk_fragment',
    image: puppetTrunk1990,
    alt: '磨损的皮影木箱半掩着一枚皮影人物，沾着南下站台的煤烟。',
    focus: '50% 52%',
  },
  farewell_letter_fragment: {
    id: 'farewell_letter_fragment',
    image: farewellLetter1990,
    alt: '未寄出的告别信与钢笔放在站台长椅上，纸面只留下模糊墨迹。',
    focus: '50% 50%',
  },
  station_clock_fragment: {
    id: 'station_clock_fragment',
    image: stationClock1990,
    alt: '旧站台时钟穿过蒸汽与钨丝灯光，记录着南下列车即将开出的时刻。',
    focus: '50% 46%',
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
