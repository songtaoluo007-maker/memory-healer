# Memory Reasoning And Hotspot Language Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace every floating orb hotspot with cinematic object-local cues and add a persistent, server-authoritative evidence-to-hypothesis loop for the 1972 first act.

**Architecture:** Add a data-driven `HypothesisContent` contract to the canonical content registry and persist confirmed hypotheses in `GameState`. The frontend keeps only the in-progress evidence selection locally, confirms it through the authoritative gameplay API, and gates the act-ending choice from the returned server state. The global hotspot overlay becomes DOM-based, accessible, and visually quiet until hover, keyboard focus, or scan mode.

**Tech Stack:** Python 3.12, FastAPI, Pydantic 2, Vue 3 Composition API, TypeScript 6, Vitest, CSS.

## Global Constraints

- Preserve the existing cinematic assets, `Noto Serif SC` typography, and palette tokens in `frontend/src/styles/cinematic.css`.
- Do not add a new visual asset: the selected design uses the existing scene, character, and fragment artwork.
- Remove persistent circular hotspot marks in every scene, not only the example hotspot.
- Keep keyboard activation, visible focus, reduced-motion support, and a scan mode that reveals every available hotspot label.
- The 1972 choice remains unavailable until the player confirms the configured hypothesis with two collected fragments.
- The server remains authoritative for collected evidence, hypothesis confirmation, revision checks, and scene choices.
- Existing saves that do not contain `confirmed_hypotheses` must continue to validate through the field default.

---

### Task 1: Canonical Hypothesis Content And State

**Files:**
- Create: `backend/data/hypotheses.json`
- Modify: `backend/content/models.py`
- Modify: `backend/content/registry.py`
- Modify: `backend/domain/game_state.py`
- Test: `backend/tests/content/test_registry.py`
- Test: `backend/tests/domain/test_game_state.py`

**Interfaces:**
- Produces: `HypothesisContent(id, scene_id, question, statement, evidence_ids, resolution)`
- Produces: `ContentRegistry.hypotheses` and `get_hypothesis(hypothesis_id)`
- Produces: `GameState.confirmed_hypotheses: dict[str, str]`

- [ ] **Step 1: Write failing content and state tests**

```python
def test_registry_loads_first_act_hypothesis(registry: ContentRegistry) -> None:
    hypothesis = registry.get_hypothesis("hypothesis_1972_legacy")
    assert hypothesis.scene_id == "scene_1972"
    assert hypothesis.evidence_ids == (
        "fragment_grandpa_knife",
        "fragment_shadow_puppet",
    )


def test_initial_state_has_no_confirmed_hypotheses(
    registry: ContentRegistry,
    fixed_now: datetime,
) -> None:
    state = GameState.new(registry, fixed_now, UUID(int=9))
    assert state.confirmed_hypotheses == {}
```

- [ ] **Step 2: Run tests and verify they fail because the contracts do not exist**

Run: `python -m pytest backend/tests/content/test_registry.py backend/tests/domain/test_game_state.py -q`

Expected: FAIL mentioning `get_hypothesis`, `hypotheses`, or `confirmed_hypotheses`.

- [ ] **Step 3: Add the canonical content and state contracts**

`backend/data/hypotheses.json`:

```json
[
  {
    "id": "hypothesis_1972_legacy",
    "scene_id": "scene_1972",
    "question": "陈守义为什么仍想把皮影传下去？",
    "statement": "爷爷留下的刻刀与仍在发光的戏幕证明：他守住的不是旧物，而是一种仍能被讲述的生活。",
    "evidence_ids": ["fragment_grandpa_knife", "fragment_shadow_puppet"],
    "resolution": "两条记忆互相印证。你可以带着这份理解作出选择。"
  }
]
```

Add a frozen Pydantic model:

```python
class HypothesisContent(ContentModel):
    id: str
    scene_id: str
    question: str = Field(min_length=1, max_length=120)
    statement: str = Field(min_length=1, max_length=300)
    evidence_ids: tuple[str, ...] = Field(min_length=2)
    resolution: str = Field(min_length=1, max_length=200)
```

Load and validate the file in `ContentRegistry`, reject hypotheses whose scene is missing, whose evidence is missing, whose evidence belongs to another scene, or whose evidence list contains duplicates. Add:

```python
def get_hypothesis(self, hypothesis_id: str) -> HypothesisContent:
    try:
        return self.hypotheses[hypothesis_id]
    except KeyError as exc:
        raise DomainError(
            "HYPOTHESIS_INVALID",
            f"推理命题不存在：{hypothesis_id}",
        ) from exc
```

Add to `GameState`:

```python
confirmed_hypotheses: dict[str, str] = Field(default_factory=dict)
```

Validate each `scene_id -> hypothesis_id` pair against the registry.

- [ ] **Step 4: Run the focused tests and verify they pass**

Run: `python -m pytest backend/tests/content/test_registry.py backend/tests/domain/test_game_state.py -q`

Expected: PASS.

- [ ] **Step 5: Commit the canonical contract**

```bash
git add backend/data/hypotheses.json backend/content/models.py backend/content/registry.py backend/domain/game_state.py backend/tests/content/test_registry.py backend/tests/domain/test_game_state.py
git commit -m "feat: add canonical memory hypotheses"
```

### Task 2: Authoritative Hypothesis Confirmation

**Files:**
- Modify: `backend/application/game_service.py`
- Modify: `backend/api/game.py`
- Test: `backend/tests/application/test_game_service.py`

**Interfaces:**
- Consumes: `ContentRegistry.get_hypothesis()` and `GameState.confirmed_hypotheses`
- Produces: `GameService.confirm_hypothesis(state, hypothesis_id, evidence_ids, expected_revision)`
- Produces: `POST /api/game/hypothesis`
- Produces: `SceneView.hypotheses: list[HypothesisContent]`

- [ ] **Step 1: Write failing service tests**

```python
def collect_first_act_evidence(service: GameService, state: GameState) -> GameState:
    for hotspot_id in ("hotspot_1972_knife", "hotspot_1972_shadow_stage"):
        state = service.explore(
            state,
            hotspot_id,
            expected_revision=state.revision,
        ).state
    return state


def test_confirm_hypothesis_records_authoritative_scene_reasoning(
    service: GameService,
) -> None:
    state = collect_first_act_evidence(service, service.create_game())
    result = service.confirm_hypothesis(
        state,
        "hypothesis_1972_legacy",
        ["fragment_grandpa_knife", "fragment_shadow_puppet"],
        expected_revision=state.revision,
    )
    assert result.state.revision == state.revision + 1
    assert result.state.confirmed_hypotheses == {
        "scene_1972": "hypothesis_1972_legacy"
    }
    assert result.events[0].type == "hypothesis.confirmed"


def test_choice_requires_confirmed_scene_hypothesis(service: GameService) -> None:
    state = service.create_game()
    with pytest.raises(DomainError) as caught:
        service.record_choice(
            state,
            "encourage_art",
            expected_revision=state.revision,
        )
    assert caught.value.code == "HYPOTHESIS_REQUIRED"
```

Also cover uncollected evidence, wrong-scene hypotheses, duplicate evidence, stale revisions, and idempotent reconfirmation.

- [ ] **Step 2: Run the focused tests and verify the expected failures**

Run: `python -m pytest backend/tests/application/test_game_service.py -q`

Expected: FAIL because `confirm_hypothesis` and the choice gate do not exist.

- [ ] **Step 3: Implement the service and API**

Add the method:

```python
def confirm_hypothesis(
    self,
    state: GameState,
    hypothesis_id: str,
    evidence_ids: list[str],
    *,
    expected_revision: int,
) -> ActionResult:
    self._check_revision(state, expected_revision)
    state.validate_content_references(self.registry)
    hypothesis = self.registry.get_hypothesis(hypothesis_id)
    if hypothesis.scene_id != state.current_scene:
        raise DomainError("HYPOTHESIS_INVALID", "该推理不属于当前场景")
    if len(evidence_ids) != len(set(evidence_ids)):
        raise DomainError("EVIDENCE_INVALID", "推理证据不能重复")
    if set(evidence_ids) != set(hypothesis.evidence_ids):
        raise DomainError("EVIDENCE_INVALID", "证据不足以支持这项推理")
    if not set(evidence_ids).issubset(state.collected_fragments):
        raise DomainError("EVIDENCE_NOT_COLLECTED", "仍有证据尚未取得")
    if state.confirmed_hypotheses.get(state.current_scene) == hypothesis.id:
        return ActionResult(state=state.model_copy(deep=True))

    payload = state.model_dump(mode="python")
    payload["confirmed_hypotheses"][state.current_scene] = hypothesis.id
    payload["revision"] += 1
    next_state = GameState.model_validate(payload)
    next_state.validate_content_references(self.registry)
    return ActionResult(
        state=next_state,
        events=[
            PresentationEvent(
                type="hypothesis.confirmed",
                content_id=hypothesis.id,
                payload={"evidence_ids": list(hypothesis.evidence_ids)},
            )
        ],
    )
```

