# 拾忆 P0-A 产品稳定底座 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将现有五场景原型改造成可构建、可测试、可部署、可完整通关且能承载后续电影级 UI/美术重构的稳定产品底座。

**Architecture:** 后端成为内容与游戏规则的唯一权威来源，以版本化 `GameState` 和确定性应用服务驱动探索、对话、选择、结局与存档；FastAPI 只负责协议映射，SQLAlchemy 只负责持久化，DeepSeek 与 Edge TTS 通过可降级适配器接入。前端先保留 Vue 3 组合式结构，但统一通过一个状态容器应用后端返回的完整状态或差量，并删除热区、碎片关系和选择规则的重复硬编码，为 P0-B 的 Pinia/PixiJS 迁移保留清晰边界。

**Tech Stack:** Python 3.11+、FastAPI、Pydantic 2、SQLAlchemy 2、Alembic、Argon2id、SQLite/PostgreSQL、pytest、Vue 3、TypeScript、Vite、Vitest、Axios、ESLint、Prettier、Docker Compose、GitHub Actions。

## Global Constraints

- 继续使用 Vue 3、FastAPI、DeepSeek 与 Edge TTS，不在 P0-A 更换主技术栈。
- 本地默认 SQLite；生产通过 `DATABASE_URL` 使用腾讯云 PostgreSQL；所有表结构由 Alembic 管理。
- 密码使用 Argon2id；会话令牌仅以哈希形式持久化；浏览器只通过 HttpOnly、SameSite=Lax Cookie 认证，生产启用 Secure。
- 后端内容注册表是场景、NPC、碎片、热区、选择与结局条件的唯一权威来源；前端不得保存第二套内容 ID。
- 权威状态字段固定为 `schema_version`、`game_id`、`revision`、`current_scene`、`visited_scenes`、`collected_fragments`、`revealed_fragments`、`fragment_states`、`npc_trust`、`npc_emotions`、`key_choices`、`butterfly_choices`、`dialogue_history`、`current_mood`、`play_time_seconds`、`started_at`、`chapter`、`ending`。
- AI 只能提供结构化对白建议；所有信任、情绪与碎片效果必须由后端验证后应用。
- TTS 失败不得阻断文字对话；DeepSeek 不可用时必须返回角色化本地对白。
- CI 禁止用 `|| true` 绕过失败；内容校验、Python 检查与测试、前端类型/格式/测试/构建、Docker 构建和 Compose 冒烟测试必须真实执行。
- P0-A 不制作五年代最终电影级资产；P0-A 通过后立即进入 P0-B 的 1972 全屏电影舞台纵向切片。

---

## File Map

### Backend domain and content

- `backend/domain/game_state.py`：权威状态、对话记录、关键选择和状态差量的 Pydantic 模型。
- `backend/domain/errors.py`：机器可读领域错误码与异常。
- `backend/content/models.py`：场景、NPC、碎片、热区、选择和结局内容模型。
- `backend/content/registry.py`：加载、索引并交叉验证所有内容。
- `backend/data/hotspots.json`：五场景热区及碎片引用。
- `backend/data/choices.json`：标准化关键选择、场景跳转和状态效果。
- `backend/data/endings.json`：四个结局的确定性条件与展示元数据。
- `backend/application/game_service.py`：创建游戏、进入场景、探索热区、记录选择和计算结局。
- `backend/application/dialogue_service.py`：校验 NPC/场景、调用 AI 适配器、应用合法效果并记录双方消息。

### Backend integration and persistence

- `backend/integrations/deepseek.py`：DeepSeek 超时、有限重试、熔断、结构化解析与本地降级。
- `backend/integrations/tts.py`：Edge TTS 输入限制、并发、原子缓存和容量清理。
- `backend/persistence/models.py`：用户、哈希会话和带修订号的用户存档表。
- `backend/persistence/repositories.py`：会话与存档的查询/并发更新边界。
- `backend/database.py`：`DATABASE_URL` 引擎和可覆盖的会话依赖。
- `alembic.ini`、`alembic/env.py`、`alembic/versions/20260726_0001_product_foundation.py`：全新未上线数据库结构。
- `backend/api/auth.py`、`save.py`、`scene.py`、`dialogue.py`、`ending.py`、`tts.py`：只处理请求/响应/Cookie/错误映射。

### Frontend state and protocol

- `frontend/src/types/game.ts`：与后端一致的内容、状态、对话和错误类型。
- `frontend/src/api/index.ts`：同域 `/api`、Cookie 会话、统一错误归一化。
- `frontend/src/composables/useGameState.ts`：单一客户端状态、修订检查和完整状态替换。
- `frontend/src/composables/useScene.ts`：从场景接口加载展示模型。
- `frontend/src/composables/useHotspots.ts`：由响应式场景模型派生热区，不保存内容。
- `frontend/src/domain/fragmentGraph.ts`：由注册表返回的碎片关系构造展示图。
- `frontend/src/views/Game.vue`：编排探索、对话、选择和场景切换，不直接实现领域规则。
- `frontend/src/components/FragmentGraph.vue`、`ChatPanel.vue`、`HotspotOverlay.vue`：消费规范化 props 并发出意图事件。
- `frontend/eslint.config.js`、`.prettierrc.json`：稳定工具链配置。

### Operations and documentation

