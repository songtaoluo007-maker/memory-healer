# 拾忆 · 1990—2089 电影美术重制 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **执行状态（2026-07-27）：** Tasks 1—7 与 Task 9 自动化质量门已完成；
> Task 8 的本机服务检查已完成，应用内浏览器因本机 URL 接管策略拒绝自动控制，
> 故完整剧情截图与四视口人工视觉签收仍保持未勾选。

**Goal:** 生成并接入 1990、2024、2050、2089 的 4 张电影主场景、6 张 NPC
立绘和 4 张代表碎片插片，使后续四幕达到与 1972 一致的电影品质。

**Architecture:** 保持后端 `GameState`、内容 ID 和规则不变；扩展纯展示
`ScenePresentation` 为多 NPC 立绘映射，并新增独立碎片展示注册表。PixiJS 只加载
当前场景背景，Vue 渲染语义化人物、碎片和降级 UI；所有新图片运行时使用 WebP，
主背景失败继续回退旧 `SceneIllustration`。

**Tech Stack:** Vue 3、TypeScript、Pinia、PixiJS 8、Vitest、Vite、内置
imagegen、FFmpeg 8.1/libwebp、Playwright/Edge 浏览器验收。

## Global Constraints

- 设计规格：`docs/superpowers/specs/2026-07-27-later-era-art-remaster-design.md`。
- 范围固定为 4 张主场景、6 张 NPC 立绘、4 张代表碎片，共 14 张。
- 不修改 canonical scene/NPC/fragment/hotspot/choice ID、后端规则或存档 schema。
- 生成图片不得包含可读招牌、证书正文、票据正文、品牌 Logo、水印或乱码。
- 主场景内不得出现与独立 NPC 立绘重复的清晰正面角色。
- 陈守义 1990/2024 必须以现有 1972 立绘为身份参考。
- 2089 小雨必须以 2050 小雨为身份参考，并明确呈现为年轻记忆投影。
- 背景目标单张不超过 1.5 MB，人物不超过 800 KB，碎片不超过 600 KB。
- 保留主背景 SVG 回退；人物或碎片断图不得阻断文字和操作。
- 不把生成源 PNG 全部加入 Git；最终项目资产使用高质量 WebP。
- 不启用子代理；在当前会话使用 `superpowers:executing-plans` 内联执行。

---

### Task 1: Refactor the presentation contract for multiple NPC portraits

**Files:**
- Modify: `frontend/src/__tests__/scenePresentation.test.ts`
- Modify: `frontend/src/stage/presentation.ts`
- Modify: `frontend/src/components/CinematicStage.vue`

**Interfaces:**
- Consumes: `getScenePresentation(sceneId: string): ScenePresentation | null`
- Produces: `ScenePresentation.portraits: Readonly<Record<string, string>>`
- Produces: `activePortrait: ComputedRef<string | null>` inside `CinematicStage.vue`

- [x] **Step 1: Write the failing 1972 contract test**

Replace the portrait assertions in
`frontend/src/__tests__/scenePresentation.test.ts` with:

```ts
expect(scene?.portraits).toEqual({
  chen_shouyi_young: expect.stringContaining('chen-shouyi-1972'),
})
expect(scene).not.toHaveProperty('portrait')
expect(scene).not.toHaveProperty('portraitNpcIds')
```

- [x] **Step 2: Run the focused test and verify RED**

Run:

```powershell
cd frontend
npm test -- --run src/__tests__/scenePresentation.test.ts
```

Expected: FAIL because `portraits` does not exist and the legacy portrait fields remain.

- [x] **Step 3: Replace the single-portrait interface**

In `frontend/src/stage/presentation.ts`, change the interface fields to:

```ts
portraits: Readonly<Record<string, string>>
```

Change the 1972 entry to:

```ts
portraits: {
  chen_shouyi_young: chenShouyi1972Portrait,
},
```

Delete `portrait` and `portraitNpcIds`.

- [x] **Step 4: Select the portrait by canonical NPC ID**

In `frontend/src/components/CinematicStage.vue`, add:

```ts
const activePortrait = computed(() => {
  if (!props.activeNpcId) return null
  return presentation.value?.portraits[props.activeNpcId] ?? null
})
```

Replace the portrait `<img>` condition and source with:

```vue
<img
  v-if="activePortrait"
  class="character-portrait"
  :src="activePortrait"
  alt=""
  aria-hidden="true"
/>
```

- [x] **Step 5: Verify GREEN**

Run:

```powershell
cd frontend
npm test -- --run src/__tests__/scenePresentation.test.ts
npm run typecheck
```

Expected: 2 tests passed; typecheck passed.

- [x] **Step 6: Commit the contract refactor**

```powershell
git add frontend/src/__tests__/scenePresentation.test.ts frontend/src/stage/presentation.ts frontend/src/components/CinematicStage.vue
git commit -m "refactor: support per-NPC cinematic portraits"
```

---

### Task 2: Generate, optimize, and register the 1990 art package