Gate `record_choice()` when the current scene has configured hypotheses but no confirmed one. Add `HypothesisRequest` to `backend/api/game.py` and expose `/hypothesis`.

- [ ] **Step 4: Run service, API, ending-path, and save tests**

Run: `python -m pytest backend/tests/application backend/tests/api/test_saves.py backend/tests/domain/test_game_state.py -q`

Expected: PASS after updating choice-path fixtures to confirm the first-act hypothesis before leaving 1972.

- [ ] **Step 5: Commit authoritative reasoning**

```bash
git add backend/application/game_service.py backend/api/game.py backend/tests/application backend/tests/api/test_saves.py
git commit -m "feat: validate memory hypotheses before choices"
```

### Task 3: Frontend Reasoning Domain And API

**Files:**
- Create: `frontend/src/domain/memoryReasoning.ts`
- Create: `frontend/src/__tests__/memoryReasoning.test.ts`
- Modify: `frontend/src/types/game.ts`
- Modify: `frontend/src/api/index.ts`
- Modify: `frontend/src/composables/useGameState.ts`
- Modify: `frontend/src/__tests__/api.test.ts`
- Modify: `frontend/src/__tests__/gameState.test.ts`

**Interfaces:**
- Consumes: `Hypothesis`, `SceneFragment`, and `GameState`
- Produces: `buildReasoningSnapshot(hypothesis, fragments, selectedIds, confirmed)`
- Produces: `toggleEvidenceSelection(selectedIds, evidenceId, allowedIds)`
- Produces: `confirmHypothesis(hypothesisId, evidenceIds)`

- [ ] **Step 1: Write failing domain tests**

```typescript
it('keeps only collected configured evidence selectable', () => {
  const snapshot = buildReasoningSnapshot(
    hypothesis,
    [
      { ...knife, is_collected: true },
      { ...stage, is_collected: false },
    ],
    ['fragment_grandpa_knife', 'fragment_shadow_puppet'],
    false,
  )

  expect(snapshot.evidence.map((item) => [item.id, item.available, item.selected])).toEqual([
    ['fragment_grandpa_knife', true, true],
    ['fragment_shadow_puppet', false, false],
  ])
  expect(snapshot.canConfirm).toBe(false)
})

it('allows confirmation only when every required evidence item is selected', () => {
  const snapshot = buildReasoningSnapshot(
    hypothesis,
    [
      { ...knife, is_collected: true },
      { ...stage, is_collected: true },
    ],
    ['fragment_grandpa_knife', 'fragment_shadow_puppet'],
    false,
  )
  expect(snapshot.canConfirm).toBe(true)
  expect(snapshot.progressLabel).toBe('02 / 02')
})
```

- [ ] **Step 2: Run the domain test and verify it fails because the module is absent**

Run: `npm test -- src/__tests__/memoryReasoning.test.ts`

Expected: FAIL resolving `../domain/memoryReasoning`.

- [ ] **Step 3: Implement the minimal pure domain and HTTP contract**

Add frontend types:

```typescript
export interface Hypothesis {
  id: string
  scene_id: string
  question: string
  statement: string
  evidence_ids: string[]
  resolution: string
}
```

Add `hypotheses: Hypothesis[]` to `SceneView` and optional backward-compatible `confirmed_hypotheses?: Record<string, string>` to `GameState`.

Add:

```typescript
export const confirmHypothesis = (
  hypothesisId: string,
  evidenceIds: string[],
  gameState: GameState,
  expectedRevision: number,
) =>
  api.post<ActionResult>('/game/hypothesis', {
    hypothesis_id: hypothesisId,
    evidence_ids: evidenceIds,
    game_state: gameState,
    expected_revision: expectedRevision,
  })
```

Expose a `confirmHypothesis` method from `useGameState()` that applies the returned authoritative state.

- [ ] **Step 4: Run domain, API, and game-state tests**

Run: `npm test -- src/__tests__/memoryReasoning.test.ts src/__tests__/api.test.ts src/__tests__/gameState.test.ts`

Expected: PASS.

- [ ] **Step 5: Commit the frontend reasoning contract**

```bash
git add frontend/src/domain/memoryReasoning.ts frontend/src/__tests__/memoryReasoning.test.ts frontend/src/types/game.ts frontend/src/api/index.ts frontend/src/composables/useGameState.ts frontend/src/__tests__/api.test.ts frontend/src/__tests__/gameState.test.ts
git commit -m "feat: add frontend memory reasoning contract"
```

### Task 4: Global Hotspot Language And First-Act Gameplay UI