- `requirements.txt`：锁定 Argon2、Alembic、PostgreSQL、Edge TTS、格式与静态检查依赖。
- `Dockerfile`、`frontend/Dockerfile`、`frontend/nginx.conf`、`docker-compose.yml`、`.env.example`：同域可部署运行栈。
- `.github/workflows/ci.yml`：真实质量门和 Compose 冒烟测试。
- `README.md`、`TEST_REPORT.md`、`UPGRADE_PLAN.md`、`CHANGELOG.md`：与实际交付同步。

---

### Task 1: Restore the frontend quality baseline

**Files:**
- Create: `frontend/eslint.config.js`
- Create: `frontend/.prettierrc.json`
- Modify: `frontend/package.json`
- Modify: `frontend/package-lock.json`
- Modify: `frontend/src/__tests__/api.test.ts`
- Modify: `frontend/src/composables/useWebVitals.ts`
- Modify: `frontend/src/types/game.ts`
- Modify: all `frontend/src/**/*.ts` and `frontend/src/**/*.vue` files reported by TypeScript, ESLint, or Prettier

**Interfaces:**
- Consumes: current Vue components and `frontend/src/api/index.ts`.
- Produces: commands `npm run typecheck`, `npm run lint`, `npm run check`, `npm test`, and `npm run build` that all exit zero.

- [x] **Step 1: Make the API mock represent the Axios instance contract**

Add `interceptors.request.use`, `interceptors.response.use`, `defaults`, and verb mocks to `frontend/src/__tests__/api.test.ts`, then assert the exported client uses `withCredentials: true` and no Authorization header.

```ts
const axiosInstance = {
  defaults: { withCredentials: true, headers: { common: {} } },
  interceptors: {
    request: { use: vi.fn() },
    response: { use: vi.fn() },
  },
  get: vi.fn(),
  post: vi.fn(),
  delete: vi.fn(),
}
```

- [x] **Step 2: Run the API test and preserve the expected RED**

Run: `cd frontend && npm test -- src/__tests__/api.test.ts`

Expected: FAIL because the current client still reads/writes bearer tokens and does not configure the Cookie-only contract.

- [x] **Step 3: Add explicit typecheck/lint scripts and flat ESLint configuration**

Use `vue-eslint-parser`, `@typescript-eslint/parser`, `eslint-plugin-vue`, and `eslint-config-prettier` in `frontend/eslint.config.js`; add these scripts:

```json
{
  "typecheck": "vue-tsc -b",
  "lint": "eslint src",
  "lint:fix": "eslint src --fix",
  "format": "prettier --write \"src/**/*.{ts,vue,json,css}\"",
  "check": "prettier --check \"src/**/*.{ts,vue,json,css}\""
}
```

- [x] **Step 4: Fix current compiler and API-client failures without suppressions**

Replace removed `onFID` usage with `onINP`, add all actual state fields to `GameState`, remove unused bindings/imports, type emitted component events, remove references to missing `preset_dialogues`, and set Axios to `baseURL: '/api'`, `withCredentials: true`.

```ts
export interface ApiError {
  code: string
  message: string
  status: number
}
```

- [x] **Step 5: Update direct API paths after using `/api` as base URL**

Change client calls from `/api/scene/detail` to `/scene/detail` and apply the same rule to every endpoint so the final URL contains exactly one `/api` prefix.

- [x] **Step 6: Run the complete frontend baseline**

Run:

```powershell
Set-Location frontend
npm run typecheck
npm run lint
npm run format
npm run check
npm test
npm run build
```

Expected: every command exits zero; Vitest has no unhandled errors; `dist` contains no `http://localhost`.

- [x] **Step 7: Commit**

```powershell
git add frontend
git commit -m "fix: restore frontend quality baseline"
```

---

### Task 2: Introduce canonical content models and reference validation

**Files:**
- Create: `backend/content/__init__.py`
- Create: `backend/content/models.py`
- Create: `backend/content/registry.py`
- Create: `backend/data/hotspots.json`
- Create: `backend/data/choices.json`
- Create: `backend/data/endings.json`
- Create: `backend/tests/content/test_registry.py`
- Modify: `backend/data/scenes.json`
- Modify: `backend/data/npcs.json`
- Modify: `backend/data/fragments.json`

**Interfaces:**
- Consumes: existing five scene, seven NPC, and seventeen fragment records.
- Produces: `ContentRegistry.load(data_dir: Path) -> ContentRegistry`, `ContentRegistry.validate() -> None`, `get_scene(scene_id: str) -> SceneContent`, `get_hotspot(hotspot_id: str) -> HotspotContent`, `get_choice(choice_id: str) -> ChoiceContent`, and immutable ID-indexed mappings.

- [x] **Step 1: Write registry failure tests**

Cover duplicate IDs, missing NPCs/fragments, hotspot fragments from the wrong scene, invalid choice source/target scenes, NPC reveal references, missing fallback assets, and unreachable ending condition fields.

```python
def test_hotspot_fragment_must_belong_to_same_scene(tmp_content):
    tmp_content.hotspots[0]["fragment_id"] = "fragment_1990_ticket"
    with pytest.raises(ContentValidationError, match="HOTSPOT_FRAGMENT_SCENE_MISMATCH"):
        ContentRegistry.from_documents(tmp_content.documents)
```

- [x] **Step 2: Run the registry tests to verify RED**

Run: `pytest backend/tests/content/test_registry.py -q`

Expected: FAIL with `ModuleNotFoundError: backend.content`.

- [x] **Step 3: Define strict Pydantic content models**

Use `ConfigDict(extra="forbid", frozen=True)` and explicit fields. `HotspotContent` must contain `id`, `scene_id`, `label`, normalized coordinates, optional `fragment_id`, optional `npc_id`, `interaction`, and `presentation_event`. `ChoiceContent` must contain `id`, `scene_id`, `label`, optional `target_scene`, and typed effects.