**Files:**
- Create: `frontend/src/assets/cinematic/scene-1990-shenzhen-station.webp`
- Create: `frontend/src/assets/cinematic/chen-shouyi-1990.webp`
- Create: `frontend/src/assets/cinematic/stranger-1990.webp`
- Create: `frontend/src/assets/cinematic/fragment-1990-train-ticket.webp`
- Create: `frontend/src/stage/fragmentPresentation.ts`
- Create: `frontend/src/__tests__/fragmentPresentation.test.ts`
- Modify: `frontend/src/stage/presentation.ts`
- Modify: `frontend/src/__tests__/scenePresentation.test.ts`

**Interfaces:**
- Produces: `getFragmentPresentation(fragmentId: string): FragmentPresentation | null`
- Produces: `FragmentPresentation { id: string; image: string; alt: string; focus: string }`
- Produces: registered `scene_1990`, `chen_shouyi_1990`, `stranger_1990`

- [x] **Step 1: Generate the 1990 main scene with built-in imagegen**

Use one built-in imagegen call with no input image:

```text
Use case: historical-scene
Asset type: cinematic game master background
Primary request: 1990 Shenzhen railway station platform at dusk, a green passenger train arriving through coal smoke, crowds carrying woven travel bags, an old round station clock above, a weathered shadow-puppet wooden trunk near the right foreground, worn travel papers suggested at left, early Special Economic Zone atmosphere
Style/medium: cinematic realistic animated feature, matching the existing 1972 Xi'an scene, authentic Chinese 1990 material detail, subtle shadow-puppet visual motif
Composition/framing: wide landscape composed for a 2.39:1 crop; clock near upper center, left and right hotspot objects visible; dark subtitle-safe area at lower left; clear portrait-safe area on the right; also retain the train and trunk in a portrait mobile crop
Lighting/mood: train green, coal-smoke gray, warm tungsten platform lamps; hopeful but uncertain
Constraints: environmental crowd only, no clear front-facing hero character, no readable signs, no logos, no watermark, no modern high-speed train, no contemporary phones
```

Inspect the result. Reject it if the train is modern, the clock/trunk is missing, or a clear hero
duplicates the portrait layer.

- [x] **Step 2: Generate middle-aged Chen Shouyi using the 1972 portrait as identity reference**

Use `frontend/src/assets/cinematic/chen-shouyi-1972.png` as a reference image:

```text
Use case: identity-preserve
Asset type: cinematic game character plate
Primary request: age the referenced Chen Shouyi naturally to 43 years old in 1990; he is a shadow-puppet artisan leaving home for Shenzhen, wearing worn blue-gray work clothes, holding the edge of an old wooden puppet trunk, hesitant but determined
Input images: Image 1 is the identity and cinematography reference; preserve facial bone structure, eye spacing, nose, jaw, restrained expression, and artisan hands
Style/medium: cinematic realistic animated feature, same film and actor as Image 1
Composition/framing: vertical half-body portrait, subject on the right half, generous dark negative space on the left for horizontal fade
Lighting/mood: cool station ambient light with warm tungsten rim light
Constraints: natural aging only; no beard unless subtle stubble; no text, logo, watermark, extra people, train ticket covering the face
```

- [x] **Step 3: Generate the 1990 platform stranger**

Use one built-in imagegen call with no identity reference:

```text
Use case: historical-scene
Asset type: cinematic game character plate
Primary request: a warm and observant 28-year-old Chinese man at Shenzhen railway station in 1990, wearing a new but period-authentic jacket, outwardly another migrant worker yet quietly evaluating a traditional shadow-puppet trunk
Style/medium: cinematic realistic animated feature, consistent with the 1972 film world
Composition/framing: vertical half-body portrait, subject on the right, dark negative space on the left
Lighting/mood: smoky green station ambience with tungsten edge light, open and curious rather than sinister
Constraints: no modern business suit, smartphone, logo, text, watermark, extra people
```

- [x] **Step 4: Generate the 1990 representative fragment**

```text
Use case: historical-scene
Asset type: cinematic memory fragment insert
Primary request: macro close-up of a wrinkled 1990 Chinese hard-seat railway ticket held by a calloused artisan hand, sweat-softened paper, faded red stamp shapes, a shadow-puppet trunk and green train blurred in the background
Style/medium: cinematic prop photography translated into realistic animated-feature art
Composition/framing: 4:3 landscape macro, ticket fully visible, negative space for UI caption
Lighting/mood: warm tungsten against cool train green, intimate and nostalgic
Constraints: no readable ticket text, no gibberish characters, no logo, no watermark, no modern QR code
```

- [x] **Step 5: Convert the selected images to WebP and enforce budgets**

For each selected PNG path returned by imagegen, run:

```powershell
ffmpeg -y -i "<generated_png>" -an -c:v libwebp -quality 88 -compression_level 6 -preset picture "frontend/src/assets/cinematic/<target>.webp"
```

Use the exact target names listed in this task. Check sizes:

```powershell
Get-Item frontend/src/assets/cinematic/*1990*.webp | Select-Object Name,Length
```

If a background exceeds 1.5 MB or another asset exceeds its budget, retry that file with
`-quality 84`; do not resize below the generated source dimensions unless the long edge exceeds
2560 px.

- [x] **Step 6: Write failing registry tests**

Add to `scenePresentation.test.ts`:

```ts
it('registers the 1990 scene and both distinct NPC portraits', () => {
  const scene = getScenePresentation('scene_1990')
  expect(scene?.background).toContain('scene-1990-shenzhen-station')
  expect(Object.keys(scene?.portraits ?? {}).sort()).toEqual([
    'chen_shouyi_1990',
    'stranger_1990',
  ])
  expect(scene?.portraits.chen_shouyi_1990).not.toBe(scene?.portraits.stranger_1990)
  expect(scene?.composition.mobileFocus).toBeDefined()
})
```

Create `fragmentPresentation.test.ts`:

```ts
import { describe, expect, it } from 'vitest'
import { getFragmentPresentation } from '../stage/fragmentPresentation'

describe('fragment presentation registry', () => {
  it('registers the 1990 train-ticket insert', () => {
    const fragment = getFragmentPresentation('train_ticket_fragment')
    expect(fragment?.image).toContain('fragment-1990-train-ticket')
    expect(fragment?.alt).toContain('车票')
  })

  it('returns null for a fragment without bespoke art', () => {
    expect(getFragmentPresentation('fragment_grandpa_knife')).toBeNull()
  })
})
```

Run both focused tests and confirm they fail before registration.

- [x] **Step 7: Register 1990 scene, portraits, and fragment**

Import the three scene/person WebP files in `presentation.ts`:

```ts
import scene1990Background from '../assets/cinematic/scene-1990-shenzhen-station.webp'
import chenShouyi1990Portrait from '../assets/cinematic/chen-shouyi-1990.webp'
import stranger1990Portrait from '../assets/cinematic/stranger-1990.webp'
```

Add:

```ts
scene_1990: {
  id: 'scene_1990',
  eraLabel: '庚午年 · 秋',
  locationLabel: '深圳 · 火车站',
  palette: 'rail',
  background: scene1990Background,
  portraits: {
    chen_shouyi_1990: chenShouyi1990Portrait,
    stranger_1990: stranger1990Portrait,
  },
  alt: '1990年深圳火车站，绿皮火车驶入煤烟笼罩的站台，旧木箱与南下人群等待新的生活。',
  composition: {
    desktopFocus: [0.5, 0.48],
    mobileFocus: [0.52, 0.5],
  },
},
```

Create `fragmentPresentation.ts`:

```ts
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
```

Add `rail` to `CinematicPalette`.

- [x] **Step 8: Verify and commit the 1990 package**

Run focused tests, typecheck, and build. Then:

```powershell
git add frontend/src/assets/cinematic/*1990*.webp frontend/src/stage/presentation.ts frontend/src/stage/fragmentPresentation.ts frontend/src/__tests__/scenePresentation.test.ts frontend/src/__tests__/fragmentPresentation.test.ts
git commit -m "feat: add 1990 cinematic art package"
```

---

### Task 3: Generate, optimize, and register the 2024 art package

**Files:**
- Create: `frontend/src/assets/cinematic/scene-2024-urban-village-room.webp`
- Create: `frontend/src/assets/cinematic/chen-shouyi-2024.webp`
- Create: `frontend/src/assets/cinematic/fragment-2024-xiaoyu-letter.webp`
- Modify: `frontend/src/stage/presentation.ts`
- Modify: `frontend/src/stage/fragmentPresentation.ts`
- Modify: `frontend/src/__tests__/scenePresentation.test.ts`
- Modify: `frontend/src/__tests__/fragmentPresentation.test.ts`

**Interfaces:**
- Produces: registered `scene_2024`, `chen_shouyi_old`, `fragment_letter`

- [x] **Step 1: Generate the 2024 room**

```text
Use case: historical-scene
Asset type: cinematic game master background
Primary request: cramped 2024 Shenzhen urban-village rental room on a rainy night, old shadow-puppet workbench, carving knife, unfinished puppets, yellowed performance photos and a last-show poster on the left wall, repeatedly folded letter on the right side of the desk, empty worn chair, barred window revealing blue neon towers
Style/medium: cinematic realistic animated feature, same film as the 1972 scene, authentic worn plaster, wood, paper and rain
Composition/framing: intimate wide shot for 2.39:1 crop; oppressive foreground; left wall and right desk objects remain visible; dark subtitle-safe lower left; right portrait-safe zone; mobile crop centered on desk, window and chair
Lighting/mood: rain blue, old-wall gray, distant Shenzhen neon, one weak warm desk lamp; lonely and fragile
Constraints: no clear person in the room, no readable poster or letter text, no logos, no watermark, no luxury apartment, no cyberpunk excess
```

