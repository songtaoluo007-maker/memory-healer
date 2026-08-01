# Task 4 report — dialogue evidence task

## Status

Complete. Dialogue unlock prompts now derive from scene fragment metadata, use the canonical configured text, announce trust and archive outcomes through an accessible status line, and place newly collected dialogue evidence into the active reasoning hypothesis. Locked exploration results retain their hotspot state, show the canonical hint, and open the configured NPC task when available.

## Files

- `frontend/src/components/ChatPanel.vue`
- `frontend/src/views/Game.vue`
- `frontend/src/__tests__/dialogueFlow.test.ts`
- `frontend/src/__tests__/gamePagePresentation.test.ts`

## RED

- `npm test -- --run src/__tests__/dialogueFlow.test.ts` failed as expected before the prompt/status implementation: no suggested prompt button and no trust-status output.
- `npm test -- --run src/__tests__/gamePagePresentation.test.ts` failed as expected before the locked-result branch: the locked hotspot became disabled (marked explored).

## GREEN and verification

- Targeted: `npm test -- --run src/__tests__/dialogueFlow.test.ts src/__tests__/gamePagePresentation.test.ts` — 12 passed.
- Full frontend: `npm test -- --run` — 18 files, 141 passed.
- ESLint: `npm run lint` — passed with 4 existing/test-only `vue/one-component-per-file` warnings (no errors).
- Build: `npm run build` — passed.

## Commit

`feat: make dialogue unlock playable evidence`

## Concerns

- The page-level test mocks the Pixi cinematic canvas so it can exercise the real Game-to-Hotspot interaction path in jsdom; production rendering is covered by the production build.