- [x] **Step 4: Implement load, indexes, and cross-reference validation**

Load UTF-8 JSON once, reject duplicate IDs before building maps, and raise `ContentValidationError(code, references)` containing stable machine-readable codes.

```python
class ContentRegistry:
    def get_scene(self, scene_id: str) -> SceneContent:
        try:
            return self.scenes[scene_id]
        except KeyError as exc:
            raise DomainError("SCENE_NOT_FOUND", scene_id) from exc
```

- [x] **Step 5: Normalize all five-scene content**

Define exactly five scene IDs, seven NPC IDs, seventeen fragment IDs, scene-correct hotspots, standardized choices for 1972/1990/2024/2050/2089, and four endings. Remove invalid IDs `fragment_childhood_photo`, `fragment_medicine_label`, `fragment_wedding_photo`, `fragment_xiaoyu_letter`, `fragment_su_family_letter`, plus all three-era graph aliases.

- [x] **Step 6: Add whole-registry acceptance assertions**

```python
def test_shipping_content_counts_and_references():
    registry = ContentRegistry.load(DATA_DIR)
    assert len(registry.scenes) == 5
    assert len(registry.fragments) == 17
    assert len(registry.endings) == 4
    registry.validate()
```

- [x] **Step 7: Run tests**

Run: `pytest backend/tests/content/test_registry.py -q`

Expected: PASS with all shipping-content reference checks executed.

- [x] **Step 8: Commit**

```powershell
git add backend/content backend/data backend/tests/content
git commit -m "feat: add canonical content registry"
```

---

### Task 3: Define the versioned authoritative game state

**Files:**
- Create: `backend/domain/__init__.py`
- Create: `backend/domain/errors.py`
- Create: `backend/domain/game_state.py`
- Create: `backend/tests/domain/test_game_state.py`
- Modify: `backend/engine/world.py`
- Modify: `frontend/src/types/game.ts`
- Modify: `frontend/src/__tests__/gameState.test.ts`

**Interfaces:**
- Consumes: `ContentRegistry`.
- Produces: `GameState.new(registry, now, game_id) -> GameState`, `GameState.model_validate(...)`, `DialogueMessage`, `KeyChoiceRecord`, `FragmentState`, and the exact JSON contract consumed by TypeScript.

- [x] **Step 1: Write state schema and initial-state tests**

Assert all eighteen required fields, UUID game ID, `schema_version == 1`, `revision == 0`, current/visited `scene_1972`, timezone-aware ISO start time, bounded trust/emotions, no duplicate fragment IDs, and rejection of unknown fields.

```python
def test_initial_state_has_versioned_contract(registry, fixed_now):
    state = GameState.new(registry, fixed_now, UUID(int=1))
    assert state.current_scene == "scene_1972"
    assert state.visited_scenes == ["scene_1972"]
    assert state.model_dump(mode="json")["schema_version"] == 1
```

- [x] **Step 2: Run backend state tests to verify RED**

Run: `pytest backend/tests/domain/test_game_state.py -q`

Expected: FAIL because `backend.domain.game_state` does not exist.

- [x] **Step 3: Implement strict state models and validators**

Use `extra="forbid"`; model dialogue roles as `player | npc | system`; model fragment status as `hidden | revealed | collected`; clamp trust to `0..100`; validate every state ID against the injected registry through `validate_content_references(registry)`.

- [x] **Step 4: Replace the legacy initial-state factory**

Make `backend/engine/world.py:create_initial_state()` delegate to `GameState.new(...).model_dump(mode="json")` during the compatibility period.

- [x] **Step 5: Mirror the schema in TypeScript and test representative decoding**

Define literal unions, arrays, maps, and nullable ending without `any`. Update `gameState.test.ts` to assert complete state replacement preserves `revision`, `visited_scenes`, dialogue roles, and fragment states.

- [x] **Step 6: Run focused tests**

Run:

```powershell
pytest backend/tests/domain/test_game_state.py -q
Set-Location frontend
npm test -- src/__tests__/gameState.test.ts
npm run typecheck
```

Expected: all commands PASS.

- [x] **Step 7: Commit**

```powershell
git add backend/domain backend/tests/domain backend/engine/world.py frontend/src/types/game.ts frontend/src/__tests__/gameState.test.ts
git commit -m "feat: version authoritative game state"
```

---

### Task 4: Build deterministic gameplay application services

**Files:**
- Create: `backend/application/__init__.py`
- Create: `backend/application/game_service.py`
- Create: `backend/tests/application/test_game_service.py`
- Create: `backend/tests/application/test_ending_paths.py`
- Modify: `backend/api/scene.py`
- Modify: `backend/api/ending.py`
- Modify: `backend/api/butterfly.py`
- Modify: `backend/engine/butterfly.py`
- Modify: `backend/engine/ending.py`

**Interfaces:**
- Consumes: `ContentRegistry`, `GameState`.
- Produces: `GameService.create_game()`, `get_scene_view(state)`, `explore(state, hotspot_id, expected_revision)`, `record_choice(state, choice_id, expected_revision)`, `evaluate_ending(state)`, `ActionResult(state, events)`.

- [x] **Step 1: Write exploration and revision failure tests**

Assert wrong-scene hotspot yields `HOTSPOT_INVALID`, stale revisions yield `GAME_REVISION_CONFLICT`, fragment hotspots reveal/collect only their canonical fragment, repeated idempotent exploration does not duplicate state, and successful mutations increment revision exactly once.

