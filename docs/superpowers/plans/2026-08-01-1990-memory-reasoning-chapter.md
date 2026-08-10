# 1990 Memory Reasoning Chapter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** Turn 1990 into a complete second gameplay chapter with competing hypotheses, deterministic dialogue evidence, a trust-gated clue, actionable wrong-reasoning feedback, explicit choice requirements, and a visible consequence from the 1972 decision.

**Architecture:** Keep the canonical backend authoritative. Content JSON declares unlock rules, hypothesis outcomes, choice requirements, and cross-scene consequences; the registry validates every reference; application services evaluate those rules and return presentation events. The Vue client renders a single reusable reasoning/dialogue flow for every scene and never invents unlock state locally.

**Tech Stack:** Python 3.12, FastAPI, Pydantic 2, pytest; Vue 3, TypeScript, Pinia, Vitest, PixiJS, CSS.

## Global Constraints

- Preserve the existing uncommitted `design-qa.md` change exactly; do not stage, rewrite, or revert it.
- Work only in `C:\Users\Administrator\Documents\拾忆\.worktrees\solid-characters-fragments` on `codex/solid-characters-fragments`.
- Follow RED → GREEN → REFACTOR for every behavior. Record the failing command and the passing command in the task report.
- Do not install or download any local speech model. New lines may use existing runtime/fallback voice behavior but must not add model weights or generated caches.
- Keep one canonical rule path under `/api/game/*`; do not expand the legacy dict-based `/api/scene/detail` or `/api/butterfly/status` engines.
- Keep the existing cinematic visual language: warm ivory/gold copy, dark translucent surfaces, physical-object imagery, no purple orb controls.
- Do not duplicate a `1990`-specific reasoning component. All UI must remain data-driven and reusable by 2024/2050/2089.

---

## Task 1: Add explicit canonical gameplay contracts

**Files:**

- Modify: `backend/content/models.py`
- Modify: `backend/content/registry.py`
- Modify: `backend/data/choices.json`
- Modify: `backend/tests/content/test_registry.py`
- Modify: `backend/tests/application/test_game_service.py`

### Step 1: Write failing registry and choice-gate tests

Add literal behavior tests for:

1. A choice may declare requirements of three reusable kinds:

```json
{"kind": "hypothesis_confirmed", "hypothesis_id": "hypothesis_1972_legacy"}
{"kind": "fragment_collected", "fragment_id": "fragment_grandpa_knife"}
{"kind": "npc_trust_at_least", "npc_id": "chen_shouyi_young", "minimum": 60}
```

2. Registry rejection codes are stable for missing or cross-scene references:
   - `CHOICE_REQUIREMENT_HYPOTHESIS_NOT_FOUND`
   - `CHOICE_REQUIREMENT_HYPOTHESIS_SCENE_MISMATCH`
   - `CHOICE_REQUIREMENT_FRAGMENT_NOT_FOUND`
   - `CHOICE_REQUIREMENT_FRAGMENT_SCENE_MISMATCH`
   - `CHOICE_REQUIREMENT_NPC_NOT_FOUND`
3. A scene with two hypotheses cannot unlock a choice by confirming the non-required one.
4. The shipping 1972 choices both explicitly require `hypothesis_1972_legacy`.

Run and observe RED:

```powershell
python -m pytest backend/tests/content/test_registry.py backend/tests/application/test_game_service.py -q
```

### Step 2: Implement the smallest contract

In `models.py`, add a discriminated union for:

- `HypothesisConfirmedRequirementContent`
- `FragmentCollectedRequirementContent`
- `NpcTrustAtLeastRequirementContent`

Add `requirements: tuple[ChoiceRequirementContent, ...] = ()` to `ChoiceContent`.

In `registry.py`, validate all references. Hypothesis and fragment requirements must belong to the choice scene. Trust requirements may reference any canonical NPC so later scenes can intentionally depend on earlier relationships.

Replace the implicit “any hypothesis in this scene” gate in `GameService.record_choice()` with a private requirement evaluator. Preserve the current public error codes where they are semantically precise:

- unmet hypothesis → `HYPOTHESIS_REQUIRED`
- unmet fragment or trust → `CHOICE_REQUIREMENT_UNMET`

