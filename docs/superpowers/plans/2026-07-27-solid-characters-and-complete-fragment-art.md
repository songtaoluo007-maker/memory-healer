# 实体人物与全交互物美术 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把七名可对话人物升级为带透明通道的实体角色层，并为全部十七个
canonical fragment ID 提供独立电影特写，同时确保五幕背景中的交互物可辨认。

**Architecture:** 后端内容与规则保持不变；`ScenePresentation` 继续按 NPC ID 映射
人物资源，`FragmentPresentation` 扩展为十七条纯展示映射。人物和碎片资产由内置
imagegen 生成、FFmpeg 转换为 WebP，并由独立 Python/Pillow 校验器检查透明通道、
宽高比和体积；Vue/Pixi 只负责当前场景展示与降级。

**Tech Stack:** Vue 3、TypeScript 6、PixiJS 8、Vitest、Vite、Python 3.12、
Pillow 11.3、内置 imagegen、FFmpeg 8.1/libwebp。

## Global Constraints

- 设计规格：`docs/superpowers/specs/2026-07-27-solid-characters-and-complete-fragment-art-design.md`。
- 不修改 canonical scene/NPC/fragment/hotspot/choice ID、后端规则或存档 schema。
- 七个人物最终使用有实际透明像素的 WebP；普通人物主体 `opacity: 1`。
- 只允许人物脚部约 8%—12% 渐隐；不得使用横向大面积 `mask-image`。
- 2089 小雨主体不透明度不低于 0.88，只在边缘表现记忆投影。
- 十七个 fragment ID 全部具有独立 4:3 特写；未知 ID 安全返回 `null`。
- 生成图片不得包含可读假文字、乱码、Logo、水印或无关人物。
- 人物单张不超过 800 KB；碎片单张不超过 600 KB。
- 主背景仅在物件缺失或完全不可辨认时做局部编辑，不整体重生成合格背景。
- 当前场景之外的人物和碎片不主动预加载；不新增 Canvas 动画循环。
- `prefers-reduced-motion` 下人物只即时显隐。
- 使用内置 imagegen；每个资产单独调用，最终选择源图保留在生成目录。
- 生成输入图必须先用 `view_image` 检查；身份参考使用本地绝对路径。
- 不启用子代理，除非用户在执行选择中明确要求。

---

### Task 1: Add deterministic cinematic asset validation

**Files:**
- Modify: `requirements.txt`
- Create: `scripts/validate_cinematic_assets.py`
- Create: `backend/tests/test_cinematic_assets.py`

**Interfaces:**
- Produces: `validate_portrait(path: Path) -> list[str]`
- Produces: `validate_fragment(path: Path) -> list[str]`
- Produces: CLI flags `--portrait PATH` and `--fragment PATH`, repeatable
- Enforces: WebP format, actual alpha range, aspect ratio, and byte budgets

- [ ] **Step 1: Write failing validator tests**

Create `backend/tests/test_cinematic_assets.py` with synthetic images:

```python
from pathlib import Path

from PIL import Image

from scripts.validate_cinematic_assets import validate_fragment, validate_portrait


def save_rgba(path: Path, size: tuple[int, int], alpha: int) -> None:
    Image.new("RGBA", size, (120, 90, 60, alpha)).save(path, "WEBP", lossless=True)


def test_transparent_portrait_passes(tmp_path: Path) -> None:
    path = tmp_path / "portrait.webp"
    image = Image.new("RGBA", (600, 1000), (0, 0, 0, 0))
    image.paste((120, 90, 60, 255), (180, 100, 500, 950))
    image.save(path, "WEBP", lossless=True)
    assert validate_portrait(path) == []


def test_opaque_portrait_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "portrait.webp"
    save_rgba(path, (600, 1000), 255)
    assert "portrait must contain transparent pixels" in validate_portrait(path)


def test_fragment_requires_four_by_three_and_budget(tmp_path: Path) -> None:
    path = tmp_path / "fragment.webp"
    Image.new("RGB", (1200, 900), (40, 30, 20)).save(path, "WEBP", quality=80)
    assert validate_fragment(path) == []


def test_fragment_rejects_wrong_aspect_ratio(tmp_path: Path) -> None:
    path = tmp_path / "fragment.webp"
    Image.new("RGB", (1600, 900), (40, 30, 20)).save(path, "WEBP", quality=80)
    assert "fragment aspect ratio must be 4:3 ± 0.03" in validate_fragment(path)
```

- [ ] **Step 2: Run tests and verify RED**

Run:

```powershell
python -m pytest backend/tests/test_cinematic_assets.py -q
```

Expected: collection fails because `scripts.validate_cinematic_assets` does not exist.

- [ ] **Step 3: Add Pillow and implement the validator**

Add to `requirements.txt`:

```text
Pillow==11.3.0
```

Create `scripts/validate_cinematic_assets.py`:

```python
from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image

PORTRAIT_BUDGET = 800_000
FRAGMENT_BUDGET = 600_000


def _common_errors(path: Path, budget: int) -> tuple[list[str], Image.Image | None]:
    errors: list[str] = []
    if not path.is_file():
        return [f"asset does not exist: {path}"], None
    if path.stat().st_size > budget:
        errors.append(f"asset exceeds {budget} bytes")
    try:
        image = Image.open(path)
        image.load()
    except Exception as exc:
        return [f"asset cannot be decoded: {exc}"], None
    if image.format != "WEBP":
        errors.append("asset must be WebP")
    return errors, image


def validate_portrait(path: Path) -> list[str]:
    errors, image = _common_errors(path, PORTRAIT_BUDGET)
    if image is None:
        return errors
    if image.height <= image.width:
        errors.append("portrait must be vertical")
    if "A" not in image.getbands():
        errors.append("portrait must contain an alpha channel")
        return errors
    alpha = image.getchannel("A")
    minimum, maximum = alpha.getextrema()
    if minimum > 16:
        errors.append("portrait must contain transparent pixels")
    if maximum < 240:
        errors.append("portrait subject must contain opaque pixels")
    transparent = sum(value <= 16 for value in alpha.resize((64, 64)).getdata())
    if transparent / (64 * 64) < 0.18:
        errors.append("portrait transparent area must be at least 18%")
    return errors


def validate_fragment(path: Path) -> list[str]:
    errors, image = _common_errors(path, FRAGMENT_BUDGET)
    if image is None:
        return errors
    ratio = image.width / image.height
    if abs(ratio - 4 / 3) > 0.03:
        errors.append("fragment aspect ratio must be 4:3 ± 0.03")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--portrait", action="append", default=[])
    parser.add_argument("--fragment", action="append", default=[])
    args = parser.parse_args()
    failures: list[str] = []
    for raw in args.portrait:
        path = Path(raw)
        failures.extend(f"{path}: {error}" for error in validate_portrait(path))
    for raw in args.fragment:
        path = Path(raw)
        failures.extend(f"{path}: {error}" for error in validate_fragment(path))
    if failures:
        print("\n".join(failures))
        return 1
    print(f"Validated {len(args.portrait)} portraits and {len(args.fragment)} fragments.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run focused tests and compile**

Run:

```powershell
python -m pytest backend/tests/test_cinematic_assets.py -q
python -m compileall -q scripts/validate_cinematic_assets.py
```

Expected: 4 tests pass; compile exits 0.

- [ ] **Step 5: Commit the validator**

```powershell
git add requirements.txt scripts/validate_cinematic_assets.py backend/tests/test_cinematic_assets.py
git commit -m "test: add cinematic asset validation"
```

---

### Task 2: Generate and register seven solid character plates

**Files:**
- Create: `frontend/src/assets/cinematic/chen-shouyi-1972-solid.webp`
- Create: `frontend/src/assets/cinematic/chen-shouyi-1990-solid.webp`
- Create: `frontend/src/assets/cinematic/stranger-1990-solid.webp`
- Create: `frontend/src/assets/cinematic/chen-shouyi-2024-solid.webp`
- Create: `frontend/src/assets/cinematic/xiaoyu-2050-solid.webp`
- Create: `frontend/src/assets/cinematic/journalist-2050-solid.webp`
- Create: `frontend/src/assets/cinematic/xiaoyu-2089-projection-solid.webp`
- Modify: `frontend/src/stage/presentation.ts`
- Modify: `frontend/src/__tests__/scenePresentation.test.ts`
- Delete after successful replacement: the seven superseded portrait files currently imported by `presentation.ts`

**Interfaces:**
- Consumes: existing portraits as identity, age, costume, and lighting references
- Consumes: `validate_portrait(path: Path) -> list[str]`
- Produces: seven vertical alpha WebP character plates
- Produces: unchanged `ScenePresentation.portraits` canonical ID mapping

- [ ] **Step 1: Write the failing solid-portrait registry assertions**

Update `frontend/src/__tests__/scenePresentation.test.ts` so the seven mappings contain
`-solid`:

```ts
const solidPortraits = [
  getScenePresentation('scene_1972')?.portraits.chen_shouyi_young,
  getScenePresentation('scene_1990')?.portraits.chen_shouyi_1990,
  getScenePresentation('scene_1990')?.portraits.stranger_1990,
  getScenePresentation('scene_2024')?.portraits.chen_shouyi_old,
  getScenePresentation('scene_2050')?.portraits.xiaoyu_2050,
  getScenePresentation('scene_2050')?.portraits.journalist_2050,
  getScenePresentation('scene_2089')?.portraits.xiaoyu,
]
expect(solidPortraits).toHaveLength(7)
expect(solidPortraits.every((portrait) => portrait?.includes('-solid'))).toBe(true)
expect(new Set(solidPortraits).size).toBe(7)
```

- [ ] **Step 2: Run the registry test and verify RED**

```powershell
cd frontend
npm test -- --run src/__tests__/scenePresentation.test.ts
```

Expected: the `-solid` assertion fails for all current mappings.

- [ ] **Step 3: Inspect all seven identity references**

Use `view_image` with original detail on:

```text
frontend/src/assets/cinematic/chen-shouyi-1972.png
frontend/src/assets/cinematic/chen-shouyi-1990.webp
frontend/src/assets/cinematic/stranger-1990.webp
frontend/src/assets/cinematic/chen-shouyi-2024.webp
frontend/src/assets/cinematic/xiaoyu-2050.webp
frontend/src/assets/cinematic/journalist-2050.webp
frontend/src/assets/cinematic/xiaoyu-2089-projection.webp
```

Record face shape, clothing, pose, lighting, and unwanted baked background before generation.

- [ ] **Step 4: Generate 25-year-old Chen Shouyi**

Call built-in imagegen once with the current 1972 portrait as reference:

```text
Use case: identity-preserve
Asset type: isolated cinematic game character sprite with true transparent alpha background
Primary request: preserve the referenced 25-year-old Chinese shadow-puppet artisan Chen Shouyi exactly—same face proportions, eyes, nose, mouth, work-worn hands and restrained determined expression—now shown as a grounded three-quarter-body standing character wearing the same period-correct 1972 blue-gray padded work jacket
Input images: Image 1 is the identity, age, costume and film-world reference
Style/medium: cinematic realistic animated feature, tactile cloth and skin, grounded physical presence
Composition/framing: vertical 3:5, full head, both shoulders, torso, hands and upper legs visible, character on the right half looking slightly left
Lighting/mood: warm 1972 window key light with subtle cool alley rim and natural contact shadow under the lower body
Background: true transparent background with alpha channel, no scenery, no wall, no floor, no gradient, no shadow rectangle
Constraints: one person only, no text, logo, watermark, props covering face, cropped hands, fog, ghost transparency or hologram effects
```

- [ ] **Step 5: Generate 43-year-old Chen Shouyi**

Use both the current 1972 and 1990 portraits as references:

```text
Use case: identity-preserve
Asset type: isolated cinematic game character sprite with true transparent alpha background
Primary request: preserve Chen Shouyi as the same man naturally aged to 43 in 1990—same eyes, nose, mouth, cheekbone structure and artisan hands—standing with a worn shadow-puppet wooden trunk held close to his side, hesitant yet determined, wearing an aged blue-gray worker jacket
Input images: Image 1 is the young identity anchor; Image 2 is the approved 1990 age, clothing and mood reference
Style/medium: cinematic realistic animated feature, tactile period fabric and wood, grounded physical presence
Composition/framing: vertical 3:5, three-quarter body, full head, both shoulders, hands and upper legs visible, character on the right half looking slightly left
Lighting/mood: smoky station tungsten key, muted green rail bounce, narrow warm rim
Background: true transparent background with alpha channel, no station, train, platform, scenery, floor or gradient
Constraints: one person only, no readable marks on trunk, no text, logo, watermark, cropped hands, fog, ghost transparency or hologram effects
```

- [ ] **Step 6: Generate the 1990 platform stranger**

Use the current stranger portrait as reference:

```text
Use case: identity-preserve
Asset type: isolated cinematic game character sprite with true transparent alpha background
Primary request: preserve the referenced thoughtful 28-year-old Chinese southbound traveler exactly—same face, hair and observant humane expression—now standing naturally with one hand near a simple travel bag, wearing the same plausible early-1990s jacket
Input images: Image 1 is the identity, clothing and lighting reference
Style/medium: cinematic realistic animated feature, period-authentic fabric, grounded physical presence
Composition/framing: vertical 3:5, three-quarter body, full head, both shoulders, hands and upper legs visible, character on the right half listening toward the left
Lighting/mood: smoky station tungsten key, dark green ambient fill and restrained red-brown rim
Background: true transparent background with alpha channel, no station, train, scenery, floor or gradient
Constraints: one person only, no earbuds, modern phone, logos, text, watermark, cropped hands, fog, ghost transparency or hologram effects
```

- [ ] **Step 7: Generate 77-year-old Chen Shouyi**

Use the 1972 identity anchor and current 2024 portrait:

```text
Use case: identity-preserve
Asset type: isolated cinematic game character sprite with true transparent alpha background
Primary request: preserve Chen Shouyi as the same man naturally aged to 77 in 2024—same eyes, nose, mouth and cheekbone structure—with gray hair, a slight artisan stoop and one old carving knife held safely downward, struggling to remember rather than simply grieving
Input images: Image 1 is the young identity anchor; Image 2 is the approved elderly age, expression and costume reference
Style/medium: cinematic realistic animated feature, detailed aged skin, worn knit and work cloth, grounded physical presence
Composition/framing: vertical 3:5, three-quarter body, full head, shoulders, hands and upper legs visible, character on the right half looking slightly left
Lighting/mood: cool rain-window rim with a weak amber workbench key
Background: true transparent background with alpha channel, no room, window, scenery, floor or gradient
Constraints: one person only, carving knife not raised, no text, logo, watermark, cropped hands, fog, ghost transparency or hologram effects
```

- [ ] **Step 8: Generate 48-year-old Xiaoyu**

Use the current 2050 portrait:

```text
Use case: identity-preserve
Asset type: isolated cinematic game character sprite with true transparent alpha background
Primary request: preserve the referenced 48-year-old Chinese woman Xiaoyu exactly—same eye shape, nose, mouth, face proportions, mature steady expression and elegant black formalwear with subtle traditional cut-paper texture—now shown as a grounded standing three-quarter-body character
Input images: Image 1 is the identity, age, costume and lighting reference
Style/medium: cinematic realistic animated feature, dignified tactile fabric and natural skin, grounded physical presence
Composition/framing: vertical 3:5, full head, both shoulders, hands and upper legs visible, character on the right half looking slightly left
Lighting/mood: warm ivory-gold ceremony key, restrained digital-red rim and natural lower-body contact shadow
Background: true transparent background with alpha channel, no stage, shadow screen, scenery, floor or gradient
Constraints: one person only, no microphone, crown, logo, text, watermark, cropped hands, fog, ghost transparency or hologram effects
```

- [ ] **Step 9: Generate the 2050 journalist**

Use the current journalist portrait:

```text
Use case: identity-preserve
Asset type: isolated cinematic game character sprite with true transparent alpha background
Primary request: preserve the referenced thoughtful Chinese cultural journalist around 30 exactly—same face, hair and attentive humane expression—standing with a compact plausible near-future recorder lowered near his waist, listening instead of posing
Input images: Image 1 is the identity, clothing, recorder and lighting reference
Style/medium: cinematic realistic animated feature, restrained plausible near future, grounded physical presence
Composition/framing: vertical 3:5, three-quarter body, full head, shoulders, hands and upper legs visible, character on the right half leaning subtly toward the left
Lighting/mood: ivory stage spill with a soft digital-red rim and natural contact shadow
Background: true transparent background with alpha channel, no auditorium, stage, scenery, floor or gradient
Constraints: one person only, no earbuds, logos, text, watermark, helmet, implants, cropped hands, fog, ghost transparency or exaggerated gadgets
```

- [ ] **Step 10: Generate young Xiaoyu as a solid memory projection**

Use current 2050 Xiaoyu and 2089 projection portraits:

```text
Use case: identity-preserve
Asset type: isolated cinematic game character sprite with true transparent alpha background
Primary request: preserve Xiaoyu as the same woman reconstructed at a natural university age of 22—same eye shape, nose, mouth and face proportions—standing beside an implied memory console while holding a faded family photo, emotionally focused on saving her grandfather; her face, clothing and body are physically clear and nearly opaque
Input images: Image 1 is the age-48 identity anchor; Image 2 is the approved young projection, costume, family-photo and color reference
Style/medium: cinematic realistic animated feature with only subtle cyan-purple holographic edge breakup and a few memory particles
Composition/framing: vertical 3:5, three-quarter body, full head, shoulders, hands and upper legs visible, character on the right half looking slightly left
Lighting/mood: cyan and memory-purple rim with warm family-photo reflection
Background: true transparent background with alpha channel, no laboratory, console body, scenery, floor or gradient
Constraints: clearly an adult projection; body and face at least 90% visually opaque; one person only; no text, logo, watermark, helmet, implants, cropped hands, fog or full-body ghost transparency
```

- [ ] **Step 11: Convert and validate all seven portraits**

For each selected PNG, convert with alpha preserved:

```powershell
ffmpeg -loglevel error -y -i "<selected-source.png>" -an -c:v libwebp -quality 90 -compression_level 6 -preset picture -pix_fmt yuva420p "<solid-output.webp>"
```

Run:

```powershell
python scripts/validate_cinematic_assets.py `
  --portrait frontend/src/assets/cinematic/chen-shouyi-1972-solid.webp `
  --portrait frontend/src/assets/cinematic/chen-shouyi-1990-solid.webp `
  --portrait frontend/src/assets/cinematic/stranger-1990-solid.webp `
  --portrait frontend/src/assets/cinematic/chen-shouyi-2024-solid.webp `
  --portrait frontend/src/assets/cinematic/xiaoyu-2050-solid.webp `
  --portrait frontend/src/assets/cinematic/journalist-2050-solid.webp `
  --portrait frontend/src/assets/cinematic/xiaoyu-2089-projection-solid.webp
```