- [x] **Step 2: Write choice and four-ending reachability tests**

For every shipping choice, assert source-scene enforcement, standard `KeyChoiceRecord`, derived `butterfly_choices`, target transition, and revision increment. Build one legal state-machine path per ending and assert all four ending IDs are returned.

```python
@pytest.mark.parametrize("path,ending_id", LEGAL_ENDING_PATHS)
def test_every_ending_has_a_legal_path(service, path, ending_id):
    state = service.create_game()
    for action in path:
        state = apply_action(service, state, action).state
    assert service.evaluate_ending(state).id == ending_id
```

- [x] **Step 3: Run application tests to verify RED**

Run: `pytest backend/tests/application/test_game_service.py backend/tests/application/test_ending_paths.py -q`

Expected: FAIL because `GameService` and typed results do not exist.

Execution note: the first focused run returned 11 PASS because the service and route files had already landed in the same active implementation batch. The files were inspected line by line, the HTTP revision-conflict contract was exercised through `TestClient`, and the full backend suite then passed 117 tests.

- [x] **Step 4: Implement pure deterministic mutations**

Copy the validated Pydantic state before mutation; validate `expected_revision`; apply content-declared effects only; append newly visited scenes once; recompute chapter/current mood; increment revision once; return presentation events without embedding UI implementation.

```python
class ActionResult(BaseModel):
    state: GameState
    events: list[PresentationEvent] = Field(default_factory=list)
```

- [x] **Step 5: Map scene and ending routes to services**

Expose:

```text
GET  /api/game/new
POST /api/game/scene
POST /api/game/explore
POST /api/game/choice
POST /api/game/ending
```

Keep legacy routes only as thin deprecated aliases until the frontend migration in Task 6 is complete. Errors use `{"error":{"code":"...","message":"..."}}`.

- [x] **Step 6: Run old and new backend tests**

Run: `pytest backend/tests -q`

Expected: PASS, including all four legal ending paths and legacy engine regression tests.

- [x] **Step 7: Commit**

```powershell
git add backend/application backend/api backend/engine backend/tests/application
git commit -m "feat: make gameplay transitions deterministic"
```

---

### Task 5: Make dialogue authoritative and safely degradable

**Files:**
- Create: `backend/integrations/__init__.py`
- Create: `backend/integrations/deepseek.py`
- Create: `backend/application/dialogue_service.py`
- Create: `backend/tests/integrations/test_deepseek.py`
- Create: `backend/tests/application/test_dialogue_service.py`
- Modify: `backend/api/dialogue.py`
- Modify: `backend/engine/npc.py`
- Modify: `backend/config.py`

**Interfaces:**
- Consumes: `ContentRegistry`, `GameState`, `NpcContent`.
- Produces: `DialogueSuggestion`, `DeepSeekDialogueClient.suggest(context)`, `DialogueService.chat(state, npc_id, player_input, expected_revision) -> DialogueResult`.

- [x] **Step 1: Write DeepSeek adapter failure-mode tests**

Mock success, connection timeout, 429/5xx transient retries, invalid JSON, invalid enum/value ranges, and open-circuit behavior. Assert no raw provider response is returned and fallback dialogue matches the requested NPC.

- [x] **Step 2: Write dialogue state-effect tests**

Assert NPC belongs to current scene, player input is 1–500 characters, both player and NPC messages are appended, history is capped at 60 recent messages, trust remains `0..100`, only an NPC-owned fragment can be revealed, and revision increments once.

- [x] **Step 3: Run dialogue tests to verify RED**

Run: `pytest backend/tests/integrations/test_deepseek.py backend/tests/application/test_dialogue_service.py -q`

Expected: FAIL because the adapter and service do not exist.

Execution note: the focused run failed on the missing integration and application modules as expected. HTTP contract tests were then added and initially failed against the legacy route before the authoritative API mapping was implemented.

- [x] **Step 4: Implement the structured adapter**

Configure connect/read/total timeout values from settings, retry only timeout/429/5xx at most twice, open the circuit after five consecutive failures for 30 seconds, parse into:

```python
class DialogueSuggestion(BaseModel):
    reply: str = Field(min_length=1, max_length=1000)
    trust_change: int = Field(ge=-10, le=10)
    npc_mood: Literal["neutral", "warm", "guarded", "sad", "hopeful"]
    fragment_revealed: str | None = None
    inner_thought: str = Field(default="", max_length=300)
```

- [x] **Step 5: Implement the authoritative dialogue service**

Build the prompt from content plus a bounded state projection, invoke the adapter, replace invalid/failed suggestions with `npc.fallback_dialogue`, validate requested effects against registry ownership, mutate state, and return the full updated state plus reply metadata.

- [x] **Step 6: Replace the dialogue API contract**

Accept `npc_id`, `player_input`, `game_state`, and `expected_revision`; return `state`, `reply`, `fragment_data`, `trust_change`, `npc_mood`, `inner_thought`, and `degraded`. Preserve SSE only if it can emit the same final authoritative result; otherwise remove the unused streaming endpoint during this task.

Execution note: `/api/dialogue/chat` now uses the authoritative service. The legacy streaming route remains only as a temporary compatibility endpoint for the current frontend and will be deleted as part of Task 6, when `ChatPanel` migrates to the canonical response.

- [x] **Step 7: Run all backend tests**

Run: `pytest backend/tests -q`

Expected: PASS with DeepSeek network fully mocked.

- [x] **Step 8: Commit**