Populate both 1972 choices with the explicit hypothesis requirement. Do not add 1990 hypotheses yet.

### Step 3: Verify GREEN and regressions

```powershell
python -m pytest backend/tests/content/test_registry.py backend/tests/application/test_game_service.py -q
python -m pytest backend -q
```

### Step 4: Commit

```powershell
git add backend/content/models.py backend/content/registry.py backend/data/choices.json backend/tests/content/test_registry.py backend/tests/application/test_game_service.py
git commit -m "refactor: make scene choice requirements explicit"
```

---

## Task 2: Build the authoritative 1990 evidence and consequence loop

**Files:**

- Modify: `backend/content/models.py`
- Modify: `backend/content/registry.py`
- Modify: `backend/application/game_service.py`
- Modify: `backend/application/dialogue_service.py`
- Modify: `backend/data/fragments.json`
- Modify: `backend/data/hypotheses.json`
- Modify: `backend/data/choices.json`
- Modify: `backend/data/npcs.json`
- Add: `backend/data/consequences.json`
- Modify: `backend/tests/content/test_registry.py`
- Modify: `backend/tests/application/test_game_service.py`
- Modify: `backend/tests/application/test_dialogue_service.py`
- Modify: `backend/tests/application/test_ending_paths.py`
- Modify: `backend/tests/api/test_game_api.py` if API coverage is not already colocated

### Step 1: Write failing unlock, reasoning, and consequence tests

Cover these observable behaviors with real services and canonical data:

- Clicking an unrevealed `dialogue` fragment returns an unchanged state plus `fragment.locked`; it never collects the clue directly.
- Sending the canonical suggested question for a dialogue fragment deterministically collects that fragment even when the AI client degrades, and grants its one-time configured trust reward.
- Repeating that question cannot farm trust or duplicate the fragment.
- Clicking a `trust` fragment below its threshold returns `fragment.locked`; at or above the threshold it collects exactly once.
- AI output cannot reveal `explore` fragments or trust fragments below threshold.
- `scene_1990` exposes exactly two public hypothesis candidates.
- Confirming `hypothesis_1990_survival` with ticket + letter returns unchanged state and a `hypothesis.rejected` event whose feedback directs the player toward the trunk and clock.
- Confirming `hypothesis_1990_modern_story` with trunk + clock records the scene-specific confirmation and emits `hypothesis.confirmed`.
- Both 1990 choices remain locked until `hypothesis_1990_modern_story` is confirmed; the rejected candidate never unlocks them.
- After either 1972 choice, the authoritative 1990 `SceneView` contains exactly one applied consequence with the expected variant and text.
- `DialogueService` includes the applied consequence's NPC context in its authoritative prompt.

Run and observe RED:

```powershell
python -m pytest backend/tests/application/test_game_service.py backend/tests/application/test_dialogue_service.py backend/tests/content/test_registry.py -q
```

### Step 2: Extend canonical content models without leaking server verdicts

Add to `FragmentContent` and the scene fragment view:

```python
unlock_npc_id: str | None = None
minimum_trust: int | None = Field(default=None, ge=0, le=100)
dialogue_prompt: str | None = None
dialogue_trust_reward: int = Field(default=0, ge=0, le=20)
```

Registry rules:

- `dialogue` requires a same-scene NPC and a non-empty prompt.
- `trust` requires a same-scene NPC and threshold.
- `explore` forbids dialogue-only fields.
- NPC/hotspot/fragment references must agree.

Add `outcome: Literal["confirmed", "rejected"] = "confirmed"` to the server-only `HypothesisContent`. Introduce a separate `HypothesisView` in `game_service.py` so `outcome` is not serialized to the player; keep all current public fields and voice references.

Add canonical consequence models and registry loading for `consequences.json`:

```python
id: str
source_choice_id: str
target_scene_id: str
variant: str
scene_text: str
npc_context: dict[str, str]
```

Registry must validate the choice, target scene, and NPC references. Add `applied_consequences` to `SceneView`, calculated from authoritative `GameState.butterfly_choices` on every request; never persist the derived result in saves.

### Step 3: Implement deterministic unlock rules

`GameService.explore()` must branch on the canonical fragment:

- `explore`: collect normally.
- `dialogue`: collect only if the dialogue service has already collected it; otherwise return `fragment.locked` with method/hint/NPC/prompt in the event payload and no revision change.
- `trust`: compare authoritative trust; return `fragment.locked` below threshold, collect at threshold.

`DialogueService.chat()` must:

- recognize an exact canonical `dialogue_prompt` for the selected same-scene NPC;
- deterministically collect that dialogue fragment and apply its one-time trust reward even if the LLM is unavailable;
- filter model-suggested fragments through canonical unlock rules;
- never let model output bypass explore/trust gates;
- append current applied `npc_context` to the prompt.

For a rejected hypothesis, `GameService.confirm_hypothesis()` validates the evidence normally but returns the unchanged state plus:

```python
PresentationEvent(
    type="hypothesis.rejected",
    content_id=hypothesis.id,
    payload={"feedback": hypothesis.resolution, "evidence_ids": [...]},
)
```

No revision is consumed and no `confirmed_hypotheses` entry is written.

### Step 4: Author the 1990 content

Use two candidates in this order:

1. `hypothesis_1990_survival` (rejected): ticket + farewell letter. Feedback: pressure and guilt do not prove abandonment; ask about the suit-wearing puppet and the 3:47 decision.
2. `hypothesis_1990_modern_story` (confirmed): puppet trunk + station clock. Resolution: he came south both to survive and to test whether shadow puppetry could tell contemporary stories.

Make `puppet_trunk_fragment` the required dialogue clue:

- NPC: `chen_shouyi_1990`
- prompt: `箱子里为什么有一个穿西装的皮影？`
- one-time trust reward: `10`

Convert `station_clock_fragment` to a trust clue:

- NPC: `chen_shouyi_1990`
- threshold: `35`
- memory text: 3:47 is the moment he lifts the trunk and decides to walk out of the station, not a contradictory future arrival time.

Update both 1990 choices to require `hypothesis_1990_modern_story` and use:

- `打开木箱，让他看那个人偶`
- `合上木箱，把答案留给自己`

Fix the 1990 setting copy to “just arrived in Shenzhen”; remove “the train will arrive in 23 minutes” and “board alone”. Fix the impossible 2050 prompt that says Xiaoyu personally remembers 1972.

Add two 1972 → 1990 consequences:

- `legacy_carried`: open trunk, modern puppet visible, “手艺不该被埋没”.
- `legacy_suppressed`: half-closed trunk, modern puppet buried, Chen initially guarded.

Give every existing dialogue/trust fragment valid canonical metadata so the contract is globally true, not special-cased to 1990.

### Step 5: Verify GREEN, legal paths, and API serialization

```powershell
python -m pytest backend/tests/application/test_game_service.py backend/tests/application/test_dialogue_service.py backend/tests/application/test_ending_paths.py backend/tests/content/test_registry.py -q
python -m pytest backend -q
python scripts/validate_content.py
```

### Step 6: Commit

Stage only the files owned by this task and commit:

```powershell
git commit -m "feat: add authoritative 1990 reasoning chapter"
```

---

## Task 3: Generalize the Vue reasoning and choice flow

**Files:**

- Modify: `frontend/src/types/game.ts`
- Modify: `frontend/src/domain/memoryReasoning.ts`
- Modify: `frontend/src/components/MemoryReasoningPanel.vue`
- Modify: `frontend/src/views/Game.vue`
- Modify: `frontend/src/__tests__/memoryReasoning.test.ts`
- Modify: `frontend/src/__tests__/sceneFlow.test.ts`
- Add or modify: `frontend/src/__tests__/memoryReasoningPanel.test.ts`

### Step 1: Write failing Vitest coverage

Add tests that prove:

- A four-item 1990 snapshot uses only canonical collected IDs and ignores selected evidence from 1972.
- The UI presents both 1990 hypothesis candidates and switching candidates resets incompatible selected evidence.
- A rejected hypothesis event shows its authoritative feedback and leaves the decision locked.
- The correct hypothesis confirmation unlocks choices whose explicit requirements are satisfied.
- Choice locking evaluates `requirements`; it does not infer correctness from “first hypothesis” or “any scene hypothesis”.
- Replacing the 1972 scene view with 1990 removes all stale candidate/evidence selection state.
- Existing one-candidate 1972 behavior remains unchanged.