- [x] **Step 2: Generate elderly Chen Shouyi from the 1972 identity reference**

```text
Use case: identity-preserve
Asset type: cinematic game character plate
Primary request: age the referenced Chen Shouyi naturally to 77 years old in 2024, white-gray hair, slightly stooped, seated with a carving knife held motionless, trying hard to remember rather than simply looking sad
Input images: Image 1 is the identity and cinematography reference; preserve facial bone structure, eye spacing, nose, jaw, restrained gaze, and artisan hands
Style/medium: cinematic realistic animated feature, same actor many decades later
Composition/framing: vertical seated half-body portrait on the right, dark negative space on the left
Lighting/mood: cool rain-window light with faint warm desk-lamp rim
Constraints: dignified natural aging, no exaggerated illness, no medical equipment, no text, logo, watermark, extra people
```

- [x] **Step 3: Generate the folded letter fragment**

```text
Use case: illustration-story
Asset type: cinematic memory fragment insert
Primary request: macro close-up of a small letter repeatedly folded and unfolded, childlike pencil marks and simple drawings without readable words, resting beside an old carving knife and a faded shadow-puppet photo
Style/medium: cinematic realistic animated-feature prop close-up
Composition/framing: 4:3 landscape, letter centered with caption-safe dark edge
Lighting/mood: weak warm lamp surrounded by rainy blue darkness, tender and painful
Constraints: no readable sentence, no gibberish text, no logo, no watermark, no modern printed stationery
```

- [x] **Step 4: Convert and visually validate**

For each selected imagegen output, run FFmpeg separately:

```powershell
ffmpeg -y -i "<2024_scene_imagegen_output>" -an -c:v libwebp -quality 88 -compression_level 6 -preset picture "frontend/src/assets/cinematic/scene-2024-urban-village-room.webp"
ffmpeg -y -i "<2024_chen_imagegen_output>" -an -c:v libwebp -quality 88 -compression_level 6 -preset picture "frontend/src/assets/cinematic/chen-shouyi-2024.webp"
ffmpeg -y -i "<2024_letter_imagegen_output>" -an -c:v libwebp -quality 88 -compression_level 6 -preset picture "frontend/src/assets/cinematic/fragment-2024-xiaoyu-letter.webp"
```

Here each angle-bracket value means the absolute output path returned by that immediately
preceding built-in imagegen call; record the returned value before invoking FFmpeg. Inspect both
desktop-wide and portrait crops; the desk letter, left photos, chair and rain window must survive.

- [x] **Step 5: Add failing tests, then register**

Tests must assert:

```ts
expect(getScenePresentation('scene_2024')?.portraits).toHaveProperty('chen_shouyi_old')
expect(getScenePresentation('scene_2024')?.palette).toBe('rain')
expect(getFragmentPresentation('fragment_letter')?.image).toContain(
  'fragment-2024-xiaoyu-letter',
)
```

Confirm RED, then add imports and entries. Add `rain` to `CinematicPalette`; use
this exact scene entry:

```ts
import scene2024Background from '../assets/cinematic/scene-2024-urban-village-room.webp'
import chenShouyi2024Portrait from '../assets/cinematic/chen-shouyi-2024.webp'

scene_2024: {
  id: 'scene_2024',
  eraLabel: '甲辰年 · 雨夜',
  locationLabel: '深圳 · 城中村',
  palette: 'rain',
  background: scene2024Background,
  portraits: {
    chen_shouyi_old: chenShouyi2024Portrait,
  },
  alt: '2024年深圳城中村的雨夜出租屋，旧皮影工作台面对被霓虹切开的窗户，信件与泛黄剧照仍留在暗处。',
  composition: {
    desktopFocus: [0.5, 0.5],
    mobileFocus: [0.57, 0.5],
  },
},
```

In `fragmentPresentation.ts`, import
`xiaoyuLetter2024` from `../assets/cinematic/fragment-2024-xiaoyu-letter.webp`, then add:

```ts
fragment_letter: {
  id: 'fragment_letter',
  image: xiaoyuLetter2024,
  alt: '被反复折叠的小雨来信，放在旧刻刀和泛黄皮影剧照旁。',
  focus: '50% 50%',
},
```

- [x] **Step 6: Verify and commit**

Run both registry tests, typecheck, and build, then commit:

```powershell
git add frontend/src/assets/cinematic/*2024*.webp frontend/src/stage/presentation.ts frontend/src/stage/fragmentPresentation.ts frontend/src/__tests__/scenePresentation.test.ts frontend/src/__tests__/fragmentPresentation.test.ts
git commit -m "feat: add 2024 cinematic art package"
```

---

### Task 4: Generate, optimize, and register the 2050 art package

**Files:**
- Create: `frontend/src/assets/cinematic/scene-2050-award-ceremony.webp`
- Create: `frontend/src/assets/cinematic/xiaoyu-2050.webp`
- Create: `frontend/src/assets/cinematic/journalist-2050.webp`
- Create: `frontend/src/assets/cinematic/fragment-2050-award-trophy.webp`
- Modify: `frontend/src/stage/presentation.ts`
- Modify: `frontend/src/stage/fragmentPresentation.ts`
- Modify: both presentation registry tests

