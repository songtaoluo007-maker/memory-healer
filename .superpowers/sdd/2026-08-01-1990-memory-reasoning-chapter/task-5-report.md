# Task 5 report — 1972 consequence inside the 1990 scene

## Status

Complete. The active canonical consequence is selected from `SceneView.applied_consequences` only when its `target_scene_id` matches the current scene. The 1990 opening narration and a separate accessible `因果回声` docket use the authoritative `scene_text`, while `CinematicStage` renders a restrained physical trunk treatment from the consequence data.

## Files

- `frontend/src/composables/useScene.ts`
- `frontend/src/domain/consequences.ts`
- `frontend/src/components/CinematicStage.vue`
- `frontend/src/views/Game.vue`
- `frontend/src/styles/cinematic-game.css`
- `frontend/src/__tests__/sceneFlow.test.ts`
- `frontend/src/__tests__/gamePagePresentation.test.ts`
- `frontend/src/__tests__/cinematicStageFallback.test.ts`

`frontend/src/types/game.ts` already contained the canonical `AppliedConsequence` and `SceneView.applied_consequences` contracts, so Task 5 reused them without duplicating or narrowing the authoritative type.

## RED

- Command: `npm test -- --run src/__tests__/sceneFlow.test.ts src/__tests__/gamePagePresentation.test.ts src/__tests__/cinematicStageFallback.test.ts`
- Result before implementation: 5 failed, 18 passed.
- Expected failures covered the missing active-scene consequence selector, absent Game-to-stage consequence prop, absent opening narrative/cue behavior, and absent carried/suppressed trunk props.

## GREEN and verification

- Targeted: `npm test -- --run src/__tests__/sceneFlow.test.ts src/__tests__/gamePagePresentation.test.ts src/__tests__/cinematicStageFallback.test.ts` — 3 files, 23 passed.
- Full frontend: `npm test -- --run` — 18 files, 157 passed.
- ESLint: `npm run lint` — 0 errors; 5 test-only `vue/one-component-per-file` warnings.
- Production build: `npm run build` — passed (`vue-tsc -b` and Vite).
- Formatting: targeted Prettier check/write completed for all Task 5 files.

## Presentation behavior

- `legacy_carried`: warmer practical light, open lid, clearly visible suit-wearing puppet, and an angular paper note reading `手艺不该被埋没`.
- `legacy_suppressed`: cooler/desaturated light, half-closed lid, metal latch, dark angular occlusion, and a guarded puppet silhouette.
- Unknown variants, absent consequences, and consequences targeting another scene leave the full base page unchanged: no stage prop, appended narration, or causal cue.
- All new entrance motion is removed under `prefers-reduced-motion: reduce`; the static prop, authoritative narration, and visible causal docket remain complete.

## Commit

`feat: reveal 1972 consequences in 1990`

## Concerns

- The stage prop is intentionally a CSS composition layered over the existing 1990 artwork; no second background or generated asset was added. Final browser QA should confirm the trunk's exact registration against the production artwork at desktop and 390×844, because jsdom can verify variant structure but not compositing alignment.

## Fix round 1 — unsupported variant guard

- Verified the review finding: an unknown same-scene variant was rejected by `CinematicStage`, but `useScene` still exposed it as active, so Game appended its `scene_text`, rendered `因果回声`, and passed it to the stage boundary.
- Added one shared runtime resolver in `frontend/src/domain/consequences.ts`. Its private presentation map currently supports only `legacy_carried → scene_1990` and `legacy_suppressed → scene_1990`; both `useScene` and `CinematicStage` now call that resolver.
- Added page-level coverage for unknown and absent consequences, plus useScene coverage proving the raw canonical item is retained while the unsupported item is not activated. Existing stage coverage continues to verify unknown, no-value, and target-mismatch no-op behavior.
- RED: targeted suite — 2 failed, 24 passed, with failures at active consequence selection and Game stage prop/cue behavior.
- GREEN: targeted suite — 3 files, 26 passed.
- Full frontend: 18 files, 160 passed.
- ESLint: 0 errors; 5 test-only `vue/one-component-per-file` warnings.
- Production build: passed (`vue-tsc -b` and Vite).