Run and observe RED:

```powershell
npm test -- --run src/__tests__/memoryReasoning.test.ts src/__tests__/sceneFlow.test.ts src/__tests__/memoryReasoningPanel.test.ts
```

### Step 2: Implement reusable candidate selection

Update frontend types for fragment unlock metadata, discriminated choice requirements, and applied consequences.

Replace `hypotheses[0]` assumptions with:

- `selectedHypothesisId`
- current-scene candidate lookup by `scene_id`
- one evidence selection set scoped to the active candidate
- authoritative `hypothesis.rejected` and `hypothesis.confirmed` event handling

Extend the single `MemoryReasoningPanel` to render candidate tabs/cards from props. Do not create a 1990 component. The component must:

- announce the active question;
- show rejected feedback in a restrained amber/red physical-paper treatment;
- let the player switch interpretation;
- continue to use canonical fragment artwork and names;
- expose native buttons with focus-visible states.

Replace `isSceneDecisionUnlocked(sceneId, hypotheses, confirmed)` with requirement evaluation against the authoritative game state and choices.

### Step 3: Keep mobile evidence interactive

At `max-width: 900px`, do not hide `.evidence-grid`. Make it a horizontally scrollable, snap-aligned list with visible card names, a minimum 44px action target, and preserved keyboard focus. The confirmation action must never appear usable while its evidence is hidden or incomplete.

### Step 4: Verify GREEN and build

```powershell
npm test -- --run src/__tests__/memoryReasoning.test.ts src/__tests__/sceneFlow.test.ts src/__tests__/memoryReasoningPanel.test.ts
npm test -- --run
npm run build
```

### Step 5: Commit

```powershell
git commit -m "feat: support competing memory hypotheses"
```

---

## Task 4: Turn dialogue into a visible evidence task

**Files:**

- Modify: `frontend/src/components/ChatPanel.vue`
- Modify: `frontend/src/views/Game.vue`
- Modify: `frontend/src/components/HotspotOverlay.vue` only if locked-state presentation belongs there
- Modify: `frontend/src/__tests__/dialogueFlow.test.ts`
- Modify: `frontend/src/__tests__/gamePagePresentation.test.ts` or the nearest presentation test

### Step 1: Write failing dialogue-task tests

Cover:

- Canonical suggested prompt buttons are derived from uncollected dialogue fragments for the selected NPC.
- Clicking a prompt uses the existing authoritative dialogue API path and sends the exact configured prompt.
- Positive/negative trust change is announced as text, not only sound/color.
- A newly collected dialogue clue is announced once by canonical name and becomes available to reasoning immediately.
- A locked dialogue hotspot opens the correct NPC task instead of being marked explored.
- A locked trust hotspot shows the threshold/hint without collecting or consuming a revision.
- Once trust meets the threshold, the same hotspot collects the clock clue normally.

Run and observe RED:

```powershell
npm test -- --run src/__tests__/dialogueFlow.test.ts src/__tests__/gamePagePresentation.test.ts
```

### Step 2: Implement cinematic task prompts and feedback

Add typed `suggestedPrompts` to `ChatPanel`. Render them above the input as compact physical transcript strips, not bubbles or colored orbs. Each prompt is a native button and calls the same `sendMessage(text)` function as typed input.

Render one `role="status" aria-live="polite"` task feedback line in the dialogue panel. Examples:

- `陈守义愿意多说一些 · 信任 +10`
- `线索归档 · 皮影道具箱`
- `这段记忆仍被防备遮住 · 信任达到“初识”后再查看`

Handle `fragment.locked` events in `Game.vue`: do not mark the hotspot explored; show its canonical hint; open its configured NPC when available. Auto-select newly collected dialogue evidence if it belongs to the active hypothesis.

### Step 3: Verify GREEN and full frontend suite

```powershell
npm test -- --run src/__tests__/dialogueFlow.test.ts src/__tests__/gamePagePresentation.test.ts
npm test -- --run
npm run build
```

### Step 4: Commit

```powershell
git commit -m "feat: make dialogue unlock playable evidence"
```

---

## Task 5: Present the 1972 consequence inside the 1990 scene

**Files:**

