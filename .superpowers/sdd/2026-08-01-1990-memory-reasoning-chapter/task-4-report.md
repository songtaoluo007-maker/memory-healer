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

## Fix round 1

- Locked feedback now stays in ChatPanel's sole accessible status channel after opening its configured NPC. It includes the server method, canonical hint, current trust, and authoritative threshold; it clears on a normal dialogue completion, explicit close, or NPC change.
- Dialogue feedback is a source-NPC-bound message list. Positive and negative trust use distinct wording, and degraded mode appends instead of replacing trust/archive feedback. Late results from an NPC that is no longer selected are not displayed.
- ChatPanel captures collected IDs before sending and emits `newlyCollected` only for the authoritative uncollected-to-collected transition. Game only archives, opens the fragment popup, voices, and auto-selects reasoning evidence when that flag is true.
- Strengthened page integration coverage confirms payload-NPC dialogue locks remain interactive, trust locks report `当前 / 需要`, an actual 35-trust request is sent before normal collection, prompts filter by selected NPC and collection state, newly collected dialogue evidence is selected in the active hypothesis, and a repeated standard question produces no second popup.

### Fix round verification

- Targeted: `npm test -- --run src/__tests__/dialogueFlow.test.ts src/__tests__/gamePagePresentation.test.ts` — 19 passed.
- Full frontend: `npm test -- --run` — 18 files, 148 passed.
- ESLint: `npm run lint` — passed with 5 test-only `vue/one-component-per-file` warnings and no errors.
- Build: `npm run build` — passed.

## Fix round 2

- After `sendDialogue` returns, ChatPanel now immediately discards a response whose captured NPC is no longer selected. The return precedes trust SFX, feedback construction, voice-coordinator work, completion emission, and voice requests; `finally` still clears the pending state.
- The race regression switches NPCs while the original request is pending, then proves the late response produces no status, trust SFX, voice coordinator call, dialogue-complete emission, or voice request.
- Verification: targeted 19 passed; full frontend 18 files / 148 passed; ESLint has 0 errors and 5 test-only warnings; production build passed.