Expected: `Validated 7 portraits and 0 fragments.` If any image lacks alpha or exceeds budget,
reject it and call imagegen again with only that defect named.

- [ ] **Step 12: Register the seven solid portraits**

Update imports and canonical mappings in `frontend/src/stage/presentation.ts` to the seven
`-solid.webp` filenames. Do not change NPC IDs or scene composition data.

- [ ] **Step 13: Verify, remove superseded portraits, and commit**

Run:

```powershell
cd frontend
npm test -- --run src/__tests__/scenePresentation.test.ts
npm run typecheck
npm run build
```

After all three pass, remove only the seven old portrait files no longer imported. They remain
recoverable from Git history. Commit:

```powershell
git add frontend/src/assets/cinematic frontend/src/stage/presentation.ts frontend/src/__tests__/scenePresentation.test.ts
git commit -m "feat: replace portraits with solid character plates"
```

---

### Task 3: Replace ghost blending with grounded character staging

**Files:**
- Modify: `frontend/src/components/CinematicStage.vue`
- Modify: `frontend/src/__tests__/cinematicStageFallback.test.ts`

**Interfaces:**
- Consumes: seven alpha WebP mappings from Task 2
- Produces: `data-character-treatment="solid" | "projection"`
- Keeps: image failure independent from background and dialogue state

- [ ] **Step 1: Write failing treatment tests**

Extend `cinematicStageFallback.test.ts`:

```ts
it('marks ordinary characters as solid physical layers', async () => {
  const host = mountStage('scene_1990', 'stranger_1990')
  await nextTick()
  expect(host.querySelector('.character-portrait')?.getAttribute('data-character-treatment')).toBe(
    'solid',
  )
})

it('marks 2089 Xiaoyu as the restrained projection exception', async () => {
  const host = mountStage('scene_2089', 'xiaoyu')
  await nextTick()
  expect(host.querySelector('.character-portrait')?.getAttribute('data-character-treatment')).toBe(
    'projection',
  )
})
```

Refactor the test's repeated mount code into:

```ts
const mountStage = (sceneId: string, activeNpcId?: string) => {
  const host = document.createElement('div')
  app = createApp({
    render: () =>
      h(
        CinematicStage,
        { sceneId, activeNpcId },
        { default: () => h('div', { class: 'legacy-art' }, 'legacy illustration') },
      ),
  })
  app.mount(host)
  return host
}
```

- [ ] **Step 2: Run focused tests and verify RED**

```powershell
cd frontend
npm test -- --run src/__tests__/cinematicStageFallback.test.ts
```

Expected: treatment attributes are `null`.

- [ ] **Step 3: Add treatment semantics**

In `CinematicStage.vue`:

```ts
const characterTreatment = computed(() =>
  props.sceneId === 'scene_2089' && props.activeNpcId === 'xiaoyu' ? 'projection' : 'solid',
)
```

Bind it:

```vue
<img
  v-if="activePortrait"
  class="character-portrait"
  :data-character-treatment="characterTreatment"
  :src="activePortrait"
  alt=""
  aria-hidden="true"
/>
```

- [ ] **Step 4: Replace the portrait CSS**

Replace the current `.character-portrait` rules with:

```css
.character-portrait {
  position: absolute;
  right: clamp(-2.5rem, -1vw, -0.5rem);
  bottom: -2vh;
  width: min(34vw, 30rem);
  height: 88vh;
  object-fit: contain;
  object-position: bottom right;
  opacity: 1;
  filter:
    drop-shadow(-1.25rem 1.5rem 1.6rem rgba(0, 0, 0, 0.52))
    drop-shadow(-0.15rem 0 0.45rem rgba(224, 177, 103, 0.18));
  mask-image: linear-gradient(to bottom, #000 0%, #000 88%, transparent 100%);
  pointer-events: none;
}

.character-portrait[data-character-treatment='projection'] {
  opacity: 0.92;
  filter:
    drop-shadow(-1rem 1.4rem 1.5rem rgba(0, 0, 0, 0.46))
    drop-shadow(0 0 0.65rem rgba(96, 198, 221, 0.24))
    drop-shadow(0 0 1.15rem rgba(139, 92, 196, 0.2));
}
```

Change the portrait transition to use only a short horizontal movement and opacity; remove
`blur(8px)`.

For max-aspect-ratio `4/5`, use:

```css
.character-portrait {
  right: -3.5rem;
  bottom: 20vh;
  width: min(68vw, 24rem);
  height: 61vh;
}
```

Keep reduced-motion transition disabled.

- [ ] **Step 5: Verify and commit**

```powershell
cd frontend
npm test -- --run src/__tests__/cinematicStageFallback.test.ts
npm run typecheck
npm run lint
npm run check
npm run build
git add src/components/CinematicStage.vue src/__tests__/cinematicStageFallback.test.ts
git commit -m "feat: ground characters as solid scene actors"
```

---

### Task 4: Add the three missing 1972 fragment inserts

**Files:**
- Create: `frontend/src/assets/cinematic/fragment-1972-shadow-stage.webp`
- Create: `frontend/src/assets/cinematic/fragment-1972-carving-knife.webp`
- Create: `frontend/src/assets/cinematic/fragment-1972-three-kings.webp`
- Modify: `frontend/src/stage/fragmentPresentation.ts`
- Modify: `frontend/src/__tests__/fragmentPresentation.test.ts`

**Interfaces:**
- Produces: presentations for `fragment_shadow_puppet`, `fragment_grandpa_knife`,
  `fragment_three_kings`

- [ ] **Step 1: Add failing 1972 registry assertions**

```ts
it('registers all three 1972 interaction inserts', () => {
  const expected = {
    fragment_shadow_puppet: 'fragment-1972-shadow-stage',
    fragment_grandpa_knife: 'fragment-1972-carving-knife',
    fragment_three_kings: 'fragment-1972-three-kings',
  }
  for (const [id, filename] of Object.entries(expected)) {
    expect(getFragmentPresentation(id)?.image).toContain(filename)
  }
})
```

Run and expect three `undefined` failures:

```powershell
cd frontend
npm test -- --run src/__tests__/fragmentPresentation.test.ts
```

- [ ] **Step 2: Generate the shadow-puppet stage**

```text
Use case: illustration-story
Asset type: cinematic memory fragment insert
Primary request: close view of a 1972 Xi'an handmade shadow-puppet screen glowing behind warm parchment, delicate leather figures mid-performance, bamboo control rods and an artisan silhouette visible only as hands and shoulders
Style/medium: cinematic realistic animated-feature prop close-up, tactile paper, leather and dust
Composition/framing: 4:3 landscape, illuminated screen centered, dark caption-safe lower edge
Lighting/mood: warm amber lamp, intimate winter workshop, beginning of a lifelong craft
Constraints: no readable text, logo, watermark, modern equipment, clear extra face or fantasy palace
```

- [ ] **Step 3: Generate the carving knife and toolbox**

```text
Use case: product-mockup
Asset type: cinematic memory fragment insert
Primary request: elderly artisan's well-used Chinese shadow-puppet carving knife resting across an open 1972 wooden toolbox, worn handle polished by decades of fingers, tiny leather shavings and awls arranged with care
Style/medium: cinematic realistic animated-feature macro prop, historically plausible hand tools
Composition/framing: 4:3 landscape, knife and toolbox centered, caption-safe dark lower edge
Lighting/mood: narrow warm work-lamp pool against cool winter shadow, humble and sacred
Constraints: no hands, blood, readable labels, logo, watermark, modern power tools or plastic case
```

- [ ] **Step 4: Generate the Three Heroes versus Lü Bu figures**

```text
Use case: illustration-story
Asset type: cinematic memory fragment insert
Primary request: four exquisite handmade Chinese shadow-puppet figures representing the Three Heroes battling Lu Bu, translucent dyed leather, articulated joints and fine carved patterns, arranged as a dramatic frozen stage composition
Style/medium: cinematic realistic animated-feature puppet close-up grounded in Shaanxi shadow-play craft
Composition/framing: 4:3 landscape, all four full figures and weapons readable, dark caption-safe edge
Lighting/mood: warm backlit parchment, heroic but handmade, faint workshop dust
Constraints: no readable title, logo, watermark, realistic human actors, plastic toys or missing limbs
```

- [ ] **Step 5: Convert, validate, register, and commit**

Convert each selected source to its declared WebP with the Task 2 FFmpeg settings except
`-pix_fmt yuva420p` is omitted. Run:

```powershell
python scripts/validate_cinematic_assets.py `
  --fragment frontend/src/assets/cinematic/fragment-1972-shadow-stage.webp `
  --fragment frontend/src/assets/cinematic/fragment-1972-carving-knife.webp `
  --fragment frontend/src/assets/cinematic/fragment-1972-three-kings.webp
```

Register:

```ts
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
```

Then:

```powershell
cd frontend
npm test -- --run src/__tests__/fragmentPresentation.test.ts
npm run typecheck
npm run build
git add src/assets/cinematic/fragment-1972-*.webp src/stage/fragmentPresentation.ts src/__tests__/fragmentPresentation.test.ts
git commit -m "feat: add 1972 fragment art set"
```

---

### Task 5: Add the three missing 1990 fragment inserts

**Files:**
- Create: `frontend/src/assets/cinematic/fragment-1990-puppet-trunk.webp`
- Create: `frontend/src/assets/cinematic/fragment-1990-farewell-letter.webp`
- Create: `frontend/src/assets/cinematic/fragment-1990-station-clock.webp`
- Modify: registry and registry tests

**Interfaces:**
- Produces: `puppet_trunk_fragment`, `farewell_letter_fragment`,
  `station_clock_fragment`

- [ ] **Step 1: Add failing 1990 assertions**

Add:

```ts
it('registers all three additional 1990 interaction inserts', () => {
  const expected = {
    puppet_trunk_fragment: 'fragment-1990-puppet-trunk',
    farewell_letter_fragment: 'fragment-1990-farewell-letter',
    station_clock_fragment: 'fragment-1990-station-clock',
  }
  for (const [id, filename] of Object.entries(expected)) {
    expect(getFragmentPresentation(id)?.image).toContain(filename)
  }
})
```

Run:

```powershell
cd frontend
npm test -- --run src/__tests__/fragmentPresentation.test.ts
```

Expected: three filename assertions fail because the entries do not exist.

- [ ] **Step 2: Generate the puppet trunk**

```text
Use case: product-mockup
Asset type: cinematic memory fragment insert
Primary request: battered handmade wooden trunk carrying Chinese shadow-puppet figures on a 1990 southbound railway platform, rope handle, worn brass corners and one translucent leather puppet visible beneath a half-open lid
Style/medium: cinematic realistic animated-feature prop close-up, period-authentic wood and rail grime
Composition/framing: 4:3 landscape, trunk centered, green train softly behind, caption-safe dark lower edge
Lighting/mood: smoky green station light with one warm tungsten lamp, departure and uncertainty
Constraints: no readable labels, logo, watermark, modern suitcase, clear people or plastic toy appearance
```

- [ ] **Step 3: Generate the unsent farewell letter**

```text
Use case: illustration-story
Asset type: cinematic memory fragment insert
Primary request: an unsent 1990 farewell letter to an old shadow-puppet master, folded beside a simple fountain pen and a small leather puppet cutting on a weathered station bench
Style/medium: cinematic realistic animated-feature paper and prop close-up
Composition/framing: 4:3 landscape, folded letter centered, green train blur behind, dark caption-safe edge
Lighting/mood: restrained tungsten warmth in smoky rail-station green, regret held back
Constraints: paper contains only abstract non-readable ink strokes, no legible Chinese, stamps, logo, watermark, modern objects or hands
```

- [ ] **Step 4: Generate the station clock**

```text
Use case: historical-scene
Asset type: cinematic memory fragment insert
Primary request: large weathered analog railway-platform clock in 1990 Shenzhen seen through drifting steam, cream dial, black hands and chipped dark-green metal housing above the last southbound crowd
Style/medium: cinematic realistic animated-feature architectural prop close-up
Composition/framing: 4:3 landscape, clock centered high, platform lights below, caption-safe dark lower edge
Lighting/mood: smoky green dusk, tungsten halo, time moving faster than memory
Constraints: no readable station name, numbers may be simple clock indices only, no logo, watermark, digital display or modern signage
```

- [ ] **Step 5: Convert, validate, register, and commit**

Use imports `puppetTrunk1990`, `farewellLetter1990`, `stationClock1990`. Register:

```ts
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
```

Run the validator for the three files, focused tests, typecheck and build. Commit:

```powershell
git commit -m "feat: add 1990 fragment art set"
```

---

### Task 6: Add the two missing 2024 fragment inserts

**Files:**
- Create: `frontend/src/assets/cinematic/fragment-2024-old-photos.webp`
- Create: `frontend/src/assets/cinematic/fragment-2024-last-show-poster.webp`
- Modify: registry and registry tests

**Interfaces:**
- Produces: `fragment_old_photos`, `fragment_last_show`

- [ ] **Step 1: Add failing 2024 assertions and verify RED**

Add:

```ts
it('registers both additional 2024 interaction inserts', () => {
  const expected = {
    fragment_old_photos: 'fragment-2024-old-photos',
    fragment_last_show: 'fragment-2024-last-show-poster',
  }
  for (const [id, filename] of Object.entries(expected)) {
    expect(getFragmentPresentation(id)?.image).toContain(filename)
  }
})
```

Run the focused fragment test. Expected: two filename assertions fail.

- [ ] **Step 2: Generate the yellowed performance photos**

```text
Use case: illustration-story
Asset type: cinematic memory fragment insert
Primary request: a small stack of yellowed Chinese shadow-puppet performance photographs from several decades, curled corners, fingerprints and one image showing only an elderly artisan silhouette behind a glowing screen
Style/medium: cinematic realistic animated-feature archival prop close-up
Composition/framing: 4:3 landscape, overlapping photos centered on a worn 2024 workbench, caption-safe dark edge
Lighting/mood: cool rain-window blue crossed by a weak amber desk lamp, tender and lonely
Constraints: no readable captions, logos, watermark, clear modern celebrity faces or pristine new prints
```

- [ ] **Step 3: Generate the final-show poster**

```text
Use case: product-mockup
Asset type: cinematic memory fragment insert
Primary request: faded final-performance poster for a traditional Chinese shadow-puppet troupe, handmade paper, red-black puppet silhouettes, pin holes, rain stains and a torn lower corner on an old workshop wall
Style/medium: cinematic realistic animated-feature paper prop close-up
Composition/framing: 4:3 landscape, poster centered with worn wall edge visible, dark caption-safe lower edge
Lighting/mood: cold 2024 rain-window cast with one dying amber bulb, an era ending quietly
Constraints: absolutely no readable title, dates or venue text; use only abstract ink blocks and puppet shapes; no logo or watermark
```

- [ ] **Step 4: Convert, validate, register, and commit**

Register:

```ts
fragment_old_photos: {
  id: 'fragment_old_photos',
  image: oldPhotos2024,
  alt: '卷边泛黄的皮影演出剧照铺在旧工作台上，雨夜蓝光切过照片边缘。',
  focus: '50% 50%',
},
fragment_last_show: {
  id: 'fragment_last_show',
  image: lastShowPoster2024,
  alt: '最后一场演出的旧海报只剩皮影轮廓、雨渍与被岁月磨掉的字块。',
  focus: '50% 48%',
},
```

Validate both, run focused tests/typecheck/build, and commit:

```powershell
git commit -m "feat: add 2024 fragment art set"
```

---

### Task 7: Add the three missing 2050 fragment inserts

**Files:**
- Create: `frontend/src/assets/cinematic/fragment-2050-photo-wall.webp`
- Create: `frontend/src/assets/cinematic/fragment-2050-hologram-stage.webp`
- Create: `frontend/src/assets/cinematic/fragment-2050-audience-tears.webp`
- Modify: registry and registry tests

**Interfaces:**
- Produces: `old_photos_wall_fragment`, `hologram_stage_fragment`,
  `audience_reactions_fragment`

- [ ] **Step 1: Add failing 2050 assertions and verify RED**

Add:

```ts
it('registers all three additional 2050 interaction inserts', () => {
  const expected = {
    old_photos_wall_fragment: 'fragment-2050-photo-wall',
    hologram_stage_fragment: 'fragment-2050-hologram-stage',
    audience_reactions_fragment: 'fragment-2050-audience-tears',
  }
  for (const [id, filename] of Object.entries(expected)) {
    expect(getFragmentPresentation(id)?.image).toContain(filename)
  }
})
```

Run the focused fragment test. Expected: three filename assertions fail.

- [ ] **Step 2: Generate the chronological photo wall**

```text
Use case: stylized-concept
Asset type: cinematic memory fragment insert
Primary request: elegant 2050 chronological light wall displaying a sequence of shadow-puppet heritage photographs from workshop youth to national recognition, physical archival photos blending into restrained illuminated frames
Style/medium: cinematic realistic animated feature, plausible near-future museum display
Composition/framing: 4:3 landscape, photo timeline flowing left to right, dark caption-safe lower edge
Lighting/mood: ivory and ceremonial gold with restrained digital red, history becoming public memory
Constraints: no readable labels, dates, event title, logos, watermark, clear extra protagonist or excessive HUD graphics
```

- [ ] **Step 3: Generate the holographic shadow-puppet stage**

```text
Use case: stylized-concept
Asset type: cinematic memory fragment insert
Primary request: restrained 2050 holographic Chinese shadow-puppet performance where luminous articulated leather silhouettes retain visible hand-carved texture, projected above an ivory theatre platform
Style/medium: cinematic realistic animated feature, elegant plausible near future rather than cyberpunk
Composition/framing: 4:3 landscape, complete holographic stage centered, dark caption-safe lower edge
Lighting/mood: ivory-gold stage light, restrained red edge and quiet wonder
Constraints: no readable UI, logos, watermark, presenter, fantasy palace, excessive neon or photoreal human performers
```

- [ ] **Step 4: Generate the audience tears**

```text
Use case: historical-scene
Asset type: cinematic memory fragment insert
Primary request: close cinematic view across a dark 2050 theatre audience as one middle-aged spectator quietly wipes a tear while warm shadow-puppet light reflects in several attentive eyes, emotion shared without melodrama
Style/medium: cinematic realistic animated feature, humane and restrained
Composition/framing: 4:3 landscape, hands and reflected eyes as the focus, faces partially in darkness, caption-safe lower edge
Lighting/mood: warm gold reflection against deep auditorium black with a faint digital-red rim
Constraints: no celebrity likeness, readable badges, logos, watermark, exaggerated crying, microphones or futuristic implants
```

- [ ] **Step 5: Convert, validate, register, and commit**

Register:

```ts
old_photos_wall_fragment: {
  id: 'old_photos_wall_fragment',
  image: photoWall2050,
  alt: '从旧作坊到典礼舞台的照片沿着时光墙延伸，实体相片与柔光框彼此连接。',
  focus: '50% 48%',
},
hologram_stage_fragment: {
  id: 'hologram_stage_fragment',
  image: hologramStage2050,
  alt: '保留手工刻纹的全息皮影在象牙金舞台上重新活动。',
  focus: '50% 50%',
},
audience_reactions_fragment: {
  id: 'audience_reactions_fragment',
  image: audienceTears2050,
  alt: '观众席暗处有人轻轻拭去泪水，皮影暖光映在一排安静的眼睛里。',
  focus: '50% 46%',
},
```

Validate all three, run focused tests/typecheck/build, and commit:

```powershell
git commit -m "feat: add 2050 fragment art set"
```

---

### Task 8: Add the two missing 2089 fragment inserts

**Files:**
- Create: `frontend/src/assets/cinematic/fragment-2089-family-photo.webp`
- Create: `frontend/src/assets/cinematic/fragment-2089-heritage-certificate.webp`
- Modify: registry and registry tests

**Interfaces:**
- Produces: `fragment_family_photo`, `fragment_certificate`

- [ ] **Step 1: Add failing 2089 assertions and verify RED**

Add:

```ts
it('registers both additional 2089 interaction inserts', () => {
  const expected = {
    fragment_family_photo: 'fragment-2089-family-photo',
    fragment_certificate: 'fragment-2089-heritage-certificate',
  }
  for (const [id, filename] of Object.entries(expected)) {
    expect(getFragmentPresentation(id)?.image).toContain(filename)
  }
})
```

Run the focused fragment test. Expected: two filename assertions fail.

- [ ] **Step 2: Generate the family photo**

```text
Use case: illustration-story
Asset type: cinematic memory fragment insert
Primary request: worn Chinese family photograph spanning three generations, elderly shadow-puppet artisan at the center and an adult granddaughter beside him, faded warm print held inside a restrained cyan-purple 2089 memory laboratory
Style/medium: cinematic realistic animated-feature archival photo prop
Composition/framing: 4:3 landscape, complete photo centered, fingertips absent, dark caption-safe edge
Lighting/mood: warm amber family memory surrounded by cool cyan-purple laboratory reflections
Constraints: no readable handwriting, names, dates, logo, watermark, extra hands, duplicated faces or glossy new print
```

- [ ] **Step 3: Generate the heritage certificate**

```text
Use case: product-mockup
Asset type: cinematic memory fragment insert
Primary request: carefully preserved intangible-cultural-heritage certificate in a dark archival box beside a small translucent leather shadow-puppet cutting, traditional red seal shapes and fibrous paper illuminated by a 2089 memory scanner
Style/medium: cinematic realistic animated-feature archival prop close-up, plausible future conservation technology
Composition/framing: 4:3 landscape, certificate and archive box centered, dark caption-safe lower edge
Lighting/mood: cyan scanner edge, memory-purple shadow and a small warm amber core
Constraints: certificate contains no readable text, only abstract line blocks and seal shapes; no logo, watermark, hands or excessive HUD
```

- [ ] **Step 4: Convert, validate, register, and commit**

Register:

```ts
fragment_family_photo: {
  id: 'fragment_family_photo',
  image: familyPhoto2089,
  alt: '跨越三代的全家福在青紫实验室里泛着暖色旧相纸光。',
  focus: '50% 50%',
},
fragment_certificate: {
  id: 'fragment_certificate',
  image: heritageCertificate2089,
  alt: '非遗传承证书与皮影刻片被保存于档案盒中，文字只留下不可读的历史纹理。',
  focus: '50% 48%',
},
```

Validate both, run focused tests/typecheck/build, and commit:

```powershell
git commit -m "feat: add 2089 fragment art set"
```

---

### Task 9: Lock exact seventeen-fragment coverage

**Files:**
- Modify: `frontend/src/stage/fragmentPresentation.ts`
- Modify: `frontend/src/__tests__/fragmentPresentation.test.ts`

**Interfaces:**
- Produces: `FRAGMENT_PRESENTATION_IDS: readonly string[]`
- Guarantees: exact coverage of all 17 backend canonical fragment IDs

- [ ] **Step 1: Export deterministic registry IDs**

After the `presentations` object:

```ts
export const FRAGMENT_PRESENTATION_IDS = Object.freeze(Object.keys(presentations).sort())
```

- [ ] **Step 2: Replace the old four-entry scope test**

Use:

```ts
import {
  FRAGMENT_PRESENTATION_IDS,
  getFragmentPresentation,
} from '../stage/fragmentPresentation'