- Modify: `frontend/src/types/game.ts`
- Modify: `frontend/src/composables/useScene.ts`
- Modify: `frontend/src/components/CinematicStage.vue`
- Modify: `frontend/src/views/Game.vue`
- Modify: `frontend/src/styles/cinematic-game.css`
- Modify: `frontend/src/__tests__/sceneFlow.test.ts`
- Modify: `frontend/src/__tests__/gamePagePresentation.test.ts`

### Step 1: Write failing consequence tests

Test that:

- `useScene` retains canonical `applied_consequences` from `/api/game/scene`.
- Entering 1990 after `encourage_art` passes `legacy_carried` into `CinematicStage`, appends its scene text to the opening narration, and renders a visible “因果回声” cue.
- Entering after `discourage_art` uses `legacy_suppressed` and never renders the carried copy.
- Unknown/no consequence leaves the base stage unchanged.

Run and observe RED:

```powershell
npm test -- --run src/__tests__/sceneFlow.test.ts src/__tests__/gamePagePresentation.test.ts
```

### Step 2: Implement a restrained cinematic consequence treatment

Pass the active consequence variant into `CinematicStage` as data, not hard-coded scene branching in `Game.vue`.

For 1990:

- `legacy_carried`: slightly warmer trunk-side practical light, open-lid/visible-puppet foreground emphasis, and a short paper-note cue.
- `legacy_suppressed`: cooler, more occluded trunk-side treatment with a half-closed visual mask.

Use CSS/Pixi overlays and the existing 1990 physical imagery; do not introduce floating spheres, generic cards, or a duplicate background. The scene-entry narration must include the authoritative `scene_text`, so the consequence remains understandable with reduced motion or images disabled.

### Step 3: Verify GREEN, build, and reduced-motion behavior

```powershell
npm test -- --run src/__tests__/sceneFlow.test.ts src/__tests__/gamePagePresentation.test.ts
npm test -- --run
npm run build
```

### Step 4: Commit

```powershell
git commit -m "feat: reveal 1972 consequences in 1990"
```

---

## Task 6: Integrate, visually QA, document, and review

**Files:**

- Modify: `CHANGELOG.md`
- Modify: `design-qa.md` only by appending a clearly isolated 1990 verification section; preserve all pre-existing edits byte-for-byte outside the appended block
- Add: `.codex-run/qa/1990-reasoning/*` screenshots (ignored artifacts only)

### Step 1: Run fresh automated verification

From the repository root:

```powershell
python -m pytest backend -q
python scripts/validate_content.py
Set-Location frontend
npm test -- --run
npm run build
```

Expected baseline growth: backend must exceed 294 tests; frontend must exceed 125 tests. Zero failures are required.

### Step 2: Browser QA the complete loop

Run the app with the existing approved project commands. Verify both 1972 branches and capture desktop plus mobile screenshots:

1. 1972 evidence → correct hypothesis → `encourage_art`.
2. 1990 ticket + letter → rejected survival hypothesis and corrective feedback.
3. Locked trunk → canonical dialogue prompt → trunk clue + one-time trust gain.
4. Clock locked before trust and collected after threshold.
5. Correct modern-story hypothesis → choices unlock.
6. Reload/save round-trip retains collected fragments and confirmed hypothesis.
7. Repeat from 1972 `discourage_art` and verify the alternate consequence treatment.
8. At 390×844, evidence cards remain selectable, prompt buttons are at least 44px, no critical controls clip, and reduced-motion remains understandable.

### Step 3: Update release notes

Add an `Unreleased` entry to `CHANGELOG.md` covering gameplay, dialogue, consequences, accessibility, and tests. Append only the verified results to `design-qa.md`; do not rewrite the user's existing draft.

### Step 4: Request final code review and fix all findings

Review the complete branch diff from the pre-plan base through HEAD for:

- spec compliance;
- authoritative state/revision behavior;
- content validation completeness;
- save compatibility;
- AI degradation path (no soft lock);
- keyboard/mobile/reduced-motion accessibility;
- accidental changes to `design-qa.md` or generated/local model files.

Repeat the full verification commands after every review fix.

### Step 5: Commit final integration notes

```powershell
git commit -m "docs: record 1990 gameplay milestone"
```

