# 拾忆 P0-B · 1972 电影级纵向切片 Implementation Plan

> **Status:** Approved direction, implementation authorized.

**Goal:** 将现有原型界面重构为可扩展的全屏电影舞台，并让 1972 西安老巷达到
首个可验收的“东方皮影电影感”纵向切片品质，同时保持 P0-A 的全部内容、状态、
安全和部署质量门。

**Approved visual direction:** 桌面 2.39:1 全屏舞台；暖金、朱砂、旧木；常态
动画电影写实；碎片发现和情绪高潮进入超现实记忆电影；画面与字幕优先于卡片和
常驻按钮；移动端使用独立竖向构图。

**Architecture:** Vue 负责可访问的界面与状态编排；Pinia 拆分会话、游戏、舞台
和覆盖层；PixiJS 负责 1972 分层背景、镜头、灯光与粒子；后端 `SceneView` 和
`GameState` 仍是内容与规则唯一权威来源。1972 使用新电影资产，其余年代在同一
舞台契约下使用现有 SVG 回退，之后可逐幕替换。

---

## Task 1: Establish the cinematic application shell

- [ ] Add Vue Router, Pinia, and PixiJS with locked dependencies.
- [ ] Introduce route-level Home, Intro, Game, Saves, and Ending flow without
  changing backend contracts.
- [ ] Add design tokens for ink black, warm paper, cinnabar, antique gold,
  subtitle safe areas, cinematic easing, focus rings, and reduced motion.
- [ ] Keep the first screen directly actionable; no marketing card wall.
- [ ] Add tests for route transitions and mutually exclusive overlays.

## Task 2: Produce and register the 1972 art direction

- [ ] Create a cinematic 1972 Xi’an alley master background with an illuminated
  shadow-puppet window, deep foreground silhouettes, atmospheric dust, and
  empty composition zones for NPC and subtitles.
- [ ] Create a matching Chen Shouyi portrait/character plate.
- [ ] Export web-ready source assets and a typed presentation manifest that
  contains visual assets only, never gameplay IDs or rules.
- [ ] Provide existing SVG fallback for failed/slow asset loading.

## Task 3: Build the PixiJS memory stage

- [ ] Create isolated stage, camera, layer, lighting, and particle modules with
  explicit mount/update/destroy boundaries.
- [ ] Render the 1972 master art in a 2.39:1 desktop frame with gentle parallax,
  tungsten window bloom, dust, vignette, and film grain.
- [ ] Pause animation when hidden, reduced-motion, or unmounted; cap device
  resolution and support a 30 FPS low-effects path.
- [ ] Keep hotspots as semantic Vue buttons aligned over the stage.
- [ ] Fall back to the current `SceneIllustration` for non-1972 scenes.

## Task 4: Replace prototype HUD and dialogue with cinematic interaction

- [ ] Replace the top button strip with a minimal chapter slate, memory progress,
  sound control, and contextual action rail.
- [ ] Use in-scene hotspot labels with focus, hover, discovered, and completed
  states.
- [ ] Rebuild short dialogue as subtitle composition and long dialogue as a
  bottom screenplay panel; preserve full keyboard and screen-reader flow.
- [ ] Rebuild fragment discovery as a memory-film insert with close/continue
  controls and reduced-motion fallback.
- [ ] Rebuild scene choices as a centered cinematic decision beat.

## Task 5: Recompose the entry flow

- [ ] Redesign Home as a restrained film-title frame with one dominant start
  action, continue/save, and account access.
- [ ] Redesign Intro as a paced prologue using typographic cuts and the same
  art language.
- [ ] Restyle login and saves without nested cards or generic blue gradients.
- [ ] Preserve guest start and Cookie-authenticated saves.

## Task 6: Build desktop/mobile dual composition

- [ ] Desktop: 2.39:1 stage, subtitle safe zones, mouse and keyboard navigation.
- [ ] Mobile portrait: cropped scene focus, bottom interaction drawer, reachable
  hotspots, and no scaled-down desktop chrome.
- [ ] Cover 390×844, 768×1024, 1440×900, and 1920×1080.
- [ ] Respect safe-area insets, `prefers-reduced-motion`, and 200% text zoom.

## Task 7: Verify the vertical slice

- [ ] Run typecheck, lint, formatting, Vitest, production build, dependency
  audit, content validation, and all backend tests.
- [ ] Browser-QA Home → Intro → 1972 → explore → fragment → NPC dialogue →
  choice on desktop and mobile viewport.
- [ ] Inspect screenshots for clipping, dead space, low contrast, overlay
  conflicts, broken asset fallbacks, and misplaced hotspots.
- [ ] Record the exact P0-B scope and evidence in CHANGELOG and TEST_REPORT.
- [ ] Do not claim the remaining four eras have final cinematic art.