const canonicalFragmentIds = [
  'audience_reactions_fragment',
  'award_trophy_fragment',
  'farewell_letter_fragment',
  'fragment_certificate',
  'fragment_family_photo',
  'fragment_grandpa_knife',
  'fragment_last_puppet',
  'fragment_last_show',
  'fragment_letter',
  'fragment_old_photos',
  'fragment_shadow_puppet',
  'fragment_three_kings',
  'hologram_stage_fragment',
  'old_photos_wall_fragment',
  'puppet_trunk_fragment',
  'station_clock_fragment',
  'train_ticket_fragment',
].sort()

it('registers exactly all seventeen canonical fragment inserts', () => {
  expect(FRAGMENT_PRESENTATION_IDS).toEqual(canonicalFragmentIds)
  expect(canonicalFragmentIds.every((id) => getFragmentPresentation(id) !== null)).toBe(true)
  expect(getFragmentPresentation('unknown_fragment')).toBeNull()
})
```

- [ ] **Step 3: Validate all 17 files**

Run:

```powershell
python scripts/validate_cinematic_assets.py `
  --fragment frontend/src/assets/cinematic/fragment-1972-shadow-stage.webp `
  --fragment frontend/src/assets/cinematic/fragment-1972-carving-knife.webp `
  --fragment frontend/src/assets/cinematic/fragment-1972-three-kings.webp `
  --fragment frontend/src/assets/cinematic/fragment-1990-train-ticket.webp `
  --fragment frontend/src/assets/cinematic/fragment-1990-puppet-trunk.webp `
  --fragment frontend/src/assets/cinematic/fragment-1990-farewell-letter.webp `
  --fragment frontend/src/assets/cinematic/fragment-1990-station-clock.webp `
  --fragment frontend/src/assets/cinematic/fragment-2024-xiaoyu-letter.webp `
  --fragment frontend/src/assets/cinematic/fragment-2024-old-photos.webp `
  --fragment frontend/src/assets/cinematic/fragment-2024-last-show-poster.webp `
  --fragment frontend/src/assets/cinematic/fragment-2050-award-trophy.webp `
  --fragment frontend/src/assets/cinematic/fragment-2050-photo-wall.webp `
  --fragment frontend/src/assets/cinematic/fragment-2050-hologram-stage.webp `
  --fragment frontend/src/assets/cinematic/fragment-2050-audience-tears.webp `
  --fragment frontend/src/assets/cinematic/fragment-2089-family-photo.webp `
  --fragment frontend/src/assets/cinematic/fragment-2089-heritage-certificate.webp `
  --fragment frontend/src/assets/cinematic/fragment-2089-last-puppet.webp
```