```powershell
git add backend/integrations backend/application/dialogue_service.py backend/api/dialogue.py backend/engine/npc.py backend/config.py backend/tests
git commit -m "feat: add authoritative degradable dialogue"
```

---

### Task 6: Rewire the frontend to canonical scene and state responses

**Files:**
- Create: `frontend/src/domain/fragmentGraph.ts`
- Create: `frontend/src/__tests__/sceneFlow.test.ts`
- Create: `frontend/src/__tests__/dialogueFlow.test.ts`
- Modify: `frontend/src/api/index.ts`
- Modify: `frontend/src/composables/useGameState.ts`
- Modify: `frontend/src/composables/useScene.ts`
- Modify: `frontend/src/composables/useHotspots.ts`
- Modify: `frontend/src/views/Game.vue`
- Modify: `frontend/src/components/FragmentGraph.vue`
- Modify: `frontend/src/components/ChatPanel.vue`
- Modify: `frontend/src/components/HotspotOverlay.vue`

**Interfaces:**
- Consumes: Task 4/5 API responses and Task 3 TypeScript types.
- Produces: `replaceAuthoritativeState(next: GameState)`, reactive `sceneView`, canonical `hotspots`, and intent methods `exploreHotspot`, `submitChoice`, `sendDialogue`.

- [ ] **Step 1: Write a reactive scene/hotspot regression test**

Mount the game state/scene composables with scene 1972, replace state with scene 1990 and a new scene view, then assert visible hotspot IDs change and no 1972 hotspots remain.

- [ ] **Step 2: Write state-writeback tests**

Mock explore, choice, and dialogue responses with increasing revisions. Assert each response replaces local authoritative state, choice effects persist, both dialogue roles are present, stale response revisions are ignored with a diagnostic error, and no local rule mutation occurs before the response.

- [ ] **Step 3: Run frontend flow tests to verify RED**

Run: `cd frontend && npm test -- src/__tests__/sceneFlow.test.ts src/__tests__/dialogueFlow.test.ts`

Expected: FAIL because hotspots capture a plain scene string and choice/dialogue responses are not written back.

- [ ] **Step 4: Implement strict response application**

```ts
function replaceAuthoritativeState(next: GameState): void {
  if (gameState.value && next.game_id === gameState.value.game_id && next.revision < gameState.value.revision) {
    throw new StateRevisionError(next.revision, gameState.value.revision)
  }
  gameState.value = structuredClone(next)
}
```

Keep only view-local state such as open panel, selected NPC, animation event queue, and sound preference outside `GameState`.

- [ ] **Step 5: Derive hotspots and fragment graph from server data**

Accept `ComputedRef<SceneView | null>` in `useHotspots`; return `computed(() => sceneView.value?.hotspots ?? [])`. Build graph nodes from canonical fragments and relations rather than the nonexistent `puppet_stage`, `carving_knife`, and three-era arrays.

- [ ] **Step 6: Simplify Game.vue orchestration**

Load current scene whenever `gameState.current_scene` changes, pass canonical data to child components, call the authoritative endpoints, apply returned state, and queue returned presentation events. Remove fragment, trust, key-choice, and scene-transition mutations from the view.

- [ ] **Step 7: Run all frontend gates**

Run:

```powershell
Set-Location frontend
npm run typecheck
npm run lint
npm run check
npm test
npm run build
```

Expected: all PASS and the build has no hard-coded invalid fragment IDs.

- [ ] **Step 8: Commit**

```powershell
git add frontend/src
git commit -m "refactor: use canonical gameplay state in frontend"
```

---

### Task 7: Replace bearer authentication with secure Cookie sessions

**Files:**
- Modify: `requirements.txt`
- Create: `backend/persistence/__init__.py`
- Create: `backend/persistence/models.py`
- Create: `backend/persistence/repositories.py`
- Create: `backend/security.py`
- Create: `backend/tests/api/test_auth.py`
- Create: `backend/tests/persistence/test_sessions.py`
- Modify: `backend/database.py`
- Modify: `backend/api/auth.py`
- Modify: `backend/main.py`
- Modify: `backend/config.py`
- Delete: `backend/models/token.py`
- Modify: `backend/models/__init__.py`

**Interfaces:**
- Consumes: SQLAlchemy session dependency and application settings.
- Produces: `PasswordHasher`, `hash_session_token(raw: str) -> str`, `get_current_user(request, db)`, `SessionRepository.create/revoke/resolve`, and Cookie name `memory_session`.

- [ ] **Step 1: Write authentication integration tests**

Use a temporary SQLite database dependency override. Assert registration sets an HttpOnly SameSite=Lax Cookie without returning a token body, passwords are Argon2 hashes, the database stores only SHA-256 session-token hashes, `/me` works by Cookie, logout revokes the current session and clears the Cookie, expired sessions fail, duplicate usernames return a stable error, and invalid credentials do not disclose which field was wrong.

- [ ] **Step 2: Run auth tests to verify RED**

Run: `pytest backend/tests/api/test_auth.py backend/tests/persistence/test_sessions.py -q`

Expected: FAIL because bearer tokens and unsalted password SHA-256 are still active.

- [ ] **Step 3: Add locked runtime dependencies**

Add `argon2-cffi`, `alembic`, `psycopg[binary]`, and `edge-tts`; update vulnerable direct packages to versions reported non-vulnerable by their authoritative advisories. Install from `requirements.txt` and record exact pins.

- [ ] **Step 4: Implement password and session primitives**