**Interfaces:**
- Produces: registered `scene_2050`, `xiaoyu_2050`, `journalist_2050`,
  `award_trophy_fragment`
- Produces: identity reference for Task 5 `xiaoyu-2050.webp`

- [x] **Step 1: Generate the 2050 ceremony**

```text
Use case: stylized-concept
Asset type: cinematic game master background
Primary request: 2050 Beijing national-theatre award ceremony honoring shadow-puppet heritage and memory technology, open ivory stage, crystal trophy at center, chronological photo-light wall on the left, restrained holographic shadow-puppet performance on the right, audience in emotional darkness below
Style/medium: cinematic realistic animated feature, plausible Chinese near future, elegant rather than glossy science fiction
Composition/framing: wide 2.39:1 stage; four hotspot zones clearly separated; dark lower-left subtitle safe area; right portrait safe area; mobile crop retains trophy and holographic stage
Lighting/mood: ivory white, ceremonial gold, restrained digital red; solemn forward-moving camera feeling
Constraints: no readable event title, no logos, no watermark, no clear presenter on stage, no fantasy palace, no excessive neon
```

- [x] **Step 2: Generate 48-year-old Xiaoyu**

```text
Use case: historical-scene
Asset type: cinematic game character plate
Primary request: 48-year-old Chinese woman in 2050, founder of a memory-restoration company and advocate for shadow-puppet heritage, mature and steady with restrained emotion when speaking about her grandfather, elegant contemporary formalwear with a subtle traditional cut-paper texture
Style/medium: cinematic realistic animated feature, same film world as 1972
Composition/framing: vertical half-body portrait on the right, dark negative space on the left
Lighting/mood: warm ceremonial key light with ivory-gold rim, dignified and human
Constraints: no logo, text, watermark, microphone covering face, crown, fantasy costume, extra people
```

- [x] **Step 3: Generate the 2050 journalist**

```text
Use case: stylized-concept
Asset type: cinematic game character plate
Primary request: thoughtful Chinese cultural journalist around 30 years old in 2050, professional but humane, carrying a compact plausible near-future recorder, listening closely rather than posing
Style/medium: cinematic realistic animated feature, restrained plausible near future
Composition/framing: vertical half-body portrait on the right, dark negative space on the left
Lighting/mood: ivory stage spill and soft digital-red rim
Constraints: no logos, text, watermark, helmet, cyberpunk implants, exaggerated holographic gadgets, extra people
```

- [x] **Step 4: Generate the trophy fragment**

```text
Use case: product-mockup
Asset type: cinematic memory fragment insert
Primary request: close-up of a refined crystal heritage award on a dark ceremonial pedestal, warm gold light refracting through the crystal into subtle rainbow bands, an abstract shadow-puppet silhouette reflected inside
Style/medium: cinematic realistic animated-feature prop close-up
Composition/framing: 4:3 landscape, trophy centered, caption-safe dark lower edge
Lighting/mood: warm, solemn, emotionally earned
Constraints: blank base with no readable engraving, no logo, no watermark, no brand trophy shape
```

- [x] **Step 5: Convert, test, register, and commit**

Convert with FFmpeg and enforce budgets. Add RED assertions for both distinct NPC IDs,
`ceremony` palette, and `award_trophy_fragment`; then add:

```ts
scene_2050: {
  id: 'scene_2050',
  eraLabel: '庚午年 · 典礼',
  locationLabel: '北京 · 国家大剧院',
  palette: 'ceremony',
  background: scene2050Background,
  portraits: {
    xiaoyu_2050: xiaoyu2050Portrait,
    journalist_2050: journalist2050Portrait,
  },
  alt: '2050年北京的非遗传承颁奖舞台，水晶奖杯、时光照片墙与全息皮影在象牙金灯光中彼此呼应。',
  composition: {
    desktopFocus: [0.5, 0.5],
    mobileFocus: [0.53, 0.48],
  },
},
```

Add the fragment entry:

```ts
award_trophy_fragment: {
  id: 'award_trophy_fragment',
  image: awardTrophy2050,
  alt: '折射暖金光晕的水晶奖杯，内部映出一枚皮影轮廓。',
  focus: '50% 48%',
},
```

Use imports named `scene2050Background`, `xiaoyu2050Portrait`,
`journalist2050Portrait`, and `awardTrophy2050`, each pointing to the exact filenames declared
in this task. Run tests/typecheck/build and commit:

```powershell
git add frontend/src/assets/cinematic/*2050*.webp frontend/src/stage/presentation.ts frontend/src/stage/fragmentPresentation.ts frontend/src/__tests__/scenePresentation.test.ts frontend/src/__tests__/fragmentPresentation.test.ts
git commit -m "feat: add 2050 cinematic art package"
```

---

### Task 5: Generate, optimize, and register the 2089 art package