Expected: `Validated 0 portraits and 17 fragments.`

- [ ] **Step 4: Run full frontend checks and commit**

```powershell
cd frontend
npm test
npm run typecheck
npm run lint
npm run check
npm run build
git add src/stage/fragmentPresentation.ts src/__tests__/fragmentPresentation.test.ts
git commit -m "test: lock complete fragment art coverage"
```

---

### Task 10: Audit every hotspot object in the five master backgrounds

**Files:**
- Review: `backend/data/hotspots.json`
- Review and conditionally modify: five master background assets
- Create: `docs/qa/2026-07-27-hotspot-art-audit.md`

**Interfaces:**
- Consumes: all 17 hotspot positions and labels
- Produces: pass/fail evidence for each scene object
- Allows: targeted imagegen edit only for a failed row

- [ ] **Step 1: Inspect all five backgrounds at original detail**

Use `view_image` on:

```text
scene-1972-xian-alley.png
scene-1990-shenzhen-station.webp
scene-2024-urban-village-room.webp
scene-2050-award-ceremony.webp
scene-2089-memory-lab.webp
```

- [ ] **Step 2: Check the exact object list**

Record each as `visible`, `partially visible`, or `missing`:

```text
1972: 皮影戏幕 / 旧工具箱与刻刀 / 三英战吕布皮影
1990: 南下车票 / 皮影木箱 / 未寄出的信 / 站台时钟
2024: 小雨的信 / 泛黄剧照 / 最后一场演出海报
2050: 水晶奖杯 / 时光照片墙 / 全息皮影舞台 / 观众席泪光
2089: 泛黄全家福 / 非遗证书档案 / 最后一个孙悟空皮影
```

`partially visible` passes only when the hotspot ring can still point to a recognizable object.

- [ ] **Step 3: Target-edit only failed backgrounds**

For each `missing` row, call built-in imagegen in edit mode with the exact current background and:

```text
Edit only the named hotspot object at its existing interaction location. Add a clearly recognizable
but compositionally subordinate [OBJECT NAME] matching the scene's current year, materials,
lighting, camera, style and color grade. Preserve every other pixel-level subject, the 2.39:1
composition, subtitle safe area, portrait safe area and all already-valid hotspot objects.
No readable text, logo, watermark, new people or global restyling.
```

For `partially visible`, edit only if the object cannot be identified at the 390×844 mobile crop.
Convert the edited source back to the exact existing filename and enforce the background 1.5 MB
budget.

- [ ] **Step 4: Write the audit record**

Create `docs/qa/2026-07-27-hotspot-art-audit.md` with:

```markdown
# 五幕热点物件美术复核

| 场景 | 热点物件 | 结果 | 证据/修复 |
| --- | --- | --- | --- |
| scene_1972 | 皮影戏幕 | visible | 原图可辨认 |
```

Include all 17 rows, not only failures. Name any regenerated background and its final byte size.

- [ ] **Step 5: Verify and commit**

Run focused presentation tests, typecheck and build. Commit the audit and only backgrounds that
actually changed:

```powershell
git add docs/qa/2026-07-27-hotspot-art-audit.md frontend/src/assets/cinematic
git commit -m "fix: align cinematic backgrounds with hotspots"
```