Use `argon2.PasswordHasher` defaults compatible with Argon2id, generate 32 random bytes with `secrets.token_urlsafe(32)`, hash raw session tokens with SHA-256 for lookup, compare with `secrets.compare_digest`, and use timezone-aware UTC at the API boundary.

- [ ] **Step 5: Implement Cookie auth routes**

Set `memory_session` with `httponly=True`, `samesite="lax"`, `secure=settings.COOKIE_SECURE`, `max_age=settings.SESSION_TTL_SECONDS`, and `path="/"`. Configure CORS credentials only for explicit configured origins; never use wildcard origins with credentials.

- [ ] **Step 6: Run auth and full backend tests**

Run: `pytest backend/tests -q`

Expected: PASS; no test sends an Authorization header.

- [ ] **Step 7: Commit**

```powershell
git add requirements.txt backend
git commit -m "feat: secure authentication with cookie sessions"
```

---

### Task 8: Add migrated, isolated, revision-safe saves

**Files:**
- Create: `alembic.ini`
- Create: `alembic/env.py`
- Create: `alembic/script.py.mako`
- Create: `alembic/versions/20260726_0001_product_foundation.py`
- Create: `backend/tests/api/test_saves.py`
- Modify: `backend/persistence/models.py`
- Modify: `backend/persistence/repositories.py`
- Modify: `backend/api/save.py`
- Modify: `backend/database.py`
- Delete: `backend/models/save.py`
- Delete: `backend/models/user.py`

**Interfaces:**
- Consumes: Cookie user, strict `GameState`.
- Produces: unique `(user_id, slot_id)` save slots, `SaveRepository.write(user_id, slot_id, expected_revision, state)`, and `GAME_REVISION_CONFLICT` mapped to HTTP 409.

- [ ] **Step 1: Write save isolation and concurrency tests**

Assert two users can own the same slot number, cannot list/load/delete each other’s slot, persisted JSON is schema-valid, first save requires expected revision 0, update succeeds only with the stored revision, stale update returns 409 and preserves the newer state, and invalid state is rejected before persistence.

- [ ] **Step 2: Run save tests to verify RED**

Run: `pytest backend/tests/api/test_saves.py -q`

Expected: FAIL because the current save API accepts arbitrary dictionaries and has no revision compare-and-swap.

- [ ] **Step 3: Define the clean initial migration**

Create `users`, `sessions`, and `save_slots` with named primary keys, foreign keys with cascade behavior, unique username, unique `(user_id, slot_id)`, session hash index, state schema/revision columns, UTC timestamp defaults, and PostgreSQL-compatible column types.

- [ ] **Step 4: Implement repository compare-and-swap**

Lock the existing row where supported, compare `expected_revision`, validate `GameState`, store JSON plus `state_schema_version` and `state_revision`, commit, and return a typed save DTO. Map integrity races to stable domain errors.

- [ ] **Step 5: Replace manual `create_all`/SQLite ALTER logic**

Keep `init_db()` only for test/bootstrap compatibility if needed; production and Compose startup must execute `alembic upgrade head`. `DATABASE_URL` must accept both SQLite and PostgreSQL URLs.

- [ ] **Step 6: Run migration and API tests on fresh SQLite**

Run:

```powershell
$env:DATABASE_URL = "sqlite:///./data/p0a-migration-test.db"
alembic upgrade head
alembic current
pytest backend/tests/api/test_saves.py -q
```

Expected: Alembic reports `20260726_0001 (head)` and save tests PASS. Remove only the explicitly named temporary database after confirming its resolved path is inside `data`.

- [ ] **Step 7: Run all backend tests**

Run: `pytest backend/tests -q`

Expected: PASS.

- [ ] **Step 8: Commit**

```powershell
git add alembic.ini alembic backend
git commit -m "feat: add revision-safe isolated saves"
```

---

### Task 9: Harden Edge TTS without making speech a gameplay dependency

**Files:**
- Create: `backend/integrations/tts.py`
- Create: `backend/tests/integrations/test_tts.py`
- Modify: `backend/api/tts.py`
- Modify: `backend/config.py`
- Modify: `backend/main.py`
- Modify: `.gitignore`

**Interfaces:**
- Consumes: installed `edge-tts`, TTS settings, validated text/voice/rate/pitch.
- Produces: `TtsService.synthesize(request) -> TtsResult`, SHA-256 cache key, atomic cache files, and `TTS_UNAVAILABLE` responses that the frontend can ignore.

- [ ] **Step 1: Write TTS tests**

Assert the cache key changes with text/voice/rate/pitch, text above 500 characters is rejected, unsupported voices/rates/pitches are rejected, concurrent identical requests synthesize once, temporary files are atomically renamed, failed synthesis leaves no partial file, and cleanup respects both maximum file count and byte size.

- [ ] **Step 2: Run TTS tests to verify RED**

Run: `pytest backend/tests/integrations/test_tts.py -q`

Expected: FAIL because the bounded TTS service does not exist.

- [ ] **Step 3: Implement bounded synthesis and cache**

Use an `asyncio.Semaphore`, one lock per cache key, `tempfile.NamedTemporaryFile(delete=False, dir=cache_dir)`, `Path.replace`, deterministic SHA-256 filenames, least-recently-used cleanup by access/modified time, and guaranteed temporary-file cleanup in `finally`.

- [ ] **Step 4: Map the TTS API and frontend fallback**

Return a same-origin `/tts/{filename}` URL on success; return status 503 with `TTS_UNAVAILABLE` on provider failure. The frontend must keep the textual reply visible, stop only the failed audio attempt, and allow the next dialogue action.