**Files:**
- Create: `frontend/src/assets/cinematic/scene-2089-memory-lab.webp`
- Create: `frontend/src/assets/cinematic/xiaoyu-2089-projection.webp`
- Create: `frontend/src/assets/cinematic/fragment-2089-last-puppet.webp`
- Modify: `frontend/src/stage/presentation.ts`
- Modify: `frontend/src/stage/fragmentPresentation.ts`
- Modify: both registry tests

**Interfaces:**
- Consumes: `frontend/src/assets/cinematic/xiaoyu-2050.webp` as identity reference
- Produces: registered `scene_2089`, `xiaoyu`, `fragment_last_puppet`

- [x] **Step 1: Generate the 2089 memory laboratory**

```text
Use case: stylized-concept
Asset type: cinematic game master background
Primary request: 2089 Memory Healer laboratory in a deep ink-black space, comfortable neural-interface recliner at center, restrained medical-memory equipment, cyan and memory-purple light ribbons reconstructing four floating visual fragments: a 1972 shadow-puppet window, a 1990 green train, a 2024 rain window, and a 2050 crystal award; family photo on the right, heritage certificate archive on the left, last Monkey King shadow puppet near center
Style/medium: cinematic realistic animated feature moving into controlled surreal memory cinema, Chinese shadow-puppet silhouettes embedded in futuristic light
Composition/framing: wide 2.39:1; three hotspot objects remain distinct; lower-left subtitle safe area; right portrait safe area; mobile crop retains recliner and puppet
Lighting/mood: deep ink black, holographic cyan, memory purple, one warm amber memory core
Constraints: no clear human operator, no readable screens or certificate text, no logos, no watermark, no sterile white spaceship, no excessive HUD clutter
```

- [x] **Step 2: Generate young Xiaoyu as a projection from the 2050 identity**

Use `xiaoyu-2050.webp` as the identity reference:

```text
Use case: identity-preserve
Asset type: cinematic game character plate
Primary request: reconstruct the referenced woman as her university-age memory projection, preserving eye shape, nose, mouth and face proportions; she sits near a memory console holding a faded family photo, emotionally focused on saving her grandfather
Input images: Image 1 is the identity reference from age 48; preserve identity while making a natural younger adult version
Style/medium: cinematic realistic animated feature with subtle holographic edge breakup, scan-line translucency and drifting memory particles
Composition/framing: vertical half-body portrait on the right, dark negative space on the left
Lighting/mood: cyan and memory-purple rim with warm family-photo reflection
Constraints: clearly a projection, not a child; no text, logo, watermark, helmet, cyberpunk implants, extra people
```

- [x] **Step 3: Generate the final puppet fragment**

```text
Use case: illustration-story
Asset type: cinematic memory fragment insert
Primary request: exquisite handmade Monkey King Chinese shadow-puppet figure as the final object made by an elderly artisan, worn translucent leather, delicate carved patterns, tiny tool marks, warm amber memory glow inside a dark cyan-purple laboratory
Style/medium: cinematic realistic animated-feature macro prop
Composition/framing: 4:3 landscape, full puppet and staff visible, caption-safe dark edge
Lighting/mood: intimate, sacred and hopeful, final emotional reward
Constraints: no readable inscription, no logo, no watermark, no plastic toy appearance, no extra hands
```

- [x] **Step 4: Convert, test, register, and commit**

Convert with FFmpeg. Add RED assertions for the `xiaoyu` portrait, `memory` palette and
`fragment_last_puppet`; replace the old “2024/2089 returns null” test with:

```ts
expect(['scene_1972', 'scene_1990', 'scene_2024', 'scene_2050', 'scene_2089'].every(
  (id) => getScenePresentation(id) !== null,
)).toBe(true)
expect(getScenePresentation('unknown_scene')).toBeNull()
```

Register with:

```ts
scene_2089: {
  id: 'scene_2089',
  eraLabel: '记忆纪元 · 终幕',
  locationLabel: '深圳 · 拾忆实验室',
  palette: 'memory',
  background: scene2089Background,
  portraits: {
    xiaoyu: xiaoyu2089Projection,
  },
  alt: '2089年拾忆实验室，四个年代的记忆残片在神经接口躺椅上方重组，最后一枚孙悟空皮影守在暖色光核中。',
  composition: {
    desktopFocus: [0.5, 0.5],
    mobileFocus: [0.5, 0.49],
  },
},
```

Add:

```ts
fragment_last_puppet: {
  id: 'fragment_last_puppet',
  image: lastPuppet2089,
  alt: '陈守义最后制作的孙悟空皮影人偶，在青紫实验室中透出暖色记忆光。',
  focus: '50% 50%',
},
```

Use imports named `scene2089Background`, `xiaoyu2089Projection`, and
`lastPuppet2089`. Run tests, typecheck, and build, then commit:

```powershell
git add frontend/src/assets/cinematic/*2089*.webp frontend/src/stage/presentation.ts frontend/src/stage/fragmentPresentation.ts frontend/src/__tests__/scenePresentation.test.ts frontend/src/__tests__/fragmentPresentation.test.ts
git commit -m "feat: add 2089 cinematic art package"
```

---

### Task 6: Add fragment artwork to the memory-film popup

**Files:**
- Create: `frontend/src/components/FragmentArtwork.vue`
- Modify: `frontend/src/views/Game.vue`
- Modify: `frontend/src/styles/cinematic-game.css`
- Modify: `frontend/src/__tests__/fragmentPresentation.test.ts`

**Interfaces:**
- Consumes: `FragmentPresentation`
- Produces: `<FragmentArtwork :presentation="..." />`, self-hiding after image load failure

- [x] **Step 1: Complete the four-entry registry test**

Add:

```ts
it('registers exactly the four approved representative inserts', () => {
  const ids = [
    'train_ticket_fragment',
    'fragment_letter',
    'award_trophy_fragment',
    'fragment_last_puppet',
  ]
  expect(ids.every((id) => getFragmentPresentation(id) !== null)).toBe(true)
})
```

Run the focused test; it should already pass after Tasks 2–5 and protect the exact scope.

- [x] **Step 2: Create a focused image-error boundary component**

Create `FragmentArtwork.vue`:

```vue
<script setup lang="ts">
import { ref, watch } from 'vue'
import type { FragmentPresentation } from '../stage/fragmentPresentation'

const props = defineProps<{ presentation: FragmentPresentation }>()
const failed = ref(false)

watch(
  () => props.presentation.image,
  () => {
    failed.value = false
  },
)
</script>

<template>
  <figure v-if="!failed" class="fragment-artwork">
    <img
      :src="presentation.image"
      :alt="presentation.alt"
      :style="{ objectPosition: presentation.focus }"
      @error="failed = true"
    />
  </figure>
</template>
```

- [x] **Step 3: Wire the popup**

In `Game.vue`, import `computed` if not already present, `FragmentArtwork`, and
`getFragmentPresentation`. Add:

```ts
const popupPresentation = computed(() =>
  popupFragment.value ? getFragmentPresentation(popupFragment.value.id) : null,
)
```

Inside `.fragment-popup`, after `.fragment-serial`, render:

```vue
<FragmentArtwork
  v-if="popupPresentation"
  :presentation="popupPresentation"
/>
<div v-else class="popup-icon" aria-hidden="true"><i /></div>
```

Remove the unconditional legacy `.popup-icon`.

- [x] **Step 4: Add responsive cinematic insert styles**

Add `.fragment-artwork` rules: 16:9 visible frame, `max-height: 34vh`, one-pixel gold border,
dark gradient overlay, `object-fit: cover`; on max-width 900 px use `max-height: 26vh` and reduce
popup padding. Under reduced motion, disable image transitions.

- [x] **Step 5: Verify and commit**

Run fragment tests, all frontend tests, typecheck, lint, format check, and build. Commit:

```powershell
git add frontend/src/components/FragmentArtwork.vue frontend/src/views/Game.vue frontend/src/styles/cinematic-game.css frontend/src/stage/fragmentPresentation.ts frontend/src/__tests__/fragmentPresentation.test.ts
git commit -m "feat: add cinematic fragment inserts"
```

---

### Task 7: Give each era a distinct stage grade without breaking the film language

**Files:**
- Modify: `frontend/src/components/CinematicStage.vue`
- Modify: `frontend/src/stage/presentation.ts`
- Test: `frontend/src/__tests__/scenePresentation.test.ts`

**Interfaces:**
- Consumes: `CinematicPalette = 'amber' | 'rail' | 'rain' | 'ceremony' | 'memory'`
- Produces: `.palette-rail`, `.palette-rain`, `.palette-ceremony`, `.palette-memory`

- [x] **Step 1: Add a failing palette coverage assertion**

```ts
expect([
  getScenePresentation('scene_1972')?.palette,
  getScenePresentation('scene_1990')?.palette,
  getScenePresentation('scene_2024')?.palette,
  getScenePresentation('scene_2050')?.palette,
  getScenePresentation('scene_2089')?.palette,
]).toEqual(['amber', 'rail', 'rain', 'ceremony', 'memory'])
```

- [x] **Step 2: Add the palette grades**

Use only CSS gradients/blending:

- `rail`: smoky green midtones, warm lamp bloom, dark moving-edge vignette.
- `rain`: cool blue window cast, weak amber desk pool, tighter vignette.
- `ceremony`: ivory-gold center lift, restrained red edge, open vignette.
- `memory`: cyan-purple radial fragments with a small warm amber core.

Do not add new Canvas loops. Keep grain stopped under `prefers-reduced-motion`.

- [x] **Step 3: Verify and commit**

Run the focused test, typecheck and build, then commit:

```powershell
git add frontend/src/components/CinematicStage.vue frontend/src/stage/presentation.ts frontend/src/__tests__/scenePresentation.test.ts
git commit -m "feat: add cinematic era color grades"
```