If no background changed, use commit message:

```powershell
git commit -m "docs: record hotspot art audit"
```

---

### Task 11: Verify solid-character and full-fragment failure paths

**Files:**
- Modify: `frontend/src/__tests__/cinematicStageFallback.test.ts`
- Modify: `frontend/src/__tests__/fragmentArtwork.test.ts`
- Review: `frontend/src/components/CinematicStage.vue`
- Review: `frontend/src/components/FragmentArtwork.vue`

**Interfaces:**
- Guarantees: portrait failure does not affect the stage or dialogue siblings
- Guarantees: fragment image error self-hides without affecting popup content

- [ ] **Step 1: Add portrait error isolation test**

Add:

```ts
it('hides a failed character image without removing the stage', async () => {
  assetLoad.mockRejectedValueOnce(new Error('background unavailable'))
  const host = mountStage('scene_1990', 'stranger_1990')
  await nextTick()

  host.querySelector<HTMLImageElement>('.character-portrait')?.dispatchEvent(new Event('error'))
  await nextTick()

  expect(host.querySelector('.cinematic-stage')).not.toBeNull()
  expect(host.querySelector('.legacy-art')).not.toBeNull()
  expect(host.querySelector('.character-portrait')).toBeNull()
})
```

Implement in `CinematicStage.vue`:

```ts
const portraitFailed = ref(false)

watch(activePortrait, () => {
  portraitFailed.value = false
})
```

Update the image:

```vue
<img
  v-if="activePortrait && !portraitFailed"
  class="character-portrait"
  :data-character-treatment="characterTreatment"
  :src="activePortrait"
  alt=""
  aria-hidden="true"
  @error="portraitFailed = true"
/>
```

- [ ] **Step 2: Extend fragment reset coverage**

Add to `fragmentArtwork.test.ts`:

```ts
it('renders the next fragment after a previous image failed', async () => {
  const host = document.createElement('div')
  const current = ref(presentation)
  app = createApp({
    render: () => h(FragmentArtwork, { presentation: current.value }),
  })
  app.mount(host)

  host.querySelector('img')?.dispatchEvent(new Event('error'))
  await nextTick()
  expect(host.querySelector('img')).toBeNull()

  current.value = {
    id: 'next_fragment',
    image: '/next-fragment.webp',
    alt: '下一张记忆碎片',
    focus: '50% 50%',
  }
  await nextTick()

  expect(host.querySelector('img')?.getAttribute('src')).toBe('/next-fragment.webp')
})
```

Update the test import to `import { createApp, h, nextTick, ref } from 'vue'`.

- [ ] **Step 3: Run focused and full frontend tests**

```powershell
cd frontend
npm test -- --run src/__tests__/cinematicStageFallback.test.ts src/__tests__/fragmentArtwork.test.ts
npm test
npm run typecheck
npm run lint
npm run check
npm run build
```

- [ ] **Step 4: Commit only if behavior or tests changed**

```powershell
git add src/components/CinematicStage.vue src/components/FragmentArtwork.vue src/__tests__/cinematicStageFallback.test.ts src/__tests__/fragmentArtwork.test.ts
git commit -m "test: cover solid character and fragment failures"
```

---

### Task 12: Run real-page visual acceptance

**Files:**
- Review: all runtime assets and cinematic components
- Modify only when a captured screenshot demonstrates a specific defect

**Interfaces:**
- Consumes: frontend `http://127.0.0.1:5173`
- Consumes: backend `http://127.0.0.1:8000`
- Produces: character grounding and 17-fragment visual sign-off

- [ ] **Step 1: Confirm local health**

Require status 200 for `/`, `/api/health`, and all 20 new runtime assets.

- [ ] **Step 2: Traverse all five eras**

For each era:

1. Open every NPC and confirm face identity, physical opacity, scale, grounding and light direction.
2. Click every hotspot and confirm the popup image matches the clicked object.
3. Confirm title, description and continue button remain readable.
4. Confirm no generated readable fake text, watermark, broken alpha rectangle or unwanted person.

- [ ] **Step 3: Verify exact viewports**

Use the Browser skill's supported viewport capability when allowed:

```text
390×844
768×1024
1440×900
1920×1080
```

Check character/choice/subtitle overlap and every mobile hotspot crop. If the browser refuses
automated control of the local URL, do not bypass policy; keep services running and ask the user
for the corresponding manual visual sign-off.

- [ ] **Step 4: Fix and recheck observed defects**

For each defect, record scene + NPC/fragment + viewport, make the smallest CSS/composition or
single-asset correction, and repeat that exact check.

- [ ] **Step 5: Commit visual acceptance fixes**

Skip this commit if no files changed. Otherwise:

```powershell
git commit -m "fix: close solid character visual QA gaps"
```

---

### Task 13: Run final gates and update product records

**Files:**
- Modify: `CHANGELOG.md`
- Modify: `TEST_REPORT.md`
- Modify: `UPGRADE_PLAN.md`
- Modify: the approved design spec and this plan

**Interfaces:**
- Produces: exact asset, test, build, browser and known-limit record

- [ ] **Step 1: Run frontend gates**

```powershell
cd frontend
npm run typecheck
npm run lint
npm run check
npm test
npm run build
npm audit --omit=dev --audit-level=high
```

Every command must exit 0. Record test count, transformed modules, Game chunk and
CinematicStage chunk gzip sizes.

- [ ] **Step 2: Run backend/content/deployment gates**

```powershell
python scripts/validate_content.py
python -m compileall -q backend scripts
python -m pytest backend/tests -q
python -m alembic current
python -m alembic check
docker compose config --quiet
powershell -ExecutionPolicy Bypass -File scripts/smoke.ps1
```

Expected content: 5 scenes, 7 NPCs, 17 fragments, 17 hotspots, 10 choices, 4 endings.

- [ ] **Step 3: Record exact art evidence**

Document:

- seven solid portrait paths, byte sizes and alpha validation result;
- all seventeen fragment paths and byte sizes;
- any background edits;
- exact frontend/backend test counts;
- four viewport results or explicit manual-sign-off limitation;
- scene, portrait and fragment failure results;
- npm and Docker daemon known limitations.

- [ ] **Step 4: Update spec and plan status**

Set the spec to `Completed and verified` only if real-page visual acceptance is complete. If the
local-browser control restriction remains, use `Implementation and automated verification
complete; manual visual sign-off pending`.

- [ ] **Step 5: Commit acceptance records**

```powershell
git add CHANGELOG.md TEST_REPORT.md UPGRADE_PLAN.md docs/superpowers/specs/2026-07-27-solid-characters-and-complete-fragment-art-design.md docs/superpowers/plans/2026-07-27-solid-characters-and-complete-fragment-art.md
git commit -m "docs: record solid character and fragment acceptance"
```

- [ ] **Step 6: Verify clean handoff**

```powershell
git status --porcelain
git log -12 --oneline
```

Expected: clean worktree and local services still returning 200.