- [ ] **Step 5: Run integration and frontend tests**

Run:

```powershell
pytest backend/tests/integrations/test_tts.py -q
Set-Location frontend
npm test
```

Expected: PASS.

- [ ] **Step 6: Commit**

```powershell
git add backend/integrations/tts.py backend/tests/integrations/test_tts.py backend/api/tts.py backend/config.py backend/main.py frontend/src .gitignore
git commit -m "feat: make tts bounded and nonblocking"
```

---

### Task 10: Make Docker and same-origin production deployment reproducible

**Files:**
- Modify: `Dockerfile`
- Modify: `frontend/Dockerfile`
- Modify: `frontend/nginx.conf`
- Modify: `docker-compose.yml`
- Modify: `.env.example`
- Create: `scripts/smoke.ps1`
- Create: `backend/tests/test_config.py`

**Interfaces:**
- Consumes: `/api/health`, frontend static output, Alembic migration command.
- Produces: one-command `docker compose up --build`, backend listening on `0.0.0.0`, Nginx proxy for `/api/` and `/tts/`, and browser bundles with no localhost API.

- [ ] **Step 1: Write configuration tests**

Assert production rejects wildcard credentialed origins, Cookie Secure follows environment, default database is SQLite, supplied PostgreSQL URL is preserved, backend default container host is `0.0.0.0`, and no secret value is included in health responses.

- [ ] **Step 2: Run config tests to verify RED**

Run: `pytest backend/tests/test_config.py -q`

Expected: FAIL on current host/CORS/health behavior.

- [ ] **Step 3: Implement container startup and health behavior**

Run `alembic upgrade head` before Uvicorn; listen on `0.0.0.0`; use Python rather than unavailable `curl` for backend healthcheck unless curl is explicitly installed; return only status, service name, version, and database status from `/api/health`.

- [ ] **Step 4: Configure same-origin Nginx**

Serve the SPA with history fallback, proxy `/api/` to `backend:8000`, proxy `/tts/` to the backend with bounded caching, forward standard proxy headers, and never embed a browser-facing backend hostname.

- [ ] **Step 5: Make Compose independent of a missing `.env`**

Provide safe local defaults via `${NAME:-default}`, make `.env` optional, mount persistent database/TTS volumes, order health-dependent services, and keep DeepSeek optional so the game boots in degraded mode.

- [ ] **Step 6: Add a deterministic smoke script**

`scripts/smoke.ps1` must request the frontend root, `/api/health`, `/api/scene/list`, and `/api/game/new`, assert status codes and the five-scene count, then exit nonzero on any failure.

- [ ] **Step 7: Validate and run containers**

Run:

```powershell
docker compose config
docker compose build
docker compose up -d
powershell -ExecutionPolicy Bypass -File scripts/smoke.ps1
docker compose down
```

Expected: config/build/start/smoke/stop all succeed. If Docker is unavailable, record that exact environment limitation and still run `docker compose config` if the CLI supports it; do not claim container verification.

- [ ] **Step 8: Commit**

```powershell
git add Dockerfile frontend/Dockerfile frontend/nginx.conf docker-compose.yml .env.example scripts backend/tests/test_config.py backend/config.py backend/main.py
git commit -m "fix: make production stack reproducible"
```

---

### Task 11: Replace the invalid CI workflow with enforceable gates

**Files:**
- Modify: `.github/workflows/ci.yml`
- Create: `scripts/validate_content.py`

**Interfaces:**
- Consumes: all local quality commands from Tasks 1–10.
- Produces: valid GitHub Actions jobs `backend`, `frontend`, `docker`, and `smoke`, with no masked failures.

- [ ] **Step 1: Add a standalone content validation command**

`scripts/validate_content.py` imports `ContentRegistry`, loads `backend/data`, calls `validate()`, prints exact scene/NPC/fragment/hotspot/choice/ending counts, and exits nonzero on `ContentValidationError`.

- [ ] **Step 2: Run the command locally**

Run: `python scripts/validate_content.py`

Expected: exit zero and report 5 scenes and 17 fragments.

- [ ] **Step 3: Rewrite the workflow with valid YAML**

Use Python 3.11 and current LTS Node, cache pip/npm, install from locked files, run content validation, pytest, TypeScript, ESLint, Prettier, Vitest, Vite build, Docker builds, Compose startup, and `scripts/smoke.ps1`. Every `upload-artifact` use must include a valid `path`; services must be cleaned up under `if: always()`.

- [ ] **Step 4: Validate workflow syntax and forbidden bypasses**

Run:

```powershell
rg -n "\|\| true|continue-on-error:\s*true" .github/workflows/ci.yml
docker run --rm -v "${PWD}:/repo" rhysd/actionlint:latest -color /repo/.github/workflows/ci.yml
```

Expected: `rg` returns no matches; actionlint exits zero.

- [ ] **Step 5: Re-run the commands used by CI**

Run backend tests, all frontend gates, both Docker builds, Compose smoke, and content validation exactly as encoded in the workflow.

Expected: every local equivalent exits zero.

- [ ] **Step 6: Commit**

```powershell
git add .github/workflows/ci.yml scripts/validate_content.py
git commit -m "ci: enforce product stability gates"
```

---

### Task 12: Synchronize product documentation and progress records

**Files:**
- Modify: `README.md`
- Modify: `TEST_REPORT.md`
- Modify: `UPGRADE_PLAN.md`
- Create or Modify: `CHANGELOG.md`
- Modify: `docs/superpowers/plans/2026-07-26-p0a-product-stability.md`