**Files:**
- Create: `frontend/src/components/MemoryReasoningPanel.vue`
- Modify: `frontend/src/components/HotspotOverlay.vue`
- Modify: `frontend/src/views/Game.vue`
- Modify: `frontend/src/styles/cinematic-game.css`
- Modify: `frontend/src/__tests__/cinematicShell.test.ts`
- Create: `design-qa.md`

**Interfaces:**
- Consumes: `hypothesis`, `sceneFragments`, `gameState`, `FragmentPresentation`
- Emits: `confirm(hypothesisId: string, evidenceIds: string[])`
- `HotspotOverlay` adds `scanMode: boolean` and emits the existing `explore` event.

- [ ] **Step 1: Write failing shell behavior tests**

Add source-backed tests that import the real domain functions and assert the game state gate, plus a render smoke test through the existing Vite/Vue compile path. The behavior assertion is:

```typescript
expect(
  isSceneDecisionUnlocked(
    'scene_1972',
    [hypothesis],
    {},
  ),
).toBe(false)

expect(
  isSceneDecisionUnlocked(
    'scene_1972',
    [hypothesis],
    { scene_1972: hypothesis.id },
  ),
).toBe(true)
```

- [ ] **Step 2: Run the focused frontend tests and verify the decision gate fails**

Run: `npm test -- src/__tests__/memoryReasoning.test.ts src/__tests__/cinematicShell.test.ts`

Expected: FAIL because the decision-unlock helper or integration does not exist.

- [ ] **Step 3: Implement the selected high-fidelity UI**

Replace the SVG circle implementation with absolutely positioned semantic buttons:

```vue
<button
  v-for="hotspot in hotspots"
  :key="hotspot.id"
  class="perception-cue"
  :class="{
    explored: exploredIds.has(hotspot.id),
    active: hoveredId === hotspot.id,
    scanning: scanMode,
  }"
  :style="{ left: `${hotspot.x * 100}%`, top: `${hotspot.y * 100}%` }"
  type="button"
  :aria-label="`${interactionLabel(hotspot.interaction)}：${hotspot.label}`"
  @click="handleClick(hotspot)"
>
  <span class="cue-frame" aria-hidden="true" />
  <span class="cue-copy">
    <small>{{ interactionLabel(hotspot.interaction) }}</small>
    <strong>{{ hotspot.label }}</strong>
  </span>
</button>
```

The default state is a quiet 20–28px object-local corner mark. Hover, focus-visible, and scan mode reveal a thin label plate. Explored cues become a short static archival line without a circle or checkmark.

`MemoryReasoningPanel.vue` renders:

- The question: `陈守义为什么仍想把皮影传下去？`
- Evidence cards using `FragmentArtwork` and the existing fragment art.
- A `编织假说` action enabled only when both required fragments are collected and selected.
- The confirmed resolution and a visible `因果选择已开放` state.

`Game.vue` adds:

- `scanMode` toggle.
- Local `selectedEvidenceIds`.
- `handleConfirmHypothesis()` calling `useGameState().confirmHypothesis`.
- A server-backed `decisionUnlocked` computed value.
- A locked decision plate instead of clickable choice buttons until confirmation.
- Narrative feedback for evidence confirmation and error states.

- [ ] **Step 4: Run all automated verification**

Run:

```bash
npm test
npm run typecheck
npm run build
python -m pytest
python scripts/validate_content.py
git diff --check
```

Expected: every command exits `0`.

- [ ] **Step 5: Run browser interaction and design QA**

At `1440 × 900`, verify:

1. No hotspot appears as a circle.
2. Tab focus exposes labels and Enter activates the hotspot.
3. Scan mode reveals all unresolved labels and can be turned off.
4. Clicking the knife and shadow stage collects both evidence cards.
5. Selecting both evidence cards enables `编织假说`.
6. Confirming the hypothesis changes the mission panel to resolved.
7. The two causal choices become enabled only after server confirmation.
8. The layout remains usable at `1024 × 768` and `390 × 844`.
9. Browser console contains no errors.

Capture the implementation and compare it in one combined image with:

`C:\Users\Administrator\.codex\visualizations\2026\07\26\019f9e41-8aae-7ab0-8203-4d72746caf60\figma-memory-proposal\board-3.png`

Write `design-qa.md` with `final result: passed` only after all P0/P1/P2 findings are fixed.

- [ ] **Step 6: Commit the gameplay UI**

```bash
git add frontend/src/components/MemoryReasoningPanel.vue frontend/src/components/HotspotOverlay.vue frontend/src/views/Game.vue frontend/src/styles/cinematic-game.css frontend/src/__tests__ design-qa.md
git commit -m "feat: add cinematic memory reasoning loop"
```