---

### Task 8: Browser-QA all four eras and failure paths

> 自动化补充证据：14/14 WebP 经开发服务器返回 200 与 `image/webp`；
> Vitest 已覆盖场景资源失败回退旧插画、未知场景回退和碎片资源失败自隐藏。
> 这些证据不替代下面未完成的真实页面视觉步骤。

**Files:**
- Review: `frontend/src/stage/presentation.ts`
- Review: `frontend/src/components/CinematicStage.vue`
- Review: `frontend/src/components/FragmentArtwork.vue`
- Review: `frontend/src/styles/cinematic-game.css`
- Modify only when a recorded screenshot demonstrates a defect in the corresponding file.

**Interfaces:**
- Consumes: running frontend `http://127.0.0.1:5173`
- Consumes: running backend `http://127.0.0.1:8000`
- Produces: visual acceptance evidence for four eras and four viewports

- [x] **Step 1: Start or confirm local services**

Confirm `/` and `/api/health` both return 200. Start Vite and FastAPI in hidden windows only if
needed.

- [ ] **Step 2: Traverse the complete story in the in-app browser**

Use accessibility snapshots and exact role locators. From a new memory:

1. Inspect 1972, choose the first route.
2. Inspect 1990 background; open Chen and stranger portraits; trigger the train-ticket hotspot.
3. Choose the first route to 2024; inspect elderly Chen and letter insert.
4. Choose the first route to 2050; inspect Xiaoyu, journalist and trophy insert.
5. Choose the first route to 2089; inspect projection Xiaoyu and final-puppet insert.

Capture screenshots after each scene, each NPC portrait class, and each representative insert.

- [ ] **Step 3: Verify exact viewports with headless Edge through node_repl**

Use Playwright Core from the existing temporary QA module or install it under a validated
`%TEMP%\shiyi-playwright-mobile` path. Check:

- 390×844
- 768×1024
- 1440×900
- 1920×1080

For every scene, assert no page errors and visually inspect hotspot/portrait/subtitle/choice
overlap.

- [ ] **Step 4: Verify network failure fallbacks**

In isolated contexts, abort:

- each `scene-*.webp`: assert `.legacy-stage svg` exists and choices remain;
- one portrait WebP: assert dialogue header, textbox and close button remain;
- one fragment WebP: assert fragment title, description and continue button remain.

- [ ] **Step 5: Fix only observed defects and re-run focused checks**

For each defect, record viewport + scene + overlay, make the smallest scoped CSS/composition fix,
then repeat that exact screenshot before moving on.

- [ ] **Step 6: Commit browser acceptance fixes**

```powershell
git commit -m "fix: close later-era cinematic QA gaps"
```

Skip the commit if no files changed.

---

### Task 9: Run full quality gates and update product records

**Files:**
- Modify: `CHANGELOG.md`
- Modify: `TEST_REPORT.md`
- Modify: `UPGRADE_PLAN.md`
- Modify: `docs/superpowers/specs/2026-07-27-later-era-art-remaster-design.md`
- Modify: `docs/superpowers/plans/2026-07-27-later-era-art-remaster.md`

**Interfaces:**
- Produces: final acceptance record with exact asset sizes, tests and known limits

- [x] **Step 1: Run the frontend gate**

```powershell
cd frontend
npm run typecheck
npm run lint
npm run check
npm test
npm run build
npm audit --omit=dev --audit-level=high
```

Expected: all commands exit 0; audit may report the already documented low-severity esbuild
Windows dev-server advisory but no high severity.

- [x] **Step 2: Run backend/content/deployment gates**

```powershell
python scripts/validate_content.py
python -m compileall -q backend scripts
python -m pytest backend/tests -q
python -m alembic current
python -m alembic check
docker compose config --quiet
powershell -ExecutionPolicy Bypass -File scripts/smoke.ps1
```

Expected: 5 scenes/7 NPCs/17 fragments/17 hotspots/10 choices/4 endings; 168 backend tests;
Alembic head with no drift; Compose and smoke exit 0.

- [x] **Step 3: Record exact build and asset evidence**

Document:

- frontend test file/test count;
- Vite transformed-module count and Pixi chunk gzip size;
- all 14 WebP byte sizes and total;
- four browser viewports;
- background, portrait and fragment failure-path results;
- Docker daemon limitation if it remains unavailable.

Change the design spec status to “Completed and verified” and check every completed plan box.

- [x] **Step 4: Commit the acceptance record**

```powershell
git add CHANGELOG.md TEST_REPORT.md UPGRADE_PLAN.md docs/superpowers/specs/2026-07-27-later-era-art-remaster-design.md docs/superpowers/plans/2026-07-27-later-era-art-remaster.md
git commit -m "docs: record later-era cinematic acceptance"
```

- [x] **Step 5: Verify the final handoff**

```powershell
git status --porcelain
git log -8 --oneline
```

Expected: clean worktree with the local app still available at `http://127.0.0.1:5173/`.