**Interfaces:**
- Consumes: verified commands, actual test counts, final endpoint/deployment/auth behavior.
- Produces: user-facing setup/deployment instructions and a changelog that distinguishes P0-A complete from P0-B/P1/P2 planned work.

- [ ] **Step 1: Capture factual final outputs**

Record tool versions, pytest/Vitest test totals, build result, content counts, migration head, Docker smoke result, and `npm audit --omit=dev` result from fresh commands. Do not copy stale counts.

- [ ] **Step 2: Rewrite README run and deployment instructions**

Document local Python/frontend setup, optional DeepSeek behavior, Cookie auth, Alembic, Docker Compose, environment variables, Tencent Cloud PostgreSQL URL form, health endpoint, test commands, and five-scene/seventeen-fragment/four-ending scope.

- [ ] **Step 3: Replace stale test and upgrade claims**

Make `TEST_REPORT.md` a dated evidence report with commands and outcomes. Mark P0-A tasks complete only when verified; list P0-B 1972 movie-stage work as next; remove claims that i18n, CI, TypeScript, or deployment are complete unless their gates pass.

- [ ] **Step 4: Add a Keep-a-Changelog-style unreleased entry**

Under `CHANGELOG.md` `Unreleased`, describe canonical content/state, deterministic endings, secure sessions, revision-safe saves, AI/TTS fallback, frontend state repair, CI, and deployment. Do not claim five-era cinematic art in P0-A.

- [ ] **Step 5: Mark this plan’s completed checkboxes**

Change each executed `- [ ]` to `- [x]` only after its command has passed or its explicit environment limitation is recorded in `TEST_REPORT.md`.

- [ ] **Step 6: Run documentation consistency checks**

Run:

```powershell
rg -n "3个场景|9个碎片|Bearer|localStorage.*token|http://localhost:8000|\|\| true" README.md TEST_REPORT.md UPGRADE_PLAN.md CHANGELOG.md frontend/src .github/workflows
python scripts/validate_content.py
```

Expected: no stale product claims or bearer-token implementation matches; content validation passes.

- [ ] **Step 7: Commit**

```powershell
git add README.md TEST_REPORT.md UPGRADE_PLAN.md CHANGELOG.md docs/superpowers/plans/2026-07-26-p0a-product-stability.md
git commit -m "docs: record p0a stability foundation"
```

---

### Task 13: Perform final security, regression, and acceptance verification

**Files:**
- Modify only files required to fix a failed acceptance gate

**Interfaces:**
- Consumes: the complete P0-A implementation.
- Produces: evidence that every P0-A acceptance criterion passes and a clean branch ready for P0-B.

- [ ] **Step 1: Run the backend acceptance suite**

Run:

```powershell
python scripts/validate_content.py
pytest backend/tests -q
alembic upgrade head
alembic current
```

Expected: all pass; output proves five scenes, seventeen fragments, four endings, auth/session isolation, revision conflicts, and DeepSeek/TTS degradation.

- [ ] **Step 2: Run the frontend acceptance suite**

Run:

```powershell
Set-Location frontend
npm ci
npm run typecheck
npm run lint
npm run check
npm test
npm run build
npm audit --omit=dev
```

Expected: all quality commands pass; production audit has no high/critical finding; built assets contain no browser-local backend URL.

- [ ] **Step 3: Run deployment acceptance**

Run:

```powershell
Set-Location ..
docker compose config
docker compose build
docker compose up -d
powershell -ExecutionPolicy Bypass -File scripts/smoke.ps1
docker compose down
```

Expected: all pass and cleanup runs even if smoke fails.

- [ ] **Step 4: Inspect the complete diff and repository state**

Run:

```powershell
git diff master...HEAD --check
git diff --stat master...HEAD
git status --short --branch
git log --oneline --decorate -15
```

Expected: no whitespace errors, no accidental secrets/generated databases/TTS files/node_modules, and no unrelated user changes.

- [ ] **Step 5: Fix any failed gate through a new RED/GREEN cycle**

For each failure, add the smallest regression test that reproduces it, run that test to confirm failure, implement the correction, run the focused test and then the affected full gate, and create a focused commit naming the behavior fixed.

- [ ] **Step 6: Use the verification and branch-finishing skills**

Read and follow `superpowers:verification-before-completion`, then `superpowers:finishing-a-development-branch`. Do not push, merge, or create a PR without explicit user authorization.

- [ ] **Step 7: Commit final verification-only corrections if present**

```powershell
git add backend frontend scripts .github Dockerfile docker-compose.yml alembic.ini alembic docs README.md TEST_REPORT.md UPGRADE_PLAN.md CHANGELOG.md
git commit -m "fix: close p0a acceptance gaps"
```

Before committing, unstage every path that has no final-correction change or belongs to an unrelated user edit. If no correction was required, do not create an empty commit.

---

## P0-A to P0-B Handoff

After Task 13 passes, create the separate P0-B implementation plan before editing cinematic UI code. It must use the already approved visual direction:

- 东方皮影电影感。
- 全屏电影舞台与桌面 2.39:1 构图。
- 常态“动画电影写实”，记忆失真/碎片重组/情绪高潮“超现实记忆电影”。
- 先完成 1972 西安老巷纵向切片，再扩展其余四年代。
- Vue Router、Pinia、PixiJS、分层高分辨率资产、桌面/移动双构图、减少动态效果、键盘与屏幕阅读器支持。

P0-B 开始前必须保留本计划的全部 P0-A 质量门，电影演出代码不得重新引入内容规则或权威状态的前端硬编码。
