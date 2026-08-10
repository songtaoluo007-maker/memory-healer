# Cinematic AI Voice Platform Pilot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a provider-neutral cinematic voice platform, validate it with a fully playable 1972 first-act pilot, and preserve the ability to expand the rewritten story without reworking voice infrastructure.

**Architecture:** Canonical voice profiles and fixed voice lines live in the existing content registry. Approved fixed assets are generated at build time through managed cloud AI voices and shipped with the game. A backend `VoiceService` resolves approved fixed assets first, then uses the existing Edge TTS integration for runtime dialogue; the already-implemented provider-neutral HTTP primary remains optional, remote-only, and disabled by default. The frontend receives one playback contract and routes it through a dedicated voice queue and mixer instead of embedding provider behavior in dialogue components.

**Tech Stack:** Python 3.12 / FastAPI / Pydantic 2 / httpx / pytest, Edge TTS 7.2.8, FFmpeg 8.1, an optional disabled-by-default provider-neutral HTTP primary, Vue 3 / TypeScript / Vitest, Web Audio API, Git LFS.

> **User override — 2026-07-28:** Do not install, download, bundle, or run a local speech model. Task 3 is retained only as an already-completed optional remote-provider contract. Task 5 generates the seven approved 1972 fixed assets directly through Edge managed cloud voices. Tasks 11–12 must document and verify the no-local-model path. This override governs every older CosyVoice-local instruction below.

## Global Constraints

- All character voices must be purely synthetic; never import human recordings as prompts, seeds, training data, or fine-tuning data.
- Use Edge managed cloud voices for the fixed-asset pilot and runtime dialogue. Any optional primary provider must be remote, disabled by default, and must never be required for boot or play.
- Never create `.local/cosyvoice`, install a model runtime, download model weights, or require a local speech-model process.
- Preserve text-first gameplay: voice failure must never block dialogue, state mutation, scene navigation, saving, or endings.
- Keep one stable `voice_lineage_id` across Chen Shouyi ages 25/43/77 and one across Xiaoyu ages 22/48/87.
- Correct Xiaoyu's canonical age to 87 in 2089 and remove the current “22-year-old student” contradiction.
- Serve the first complete fixed-voice pilot only for the 1972 act; do not batch-produce the remaining eras until the separate narrative-expansion specification freezes their scripts.
- Fixed voice assets must be approved before entering the manifest; unapproved candidates stay outside the runtime asset path.
- Lock the cloud voice ID, `edge-tts` package revision, synthetic provenance, voice profile version, line version, and post-processing version in every generated manifest entry.
- Preserve the existing same-origin `/api` contract and add same-origin `/voice` assets for local Vite and production Nginx.
- Keep the current backend and frontend test suites green; add focused red-green tests for every new contract and failure path.
- Follow the existing cinematic palette, typography, and accessibility patterns for voice controls; do not introduce floating orb controls or unrelated visual redesign.

---

## File Structure

### Canonical content

- Create `backend/data/voice_profiles.json`: versioned character voice profiles and synthetic seed provenance.
- Create `backend/data/voice_lines.json`: fixed line IDs, text, speaker profile, delivery, emotion, priority, and spatial preset.
- Create `backend/data/voice_assets.json`: approved fixed-asset manifest; begins as an empty array and is populated by the pilot generator.
- Modify `backend/content/models.py`: voice profile, line, asset, and optional content-reference models.
- Modify `backend/content/registry.py`: load, validate, and expose voice documents.
- Modify `backend/data/npcs.json`: map every NPC to a voice profile and correct 2089 Xiaoyu.
- Modify `backend/data/scenes.json`: add optional transition voice IDs and correct the 2089 description.
- Modify `backend/data/fragments.json`: add optional memory voice IDs.
- Modify `backend/data/hypotheses.json`: add optional resolution voice IDs.
- Modify `backend/data/endings.json`: add optional ending voice IDs without generating final ending audio in this pilot.

### Backend voice platform

- Create `backend/integrations/voice_contracts.py`: provider-neutral request/result/protocol types.
- Create `backend/integrations/edge_voice.py`: adapter over the existing bounded `TtsService`.
- Create `backend/integrations/cosyvoice.py`: authenticated local HTTP client for the pinned bridge.
- Create `backend/application/voice_service.py`: fixed-asset resolution, primary/fallback orchestration, circuit breaker, and stable silent result.
- Create `backend/api/voice.py`: runtime speech and fixed-line lookup endpoints.
- Modify `backend/config.py`: voice paths, provider switches, timeouts, circuit thresholds, and bridge secret.
- Modify `backend/main.py`: voice error mapping, router registration, and `/voice` static mount.
- Keep `backend/api/tts.py` and `/tts` temporarily available for backward compatibility until the frontend migration is complete.

### CosyVoice bridge and production tools

- Create `tools/cosyvoice_bridge/app.py`: narrow local bridge exposing health and WAV synthesis.
- Create `scripts/voice/setup_cosyvoice.ps1`: pinned Windows/uv setup for the reviewed 4060 Ti machine.
- Create `scripts/voice/generate_ai_seeds.py`: generate synthetic seed candidates from built-in AI voices only.
- Create `scripts/voice/generate_fixed_assets.py`: render approved fixed lines, normalize audio, and write a deterministic manifest.
- Create `scripts/voice/validate_voice_assets.py`: verify hashes, durations, formats, approvals, and references.
- Create `.gitattributes`: route approved WAV/Opus/MP3 assets through Git LFS.

### Frontend audio platform

- Create `frontend/src/audio/mixer.ts`: shared voice/music/SFX gain policy and persisted volumes.
- Create `frontend/src/composables/useMusicBus.ts`: extracted music and ambience behavior.
- Create `frontend/src/composables/useSfxBus.ts`: extracted interaction sound behavior.
- Create `frontend/src/composables/useVoicePlayback.ts`: queue, priority, pause, replay, skip, and lifecycle.
- Create `frontend/src/components/VoiceSubtitle.vue`: safe-area phrase subtitle presentation driven by reviewed cue timing.
- Create `frontend/src/components/VoiceControls.vue`: compact cinematic voice controls.
- Modify `frontend/src/composables/useAudio.ts`: compatibility facade over the three focused buses.
- Modify `frontend/src/api/index.ts`: voice request and fixed-line lookup calls.
- Modify `frontend/src/types/game.ts`: voice contracts and canonical content references.
- Modify `frontend/src/components/ChatPanel.vue`: replace direct TTS with provider-neutral voice playback.
- Modify `frontend/src/views/Game.vue`: play first-act transition, NPC intro, fragment, and hypothesis lines.
- Modify `frontend/src/views/Ending.vue`: stop all voice on unmount and expose the future ending-line hook without shipping unapproved ending audio.
- Modify `frontend/vite.config.ts` and `frontend/nginx.conf`: same-origin `/voice` proxy.

### Timeline art correction

- Create `frontend/src/assets/cinematic/xiaoyu-2089-aged-solid.webp`: age-correct 87-year-old Xiaoyu portrait.
- Modify `frontend/src/stage/presentation.ts`: use the age-correct portrait.
- Modify `frontend/src/components/CinematicStage.vue`: treat 2089 Xiaoyu as a physical elderly character, not a 22-year-old projection.

---

### Task 1: Canonical Voice Content and Xiaoyu Timeline

**Files:**
- Create: `backend/data/voice_profiles.json`
- Create: `backend/data/voice_lines.json`
- Create: `backend/data/voice_assets.json`
- Modify: `backend/content/models.py`
- Modify: `backend/content/registry.py`
- Modify: `backend/data/npcs.json`
- Modify: `backend/data/scenes.json`
- Modify: `backend/data/fragments.json`
- Modify: `backend/data/hypotheses.json`
- Modify: `backend/data/endings.json`
- Modify: `backend/tests/content/test_registry.py`

**Interfaces:**
- Consumes: existing `ContentModel`, `ContentRegistry`, canonical NPC/scene/fragment/hypothesis/ending documents.
- Produces: `VoiceProfileContent`, `VoiceLineContent`, `VoiceAssetContent`, `ContentRegistry.get_voice_profile(id)`, `ContentRegistry.get_voice_line(id)`, and `ContentRegistry.get_voice_asset(line_id)`.

- [ ] **Step 1: Add the voice documents to the shipping-content fixture and assert the canonical profile/line relationships**

```python
DOCUMENT_FILES = {
    "scenes": "scenes.json",
    "npcs": "npcs.json",
    "fragments": "fragments.json",
    "hotspots": "hotspots.json",
    "choices": "choices.json",
    "hypotheses": "hypotheses.json",
    "endings": "endings.json",
    "voice_profiles": "voice_profiles.json",
    "voice_lines": "voice_lines.json",
    "voice_assets": "voice_assets.json",
}


def test_registry_loads_voice_profiles_and_first_act_lines() -> None:
    registry = ContentRegistry.load(DATA_DIR)

    assert registry.get_npc("chen_shouyi_young").voice_profile_id == "chen_shouyi.age_25"
    assert registry.get_npc("xiaoyu").age == 87
    assert registry.get_npc("xiaoyu").voice_profile_id == "xiaoyu.age_87"
    assert registry.get_voice_profile("chen_shouyi.age_43").voice_lineage_id == "chen_shouyi"
    assert registry.get_voice_profile("xiaoyu.age_87").voice_lineage_id == "xiaoyu"
    assert registry.get_voice_line("hypothesis_1972_legacy.resolution").delivery == "pre_generated"
    assert registry.get_voice_asset("hypothesis_1972_legacy.resolution") is None
```

- [ ] **Step 2: Add validation failures for missing profiles, duplicate line IDs, stale line text, subtitle drift, and invalid asset references**

```python
def test_npc_voice_profile_must_exist(shipping_documents: dict[str, object]) -> None:
    documents = copy.deepcopy(shipping_documents)
    npcs = documents["npcs"]
    assert isinstance(npcs, dict)
    npcs["chen_shouyi_young"]["voice_profile_id"] = "missing.profile"

    expect_validation_code(documents, "NPC_VOICE_PROFILE_NOT_FOUND")


def test_voice_asset_line_must_exist(shipping_documents: dict[str, object]) -> None:
    documents = copy.deepcopy(shipping_documents)
    assets = documents["voice_assets"]
    assert isinstance(assets, list)
    assets.append(
        {
            "id": "missing.line",
            "filename": "fixed/missing.opus",
            "media_type": "audio/ogg; codecs=opus",
            "duration_ms": 1200,
            "sha256": "0" * 64,
            "text_sha256": "0" * 64,
            "integrated_lufs": -18.0,
            "true_peak_dbfs": -1.0,
            "generator": "cosyvoice3",
            "generator_revision": "074ca6dc9e80a2f424f1f74b48bdd7d3fea531cc",
            "profile_version": 1,
            "postprocess_version": 1,
            "cues": [],
            "approved": True,
        }
    )

    expect_validation_code(documents, "VOICE_ASSET_LINE_NOT_FOUND")


def test_voice_line_text_must_equal_authoritative_source(
    shipping_documents: dict[str, object],
) -> None:
    documents = copy.deepcopy(shipping_documents)
    lines = documents["voice_lines"]
    assert isinstance(lines, list)
    line = next(item for item in lines if item["id"] == "scene_1972.transition_in")
    line["text"] = "漂移后的副本。"

    expect_validation_code(documents, "VOICE_LINE_TEXT_STALE")


def test_pre_generated_subtitles_must_reconstruct_line(
    shipping_documents: dict[str, object],
) -> None:
    documents = copy.deepcopy(shipping_documents)
    lines = documents["voice_lines"]
    assert isinstance(lines, list)
    line = next(item for item in lines if item["id"] == "scene_1972.transition_in")
    line["subtitle_segments"] = ["不一致的字幕。"]

    expect_validation_code(documents, "VOICE_LINE_SUBTITLE_MISMATCH")
```

- [ ] **Step 3: Run the content tests and verify RED**

Run:

```powershell
python -m pytest backend/tests/content/test_registry.py -q
```

Expected: FAIL because the voice documents and content models do not exist.

- [ ] **Step 4: Add the exact Pydantic content contracts**

```python
class VoiceDialect(ContentModel):
    name: str = "standard_mandarin"
    strength: float = Field(default=0, ge=0, le=1)


class VoiceProviderProfile(ContentModel):
    cosyvoice_seed: str
    cosyvoice_instruction: str
    edge_voice: str
    edge_rate: str = "+0%"
    edge_pitch: str = "+0Hz"


class VoiceProfileContent(ContentModel):
    id: str
    voice_lineage_id: str
    age_stage: int | None = Field(default=None, ge=0, le=200)
    register: str
    pace: float = Field(ge=0.5, le=1.5)
    dialect: VoiceDialect = Field(default_factory=VoiceDialect)
    breathiness: float = Field(default=0, ge=0, le=1)
    emotion_limits: dict[str, float] = Field(default_factory=dict)
    forbidden_traits: tuple[str, ...] = ()
    provider: VoiceProviderProfile
    seed_provenance: Literal["edge_tts_synthetic", "cosyvoice_sft_synthetic"]
    version: int = Field(ge=1)


class VoiceCueContent(ContentModel):
    start_ms: int = Field(ge=0)
    end_ms: int = Field(gt=0)
    text: str = Field(min_length=1)


class VoiceLineContent(ContentModel):
    id: str
    source_ref: str
    speaker_profile: str
    text: str = Field(min_length=1, max_length=1000)
    subtitle_segments: tuple[str, ...] = ()
    emotion: Literal["neutral", "warm", "guarded", "sad", "hopeful"]
    intensity: float = Field(ge=0, le=1)
    space: str
    delivery: Literal["pre_generated", "runtime", "silent"]
    priority: Literal["ending", "critical", "dialogue", "narration", "system"]
    version: int = Field(ge=1)


class VoiceAssetContent(ContentModel):
    id: str
    filename: str
    media_type: Literal["audio/wav", "audio/mpeg", "audio/ogg; codecs=opus"]
    duration_ms: int = Field(gt=0)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    text_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    integrated_lufs: float = Field(ge=-30, le=-10)
    true_peak_dbfs: float = Field(le=0)
    generator: str
    generator_revision: str
    profile_version: int = Field(ge=1)
    postprocess_version: int = Field(ge=1)
    cues: tuple[VoiceCueContent, ...] = ()
    approved: bool
```

Add these fields to existing content:

```python
class SceneContent(ContentModel):
    transition_in_voice_line_id: str | None = None
    transition_out_voice_line_id: str | None = None


class NpcContent(ContentModel):
    voice_profile_id: str
    initial_voice_line_id: str | None = None


class FragmentContent(ContentModel):
    memory_voice_line_id: str | None = None


class HypothesisContent(ContentModel):
    resolution_voice_line_id: str | None = None


class EndingContent(ContentModel):
    voice_line_id: str | None = None
```

- [ ] **Step 5: Add exact profile IDs and NPC mappings**

Create these nine profile IDs:

| Profile ID | Lineage | Age | Synthetic seed | Edge fallback | CosyVoice instruction summary |
| --- | --- | ---: | --- | --- | --- |
| `chen_shouyi.age_25` | `chen_shouyi` | 25 | `seeds/chen_shouyi-base.wav` | `zh-CN-YunxiNeural` | warm young male, low-mid register, mild Xi'an accent |
| `chen_shouyi.age_43` | `chen_shouyi` | 43 | `seeds/chen_shouyi-base.wav` | `zh-CN-YunxiNeural` | same timbre, thicker register, restrained hesitation |
| `chen_shouyi.age_77` | `chen_shouyi` | 77 | `seeds/chen_shouyi-base.wav` | `zh-CN-YunyangNeural` | same timbre, slower, breathy, clear elderly speech |
| `xiaoyu.age_22` | `xiaoyu` | 22 | `seeds/xiaoyu-base.wav` | `zh-CN-XiaoyiNeural` | clear young woman, controlled anxiety |
| `xiaoyu.age_48` | `xiaoyu` | 48 | `seeds/xiaoyu-base.wav` | `zh-CN-XiaoxiaoNeural` | same timbre, mature public-speaking strength |
| `xiaoyu.age_87` | `xiaoyu` | 87 | `seeds/xiaoyu-base.wav` | `zh-CN-XiaoxiaoNeural` | same timbre, slow and clear, retained agency |
| `stranger_1990.age_28` | `stranger_1990` | 28 | `seeds/stranger-1990.wav` | `zh-CN-YunjianNeural` | bright male, brisk, mild Hunan accent |
| `journalist_2050.age_30` | `journalist_2050` | 30 | `seeds/journalist-2050.wav` | `zh-CN-XiaoyiNeural` | clear, restrained, warm professional voice |
| `memory_narrator.archive` | `memory_narrator` | — | `seeds/memory-narrator.wav` | `zh-CN-XiaoxiaoNeural` | low-saturation archive narration with distance |

Map existing NPC IDs exactly:

```text
chen_shouyi_young -> chen_shouyi.age_25
chen_shouyi_1990 -> chen_shouyi.age_43
chen_shouyi_old -> chen_shouyi.age_77
xiaoyu_2050 -> xiaoyu.age_48
xiaoyu -> xiaoyu.age_87
stranger_1990 -> stranger_1990.age_28
journalist_2050 -> journalist_2050.age_30
```

- [ ] **Step 6: Add the exact 1972 pilot line IDs**

Create:

```text
scene_1972.transition_in -> scene:scene_1972.transition_in
scene_1972.transition_out -> scene:scene_1972.transition_out
npc.chen_shouyi_young.intro -> npc:chen_shouyi_young.fallback_dialogue
fragment_shadow_puppet.memory -> fragment:fragment_shadow_puppet.memory_text
fragment_grandpa_knife.memory -> fragment:fragment_grandpa_knife.memory_text
fragment_three_kings.memory -> fragment:fragment_three_kings.memory_text
hypothesis_1972_legacy.resolution -> hypothesis:hypothesis_1972_legacy.resolution
```

Use the current canonical `transition_in`, `transition_out`, `fallback_dialogue`, fragment `memory_text`, and hypothesis `resolution` verbatim. Use `memory_narrator.archive` for transitions and fragment memories, `chen_shouyi.age_25` for the NPC intro, and `memory_narrator.archive` for the hypothesis resolution. Split `subtitle_segments` only at natural Chinese punctuation; never place breath, pause, emotion, or performance directions in visible subtitle text.

The registry must resolve each line ID back to its authoritative scene, NPC, fragment, hypothesis, or ending field and assert exact text equality. Reject drift with `VOICE_LINE_TEXT_STALE`; do not maintain a second editable copy of canonical dialogue. Every `pre_generated` line must have non-empty `subtitle_segments`, and their exact concatenation must equal `text`; reject violations with `VOICE_LINE_SUBTITLE_MISMATCH`.

- [ ] **Step 7: Correct 2089 Xiaoyu content**

Set the NPC age to `87`, change the title to `拾忆技术守护者`, remove “计算机专业大学生” and “年轻女孩”, and rewrite the background/system prompt so she is the same Xiaoyu shown at age 48 in 2050. Preserve her relationship to Chen Shouyi and her doubt about whether technology can replace human memory.

- [ ] **Step 8: Run content tests and the repository content validator**

Run:

```powershell
python -m pytest backend/tests/content/test_registry.py -q
python scripts/validate_content.py
```

Expected: PASS; validator reports five scenes, seven NPCs, seventeen fragments, and a valid voice registry.

- [ ] **Step 9: Commit**

```powershell
git add backend/content backend/data backend/tests/content/test_registry.py
git commit -m "feat: add canonical voice content"
```

---

### Task 2: Provider-Neutral Contracts and Edge Voice Adapter

**Files:**
- Create: `backend/integrations/voice_contracts.py`
- Create: `backend/integrations/edge_voice.py`
- Modify: `backend/integrations/__init__.py`
- Test: `backend/tests/integrations/test_edge_voice.py`

**Interfaces:**
- Consumes: `VoiceProfileContent`, existing `TtsRequest`, `TtsResult`, and `TtsService`.
- Produces: `VoiceSynthesisRequest`, `VoiceSynthesisResult`, `VoiceProvider`, and `EdgeVoiceProvider.synthesize(request)`.

- [ ] **Step 1: Write failing adapter tests**

```python
@pytest.mark.asyncio
async def test_edge_adapter_uses_profile_fallback_settings() -> None:
    tts = RecordingTts()
    provider = EdgeVoiceProvider(tts)
    profile = make_profile(
        edge_voice="zh-CN-YunxiNeural",
        edge_rate="-10%",
        edge_pitch="-5Hz",
    )

    result = await provider.synthesize(
        VoiceSynthesisRequest(
            text="时间不等人，手艺也不等人。",
            profile=profile,
            emotion="guarded",
            intensity=0.4,
            line_id=None,
        )
    )

    assert tts.request == TtsRequest(
        text="时间不等人，手艺也不等人。",
        voice="zh-CN-YunxiNeural",
        rate="-10%",
        pitch="-5Hz",
    )
    assert result.provider == "edge"
    assert result.url == "/tts/voice.mp3"
```

- [ ] **Step 2: Run the focused test and verify RED**

Run:

```powershell
python -m pytest backend/tests/integrations/test_edge_voice.py -q
```

Expected: FAIL because the neutral contracts and adapter are missing.

- [ ] **Step 3: Implement the exact provider-neutral contract**

```python
from dataclasses import dataclass
from typing import Literal, Protocol

from backend.content.models import VoiceCueContent, VoiceProfileContent

VoiceProviderName = Literal["fixed", "cosyvoice", "edge", "silent"]


@dataclass(frozen=True, slots=True)
class VoiceSynthesisRequest:
    text: str
    profile: VoiceProfileContent
    emotion: str
    intensity: float
    line_id: str | None = None


@dataclass(frozen=True, slots=True)
class VoiceSynthesisResult:
    url: str | None
    provider: VoiceProviderName
    cache_hit: bool
    media_type: str | None
    duration_ms: int | None
    line_id: str | None
    cues: tuple[VoiceCueContent, ...]
    degraded: bool


class VoiceProvider(Protocol):
    async def synthesize(self, request: VoiceSynthesisRequest) -> VoiceSynthesisResult:
        raise NotImplementedError
```

- [ ] **Step 4: Implement `EdgeVoiceProvider` as a thin adapter**

The adapter must only translate the canonical profile to `TtsRequest`; it must not contain NPC ID mappings.

```python
class EdgeVoiceProvider:
    def __init__(self, tts_service: TtsService) -> None:
        self.tts_service = tts_service

    async def synthesize(self, request: VoiceSynthesisRequest) -> VoiceSynthesisResult:
        result = await self.tts_service.synthesize(
            TtsRequest(
                text=request.text,
                voice=request.profile.provider.edge_voice,
                rate=request.profile.provider.edge_rate,
                pitch=request.profile.provider.edge_pitch,
            )
        )
        return VoiceSynthesisResult(
            url=result.url,
            provider="edge",
            cache_hit=result.cache_hit,
            media_type="audio/mpeg",
            duration_ms=None,
            line_id=request.line_id,
            cues=(),
            degraded=True,
        )
```

- [ ] **Step 5: Run adapter and existing TTS tests**

Run:

```powershell
python -m pytest backend/tests/integrations/test_edge_voice.py backend/tests/integrations/test_tts.py backend/tests/api/test_tts.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```powershell
git add backend/integrations backend/tests/integrations/test_edge_voice.py
git commit -m "feat: add provider neutral voice contracts"
```

---

### Task 3: Pinned CosyVoice Bridge and HTTP Provider

**Files:**
- Create: `tools/cosyvoice_bridge/app.py`
- Create: `scripts/voice/setup_cosyvoice.ps1`
- Create: `backend/integrations/cosyvoice.py`
- Modify: `backend/config.py`
- Test: `backend/tests/integrations/test_cosyvoice.py`
- Test: `backend/tests/test_config.py`

**Interfaces:**
- Consumes: `VoiceSynthesisRequest`, profile `cosyvoice_seed` and `cosyvoice_instruction`, `httpx.AsyncClient`.
- Produces: local bridge `GET /health`, bridge `POST /v1/synthesize`, and `CosyVoiceHttpProvider.synthesize(request)`.

- [ ] **Step 1: Add failing provider tests using `httpx.MockTransport`**

```python
@pytest.mark.asyncio
async def test_cosyvoice_provider_posts_synthetic_seed_and_returns_cached_url(
    tmp_path: Path,
) -> None:
    seed = tmp_path / "seed.wav"
    seed.write_bytes(b"RIFFsynthetic")
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            headers={"content-type": "audio/wav"},
            content=b"RIFFgenerated",
        )
    )
    provider = CosyVoiceHttpProvider(
        base_url="http://cosy.local",
        bridge_token="test-token",
        cache_dir=tmp_path / "cache",
        seed_root=tmp_path,
        client=httpx.AsyncClient(transport=transport),
        model_revision="Fun-CosyVoice3-0.5B-2512",
    )

    result = await provider.synthesize(make_request(seed_name="seed.wav"))

    assert result.provider == "cosyvoice"
    assert result.url is not None
    assert result.url.startswith("/voice/cache/")
    assert (tmp_path / "cache" / Path(result.url).name).read_bytes() == b"RIFFgenerated"
```

Also assert:

- missing seed raises `VoiceProviderError`;
- timeout raises `VoiceProviderTimeout`;
- non-audio response raises `VoiceProviderError`;
- repeated identical requests make one HTTP request and report `cache_hit=True` on the second result;
- the request includes `X-Voice-Bridge-Token`;
- LRU cleanup enforces both file-count and byte limits;
- cleanup never selects the cache key currently being generated or returned by an in-flight request.

- [ ] **Step 2: Run the provider tests and verify RED**

Run:

```powershell
python -m pytest backend/tests/integrations/test_cosyvoice.py backend/tests/test_config.py -q
```

Expected: FAIL because the provider, settings, and bridge do not exist.

- [ ] **Step 3: Add exact settings**

```python
VOICE_PUBLIC_DIR: Path = ROOT_DIR / "data" / "voice_public"
VOICE_SEED_DIR: Path = ROOT_DIR / "data" / "voice_seeds"
VOICE_PRIMARY_ENABLED: bool = False
VOICE_GENERATION_MAX_CONCURRENCY: int = Field(default=1, ge=1, le=4)
VOICE_CACHE_MAX_FILES: int = Field(default=500, ge=1, le=10000)
VOICE_CACHE_MAX_BYTES: int = Field(default=2_147_483_648, ge=1_048_576)
COSYVOICE_BASE_URL: str = "http://127.0.0.1:50000"
COSYVOICE_BRIDGE_TOKEN: str = ""
COSYVOICE_CONNECT_TIMEOUT_SECONDS: float = Field(default=0.5, ge=0.1, le=10)
COSYVOICE_TOTAL_TIMEOUT_SECONDS: float = Field(default=2.5, ge=0.5, le=30)
COSYVOICE_FAILURE_THRESHOLD: int = Field(default=3, ge=1, le=20)
COSYVOICE_COOLDOWN_SECONDS: float = Field(default=30, ge=1, le=600)
COSYVOICE_MODEL_REVISION: str = "Fun-CosyVoice3-0.5B-2512"
```

Create `VOICE_PUBLIC_DIR/cache`, `VOICE_PUBLIC_DIR/fixed`, and `VOICE_SEED_DIR` during settings initialization or app bootstrap without requiring CosyVoice to be running.

- [ ] **Step 4: Implement the local bridge contract**

The bridge must:

- load `AutoModel` once at startup from `COSYVOICE_MODEL_DIR`;
- reject requests without the configured bearer-equivalent `X-Voice-Bridge-Token`;
- accept `tts_text`, `instruct_text`, and a synthetic `prompt_wav` upload;
- call `inference_instruct2(..., stream=False)`;
- concatenate returned tensors;
- save a valid WAV into `io.BytesIO` with `torchaudio.save`;
- return `audio/wav`;
- never write uploaded prompt files outside a temporary directory;
- reject text longer than 500 characters.

Use this request surface:

```python
@app.post("/v1/synthesize")
async def synthesize(
    request: Request,
    tts_text: str = Form(min_length=1, max_length=500),
    instruct_text: str = Form(min_length=1, max_length=1000),
    prompt_wav: UploadFile = File(),
) -> Response:
    require_bridge_token(request)
    prompt_bytes = await prompt_wav.read()
    prompt = load_wav(io.BytesIO(prompt_bytes), 16000)
    chunks = list(
        model.inference_instruct2(
            tts_text,
            instruct_text,
            prompt,
            stream=False,
        )
    )
    speech = torch.cat([chunk["tts_speech"] for chunk in chunks], dim=1)
    output = io.BytesIO()
    torchaudio.save(output, speech, model.sample_rate, format="wav")
    return Response(output.getvalue(), media_type="audio/wav")
```

- [ ] **Step 5: Implement the pinned setup script**

The PowerShell script must:

1. run `uv python install 3.10`;
2. clone `https://github.com/QwenAudio/CosyVoice.git` into `.local/cosyvoice`;
3. fetch and detach-checkout `074ca6dc9e80a2f424f1f74b48bdd7d3fea531cc`;
4. initialize `third_party/Matcha-TTS`;
5. create `.local/cosyvoice/.venv` with Python 3.10;
6. install the pinned repository requirements;
7. download `FunAudioLLM/Fun-CosyVoice3-0.5B-2512` into `.local/cosyvoice/pretrained_models/Fun-CosyVoice3-0.5B`;
8. print the exact bridge start command using `tools/cosyvoice_bridge/app.py`;
9. never add model weights or the `.local` directory to Git.

- [ ] **Step 6: Implement `CosyVoiceHttpProvider`**

Use a SHA-256 cache payload containing:

```python
{
    "text": request.text.strip(),
    "profile_id": request.profile.id,
    "profile_version": request.profile.version,
    "emotion": request.emotion,
    "intensity": request.intensity,
    "instruction": request.profile.provider.cosyvoice_instruction,
    "seed": request.profile.provider.cosyvoice_seed,
    "model_revision": self.model_revision,
}
```

Write returned WAV bytes through `NamedTemporaryFile` and atomic `replace`, using one async lock per cache key and a semaphore sized by `VOICE_GENERATION_MAX_CONCURRENCY`. After a successful atomic write, run deterministic LRU cleanup by access time until both `VOICE_CACHE_MAX_FILES` and `VOICE_CACHE_MAX_BYTES` are satisfied. Touch cache hits, exclude in-flight keys from eviction, and never scan or delete `VOICE_PUBLIC_DIR/fixed`.

Runtime provider results always set `cues=()`; only approved fixed assets carry reviewed phrase timing.

- [ ] **Step 7: Run provider and settings tests**

Run:

```powershell
python -m pytest backend/tests/integrations/test_cosyvoice.py backend/tests/test_config.py -q
```

Expected: PASS without a live CosyVoice process.

- [ ] **Step 8: Commit**

```powershell
git add tools/cosyvoice_bridge scripts/voice/setup_cosyvoice.ps1 backend/integrations/cosyvoice.py backend/config.py backend/tests/integrations/test_cosyvoice.py backend/tests/test_config.py .gitignore
git commit -m "feat: add pinned cosyvoice bridge"
```

---

### Task 4: Voice Orchestration, Circuit Breaker, and API

**Files:**
- Create: `backend/application/voice_service.py`
- Create: `backend/api/voice.py`
- Modify: `backend/application/__init__.py`
- Modify: `backend/api/__init__.py`
- Modify: `backend/main.py`
- Modify: `frontend/vite.config.ts`
- Modify: `frontend/nginx.conf`
- Test: `backend/tests/application/test_voice_service.py`
- Test: `backend/tests/api/test_voice_api.py`

**Interfaces:**
- Consumes: `ContentRegistry`, `CosyVoiceHttpProvider`, `EdgeVoiceProvider`, `VoiceSynthesisRequest`.
- Produces: `VoiceService.speak_npc(...)`, `VoiceService.get_fixed_line(...)`, `POST /api/voice/speak`, and `GET /api/voice/lines/{line_id}`.

- [ ] **Step 1: Write failing orchestration tests**

```python
@pytest.mark.asyncio
async def test_voice_service_falls_back_to_edge_without_blocking_text() -> None:
    primary = FailingProvider(VoiceProviderTimeout("timeout"))
    fallback = SuccessfulProvider(provider="edge", url="/tts/fallback.mp3")
    service = VoiceService(registry, primary=primary, fallback=fallback)

    result = await service.speak_npc(
        npc_id="chen_shouyi_young",
        text="额守着这方幕布。",
        emotion="warm",
        intensity=0.5,
    )

    assert result.provider == "edge"
    assert result.degraded is True


@pytest.mark.asyncio
async def test_all_provider_failures_return_stable_silent_result() -> None:
    service = VoiceService(
        registry,
        primary=FailingProvider(RuntimeError("primary")),
        fallback=FailingProvider(RuntimeError("fallback")),
    )

    result = await service.speak_npc(
        npc_id="chen_shouyi_young",
        text="文字仍然继续。",
        emotion="neutral",
        intensity=0.2,
    )

    assert result.provider == "silent"
    assert result.url is None
    assert result.degraded is True
```

Add tests proving:

- an approved fixed asset wins over providers;
- an unapproved asset is ignored;
- three primary failures open the circuit;
- the primary is retried after the configured cooldown;
- unknown NPC/profile/line errors expose stable domain codes.

- [ ] **Step 2: Write failing API tests**

```python
def test_voice_api_returns_provider_neutral_response(monkeypatch) -> None:
    monkeypatch.setattr(voice_api, "voice_service", SuccessfulVoiceService())

    response = TestClient(app).post(
        "/api/voice/speak",
        json={
            "text": "戏要开场了。",
            "npc_id": "chen_shouyi_young",
            "emotion": "warm",
            "intensity": 0.4,
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "url": "/voice/cache/generated.wav",
        "provider": "cosyvoice",
        "cached": False,
        "media_type": "audio/wav",
        "duration_ms": None,
        "line_id": None,
        "cues": [],
        "degraded": False,
    }
```

- [ ] **Step 3: Run tests and verify RED**

Run:

```powershell
python -m pytest backend/tests/application/test_voice_service.py backend/tests/api/test_voice_api.py -q
```

Expected: FAIL because the service and API do not exist.

- [ ] **Step 4: Implement the service contract**

```python
async def speak_npc(
    self,
    *,
    npc_id: str,
    text: str,
    emotion: str,
    intensity: float,
) -> VoiceSynthesisResult:
    npc = self.registry.get_npc(npc_id)
    profile = self.registry.get_voice_profile(npc.voice_profile_id)
    request = VoiceSynthesisRequest(
        text=text.strip(),
        profile=profile,
        emotion=emotion,
        intensity=intensity,
        line_id=None,
    )
    if self.primary is not None and self.circuit.allows_request():
        try:
            result = await self.primary.synthesize(request)
            self.circuit.record_success()
            return result
        except Exception:
            self.circuit.record_failure()
    if self.fallback is not None:
        try:
            return await self.fallback.synthesize(request)
        except Exception:
            pass
    return VoiceSynthesisResult(
        url=None,
        provider="silent",
        cache_hit=False,
        media_type=None,
        duration_ms=None,
        line_id=None,
        cues=(),
        degraded=True,
    )
```

`get_fixed_line(line_id)` must return an approved manifest asset as `provider="fixed"`, a `/voice/{filename}` URL, and the asset's cue tuple. If no approved asset exists, it must return the line metadata with `url=None` and `cues=()`, allowing the frontend to remain silent rather than generating an unreviewed “fixed” performance.

- [ ] **Step 5: Add API schemas and stable error mapping**

`POST /api/voice/speak` accepts:

```python
class VoiceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str = Field(min_length=1, max_length=500)
    npc_id: str = Field(min_length=1, max_length=100)
    emotion: Literal["neutral", "warm", "guarded", "sad", "hopeful"] = "neutral"
    intensity: float = Field(default=0.5, ge=0, le=1)
```

`GET /api/voice/lines/{line_id}` returns the provider-neutral response. Map `VOICE_PROFILE_INVALID` and `VOICE_LINE_INVALID` to 404, and provider failures to a 200 silent result rather than an exception.

- [ ] **Step 6: Register `/voice` and same-origin proxies**

- Mount `settings.VOICE_PUBLIC_DIR` at `/voice`.
- Add `/voice` to the Vite proxy pointing to `http://127.0.0.1:8000`.
- Add an Nginx `/voice/` proxy with bounded caching and stale-on-error behavior.
- Leave `/tts/` in place for backward compatibility.

- [ ] **Step 7: Run voice service/API tests and legacy TTS tests**

Run:

```powershell
python -m pytest backend/tests/application/test_voice_service.py backend/tests/api/test_voice_api.py backend/tests/api/test_tts.py -q
```

Expected: PASS.

- [ ] **Step 8: Commit**

```powershell
git add backend/application backend/api backend/main.py backend/tests/application/test_voice_service.py backend/tests/api/test_voice_api.py frontend/vite.config.ts frontend/nginx.conf
git commit -m "feat: orchestrate voice providers"
```

---

### Task 5: Pure-AI Seed Casting and Fixed-Asset Pipeline

**Files:**
- Create: `scripts/voice/generate_ai_seeds.py`
- Create: `scripts/voice/generate_fixed_assets.py`
- Create: `scripts/voice/validate_voice_assets.py`
- Create: `backend/tests/test_voice_asset_pipeline.py`
- Create: `.gitattributes`
- Modify: `.gitignore`
- Modify after approval: `backend/data/voice_assets.json`
- Add after approval: `backend/data/voice_seeds/*.wav`
- Add after approval: `backend/data/voice_public/fixed/*.opus`

**Interfaces:**
- Consumes: canonical voice profiles/lines, Edge synthetic voice generator, running CosyVoice bridge, FFmpeg.
- Produces: traceable synthetic seed WAVs, approved 1972 Opus assets, and deterministic `voice_assets.json`.

- [ ] **Step 1: Write failing deterministic-pipeline tests**

```python
def test_manifest_entry_contains_reproducibility_fields(tmp_path: Path) -> None:
    canonical_text = "戏要开场了。"
    entry = build_manifest_entry(
        line_id="scene_1972.transition_in",
        canonical_text=canonical_text,
        audio_path=write_wav(tmp_path / "line.wav"),
        generator="cosyvoice3",
        generator_revision="074ca6dc9e80a2f424f1f74b48bdd7d3fea531cc",
        profile_version=1,
        postprocess_version=1,
        approved=True,
    )

    assert entry["id"] == "scene_1972.transition_in"
    assert entry["sha256"] == hashlib.sha256((tmp_path / "line.wav").read_bytes()).hexdigest()
    assert entry["text_sha256"] == hashlib.sha256(canonical_text.encode("utf-8")).hexdigest()
    assert entry["duration_ms"] > 0
    assert entry["approved"] is True


def test_seed_provenance_rejects_human_or_unknown_sources() -> None:
    with pytest.raises(ValueError, match="synthetic seed provenance"):
        validate_seed_provenance("human_recording")
```

Add tests for:

- missing fixed asset;
- mismatched SHA-256;
- unapproved asset in runtime manifest;
- line/profile version mismatch;
- duplicate filename or line ID;
- non-mono output;
- output sample rate other than 48 kHz;
- cue start/end values that overlap, regress, exceed the measured duration, or are not strictly positive spans;
- cue text whose ordered concatenation differs from both the line's `subtitle_segments` and canonical `text`;
- integrated loudness outside `-19..-17 LUFS` or true peak above `-1 dBTP`.

- [ ] **Step 2: Run tests and verify RED**

Run:

```powershell
python -m pytest backend/tests/test_voice_asset_pipeline.py -q
```

Expected: FAIL because the scripts do not exist.

- [ ] **Step 3: Implement synthetic seed generation**

Generate only these five source seeds:

```text
chen_shouyi-base.wav <- zh-CN-YunxiNeural
xiaoyu-base.wav <- zh-CN-XiaoyiNeural
stranger-1990.wav <- zh-CN-YunjianNeural
journalist-2050.wav <- zh-CN-XiaoxiaoNeural
memory-narrator.wav <- zh-CN-YunyangNeural
```

Use this neutral source text for every seed so timbre comparisons are not biased by content:

```text
光落在旧幕布上，风从巷口吹来，记忆里的故事正要开始。
```

The script must:

- call the existing Edge `TtsService`;
- convert MP3 to mono 16 kHz PCM WAV with FFmpeg for CosyVoice prompts;
- write a provenance JSON next to each candidate;
- reject any input file supplied by the operator;
- generate exactly three parameter variants per base seed: A `rate=+0%, pitch=+0Hz`; B `rate=-5%, pitch=-3Hz`; C `rate=+5%, pitch=+3Hz`;
- place candidates in `.codex-run/voice-casting`, not in the shipping asset directory.

For every candidate, generate non-shipping CosyVoice audition clips for these exact delivery checks:

```text
neutral: 戏要开场了，你慢些听。
warm: 你回来就好，屋里一直给你留着灯。
guarded: 这件事，额现在还不能告诉你。
sad: 有些人走远了，声音却还留在这里。
hopeful: 只要还有人记得，故事就不会断。
```

Also render `光落在旧幕布上，故事还在往前走。` once for each Chen Shouyi age profile and each Xiaoyu age profile, so the same-line age-continuity comparison is reviewable before a seed is approved.

- [ ] **Step 4: Implement fixed-line generation and post-processing**

For each 1972 `pre_generated` line:

1. call the CosyVoice bridge with the approved synthetic seed;
2. write the raw WAV to `.codex-run/voice-renders/raw`;
3. normalize to `-18 LUFS`, `-1 dBTP`, mono, 48 kHz;
4. encode an Opus file at 80 kbit/s;
5. measure duration;
6. split the canonical `subtitle_segments` into initial sentence/phrase cues, allocating time proportionally by visible character count;
7. compute audio SHA-256 and canonical UTF-8 text SHA-256;
8. record measured integrated LUFS and true peak;
9. write a candidate manifest with `id` equal to the line ID, `cues`, and `approved=false`.

Use this FFmpeg filter:

```text
loudnorm=I=-18:TP=-1:LRA=7
```

- [ ] **Step 5: Implement validation**

`validate_voice_assets.py` must exit non-zero for every invalid condition covered in Step 1 and print one line per rejected asset with `line_id`, stable reason code, and path. Cue validation is exact: cues are monotonic, non-overlapping, inside the measured audio duration, and `''.join(cue.text for cue in cues) == ''.join(line.subtitle_segments) == line.text`.

- [ ] **Step 6: Run the unit tests**

Run:

```powershell
python -m pytest backend/tests/test_voice_asset_pipeline.py -q
```

Expected: PASS without contacting Edge or CosyVoice.

- [ ] **Step 7: Generate and audition candidates**

Run:

```powershell
python scripts/voice/generate_ai_seeds.py
python scripts/voice/generate_fixed_assets.py --scene scene_1972 --candidate-mode
```

Listen to all candidates and record one selected candidate per base lineage in `.codex-run/voice-casting/selection.json`. Reject any candidate that changes speaker identity across the five required emotion samples. During the same review, adjust the automatically proposed phrase-level cue boundaries to match audible phrase starts and endings; keep breath and performance directions out of cue text.

- [ ] **Step 8: Promote only approved assets**

Copy selected seed WAVs to `backend/data/voice_seeds`, selected fixed Opus files to `backend/data/voice_public/fixed`, set their manifest entries to `approved=true`, and run:

```powershell
python scripts/voice/validate_voice_assets.py
```

Expected: `Voice assets valid: 7 approved lines, 5 synthetic seeds, 0 stale files.`

- [ ] **Step 9: Configure Git LFS and commit**

Add:

```gitattributes
backend/data/voice_seeds/*.wav filter=lfs diff=lfs merge=lfs -text
backend/data/voice_public/fixed/*.opus filter=lfs diff=lfs merge=lfs -text
backend/data/voice_public/fixed/*.mp3 filter=lfs diff=lfs merge=lfs -text
```

Then commit:

```powershell
git add .gitattributes .gitignore scripts/voice backend/tests/test_voice_asset_pipeline.py backend/data/voice_assets.json backend/data/voice_seeds backend/data/voice_public/fixed
git commit -m "feat: add approved first act voice assets"
```

---

### Task 6: Frontend Voice API and Playback Queue

**Files:**
- Modify: `frontend/src/types/game.ts`
- Modify: `frontend/src/api/index.ts`
- Create: `frontend/src/composables/useVoicePlayback.ts`
- Test: `frontend/src/__tests__/voicePlayback.test.ts`
- Test: `frontend/src/__tests__/api.test.ts`

**Interfaces:**
- Consumes: `POST /api/voice/speak`, `GET /api/voice/lines/{line_id}`, browser `HTMLAudioElement`.
- Produces: `VoiceResponse`, `requestNpcVoice`, `getFixedVoiceLine`, and a queue exposing `play`, `playResponse`, `preloadFixedLine`, `stop`, `pause`, `resume`, `replay`, and `resumeAfterUserGesture`.

- [ ] **Step 1: Add failing API contract tests**

```typescript
it('requests provider-neutral NPC voice', async () => {
  mock.onPost('/voice/speak').reply(200, {
    url: '/voice/cache/generated.wav',
    provider: 'cosyvoice',
    cached: false,
    media_type: 'audio/wav',
    duration_ms: null,
    line_id: null,
    cues: [],
    degraded: false,
  })

  const response = await requestNpcVoice('台词', 'chen_shouyi_young', 'warm', 0.4)

  expect(response.data.provider).toBe('cosyvoice')
  expect(mock.history.post[0].data).toBe(
    JSON.stringify({
      text: '台词',
      npc_id: 'chen_shouyi_young',
      emotion: 'warm',
      intensity: 0.4,
    }),
  )
})
```

- [ ] **Step 2: Add failing playback tests with an injected fake audio factory**

```typescript
it('higher priority voice stops lower priority voice', async () => {
  const first = fakeAudio()
  const second = fakeAudio()
  const queue = createVoicePlayback({
    audioFactory: sequenceAudioFactory(first, second),
  })

  await queue.play({ url: '/voice/narration.opus', priority: 'narration', lineId: 'n1', cues: [] })
  await queue.play({ url: '/voice/critical.opus', priority: 'critical', lineId: 'c1', cues: [] })

  expect(first.pause).toHaveBeenCalledOnce()
  expect(second.play).toHaveBeenCalledOnce()
  expect(queue.currentLineId.value).toBe('c1')
})
```

Also test pause/resume, replay, same-priority replacement, lower-priority rejection, media error cleanup, unmount cleanup, silent responses, cue changes driven by `timeupdate`, and fixed-line preload without playback. Simulate `audio.play()` rejecting with `NotAllowedError`; assert text flow is unaffected, `waitingForUserGesture` becomes true, and `resumeAfterUserGesture()` retries the retained request exactly once.

- [ ] **Step 3: Run the tests and verify RED**

Run:

```powershell
npm test -- --run src/__tests__/voicePlayback.test.ts src/__tests__/api.test.ts
```

Expected: FAIL because the types, API calls, and queue do not exist.

- [ ] **Step 4: Add exact frontend types**

```typescript
export type VoiceProvider = 'fixed' | 'cosyvoice' | 'edge' | 'silent'
export type VoicePriority = 'ending' | 'critical' | 'dialogue' | 'narration' | 'system'

export interface VoiceCue {
  start_ms: number
  end_ms: number
  text: string
}

export interface VoiceResponse {
  url: string | null
  provider: VoiceProvider
  cached: boolean
  media_type: string | null
  duration_ms: number | null
  line_id: string | null
  cues: VoiceCue[]
  degraded: boolean
}

export interface VoicePlaybackRequest {
  url: string
  priority: VoicePriority
  lineId: string | null
  cues: VoiceCue[]
}
```

Add optional voice references to `Scene`, `NpcSummary`, `SceneFragment`, `Hypothesis`, and `EndingContent`.

- [ ] **Step 5: Add API functions**

```typescript
export const requestNpcVoice = (
  text: string,
  npcId: string,
  emotion: string,
  intensity: number,
) =>
  api.post<VoiceResponse>('/voice/speak', {
    text,
    npc_id: npcId,
    emotion,
    intensity,
  })

export const getFixedVoiceLine = (lineId: string) =>
  api.get<VoiceResponse>(`/voice/lines/${encodeURIComponent(lineId)}`)
```

- [ ] **Step 6: Implement the queue**

Use this priority table:

```typescript
const priorityRank: Record<VoicePriority, number> = {
  system: 1,
  narration: 2,
  dialogue: 3,
  critical: 4,
  ending: 5,
}
```

The queue must expose reactive `isSpeaking`, `isPaused`, `currentLineId`, `activeCue`, `waitingForUserGesture`, `lastRequest`, and `lastError`, and must never throw an unhandled audio-play rejection.

- `playResponse(response, priority)` translates a provider-neutral response into `play(...)`; `url=null` is a no-op.
- `preloadFixedLine(lineId)` fetches the fixed response once, caches the promise by line ID, creates an audio element with `preload="auto"`, and never starts playback.
- `timeupdate` selects the phrase-level cue whose half-open interval contains `currentTime * 1000`; no cue yields `activeCue=null`.
- On `NotAllowedError`, retain the pending request and set `waitingForUserGesture=true`; `resumeAfterUserGesture()` retries it once from a real pointer/keyboard handler and clears the flag on success.
- Other play or decode errors clear the current audio and queue state without affecting displayed text or game input.

- [ ] **Step 7: Run frontend tests**

Run:

```powershell
npm test -- --run src/__tests__/voicePlayback.test.ts src/__tests__/api.test.ts
```

Expected: PASS.

- [ ] **Step 8: Commit**

```powershell
git add frontend/src/types/game.ts frontend/src/api/index.ts frontend/src/composables/useVoicePlayback.ts frontend/src/__tests__/voicePlayback.test.ts frontend/src/__tests__/api.test.ts
git commit -m "feat: add frontend voice playback contract"
```

---

### Task 7: Audio Mixer Refactor and Compatibility Facade

**Files:**
- Create: `frontend/src/audio/mixer.ts`
- Create: `frontend/src/composables/useMusicBus.ts`
- Create: `frontend/src/composables/useSfxBus.ts`
- Modify: `frontend/src/composables/useVoicePlayback.ts`
- Modify: `frontend/src/composables/useAudio.ts`
- Test: `frontend/src/__tests__/audioMixer.test.ts`
- Test: `frontend/src/__tests__/dialogueFlow.test.ts`

**Interfaces:**
- Consumes: existing BGM/SFX implementation and `useVoicePlayback`.
- Produces: `setVoiceDucking(active)`, independent music/SFX/voice volumes, and backward-compatible `useAudio()` exports.

- [ ] **Step 1: Write failing mixer tests**

```typescript
it('ducks music by eight decibels while preserving ambience at minus three', () => {
  const mixer = createAudioMixer({ storage: memoryStorage() })

  mixer.setVoiceDucking(true)

  expect(mixer.musicDuckDb.value).toBe(-8)
  expect(mixer.ambienceDuckDb.value).toBe(-3)
})

it('restores music after six hundred milliseconds', () => {
  vi.useFakeTimers()
  const mixer = createAudioMixer({ storage: memoryStorage() })
  mixer.setVoiceDucking(true)
  mixer.setVoiceDucking(false)

  vi.advanceTimersByTime(599)
  expect(mixer.musicDuckDb.value).toBe(-8)
  vi.advanceTimersByTime(1)
  expect(mixer.musicDuckDb.value).toBe(0)
})
```

Also test clamped and persisted music/SFX/voice volumes, invalid stored values, and full mute.

- [ ] **Step 2: Run tests and verify RED**

Run:

```powershell
npm test -- --run src/__tests__/audioMixer.test.ts src/__tests__/dialogueFlow.test.ts
```

Expected: FAIL because the mixer and focused buses do not exist.

- [ ] **Step 3: Implement the shared mixer**

Persist:

```typescript
export interface AudioPreferences {
  muted: boolean
  musicVolume: number
  sfxVolume: number
  voiceVolume: number
}
```

Use storage key `memory-healer.audio.v2`. Clamp every volume to `[0, 1]`. Treat invalid JSON as `{ muted: false, musicVolume: 0.35, sfxVolume: 0.5, voiceVolume: 0.85 }`.

- [ ] **Step 4: Extract focused buses**

- Move BGM and ambience creation, transition, and cleanup into `useMusicBus.ts`.
- Move synthesized interaction effects into `useSfxBus.ts`.
- Apply `musicDuckDb` and `ambienceDuckDb` to gain targets.
- Apply `voiceVolume` to every `HTMLAudioElement` created by `useVoicePlayback`.
- Call `setVoiceDucking(true)` after voice playback begins and `setVoiceDucking(false)` on ended, skipped, failed, or stopped.

- [ ] **Step 5: Keep `useAudio()` as a compatibility facade**

```typescript
export function useAudio() {
  return {
    ...useMusicBus(),
    ...useSfxBus(),
    ...useVoicePlayback(),
    ...useAudioMixer(),
  }
}
```

Remove the old direct `/api/tts/speak` fetch from `useAudio.ts`.

- [ ] **Step 6: Run audio and existing frontend tests**

Run:

```powershell
npm test -- --run src/__tests__/audioMixer.test.ts src/__tests__/dialogueFlow.test.ts
npm test
```

Expected: all frontend tests pass.

- [ ] **Step 7: Commit**

```powershell
git add frontend/src/audio frontend/src/composables frontend/src/__tests__/audioMixer.test.ts frontend/src/__tests__/dialogueFlow.test.ts
git commit -m "refactor: split cinematic audio buses"
```

---

### Task 8: Integrate Dynamic Dialogue and the 1972 Fixed-Voice Pilot

**Files:**
- Modify: `backend/application/game_service.py`
- Modify: `frontend/src/components/ChatPanel.vue`
- Create: `frontend/src/components/VoiceSubtitle.vue`
- Modify: `frontend/src/views/Game.vue`
- Modify: `frontend/src/views/Ending.vue`
- Modify: `frontend/src/composables/useScene.ts`
- Modify: `frontend/src/types/game.ts`
- Test: `backend/tests/application/test_game_service.py`
- Test: `frontend/src/__tests__/sceneFlow.test.ts`
- Test: `frontend/src/__tests__/dialogueFlow.test.ts`
- Test: `frontend/src/__tests__/voiceIntegration.test.ts`

**Interfaces:**
- Consumes: canonical voice references and `useVoicePlayback`.
- Produces: fixed voice references in `SceneView`, automatic first-act voice events, phrase-level cinematic subtitles, and dynamic NPC voice playback.

- [ ] **Step 1: Add failing backend scene-view tests**

```python
def test_scene_view_exposes_first_act_voice_references(registry) -> None:
    service = GameService(registry)
    view = service.get_scene_view(service.create_game())

    assert view.scene.transition_in_voice_line_id == "scene_1972.transition_in"
    chen = next(npc for npc in view.npcs if npc.id == "chen_shouyi_young")
    assert chen.initial_voice_line_id == "npc.chen_shouyi_young.intro"
    knife = next(fragment for fragment in view.fragments if fragment.id == "fragment_grandpa_knife")
    assert knife.memory_voice_line_id == "fragment_grandpa_knife.memory"
```

- [ ] **Step 2: Add failing frontend integration tests**

Assert:

- loading 1972 requests `scene_1972.transition_in`;
- selecting Chen requests `npc.chen_shouyi_young.intro`;
- collecting the knife requests `fragment_grandpa_knife.memory`;
- confirming the hypothesis requests `hypothesis_1972_legacy.resolution` with `critical` priority;
- submitting a scene-changing choice stops voice before transition;
- NPC AI reply calls `requestNpcVoice(reply, npc.id, npc_mood, intensity)`;
- a silent response leaves text visible and the input enabled;
- closing the dialogue stops active dialogue voice;
- `Ending.vue` stops voice on unmount;
- a real pointer or keyboard event retries an autoplay-blocked pending line once;
- an active fixed-line cue renders exactly once in the cinematic subtitle layer and disappears between cues.

- [ ] **Step 3: Run tests and verify RED**

Run:

```powershell
python -m pytest backend/tests/application/test_game_service.py -q
npm test -- --run src/__tests__/sceneFlow.test.ts src/__tests__/dialogueFlow.test.ts src/__tests__/voiceIntegration.test.ts
```

Expected: FAIL because voice references and playback triggers are not wired.

- [ ] **Step 4: Expose canonical voice references**

Add optional line IDs to the serialized scene, NPC summary, fragment, hypothesis, and ending response models. Do not duplicate fixed asset URLs in `SceneView`; the frontend resolves them through `GET /api/voice/lines/{line_id}`.

- [ ] **Step 5: Replace ChatPanel direct TTS**

```typescript
const voice = useVoicePlayback()

const result = await sendDialogue(npc.id, msg)
emit('dialogueComplete', result)
scrollToBottom()
void requestNpcVoice(result.reply, npc.id, result.npc_mood, 0.5)
  .then((response) => voice.playResponse(response.data, 'dialogue'))
  .catch(() => undefined)
```

Do not await the voice request before rendering `result.reply`. Start the request after the authoritative dialogue response has already updated the game state and chat history.

- [ ] **Step 6: Wire fixed-line events in `Game.vue`**

Use one helper:

```typescript
async function playFixedVoice(lineId: string | null | undefined, priority: VoicePriority) {
  if (!lineId) return
  const response = await getFixedVoiceLine(lineId)
  await voice.playResponse(response.data, priority)
}
```

Call it only at these state boundaries:

- initial 1972 scene ready: `narration`;
- NPC selection: `dialogue`;
- fragment popup opened: `narration`;
- hypothesis confirmed: `critical`;
- before scene transition: stop current voice.

Call `preloadFixedLine(lineId)` only when the next fixed line is deterministic from the current state; preloading must not play audio or speculate across unresolved player choices. Render `voice.activeCue.value?.text` through `VoiceSubtitle.vue` in the existing safe cinematic caption zone, never on top of a face, the memory reasoning panel, or a choice target. Hide it when there is no active cue; dynamic chat text remains in `ChatPanel` and is never duplicated as an overlay.

At the game/ending route root, connect capture-phase `pointerdown` and `keydown` handlers to `resumeAfterUserGesture()` only while `waitingForUserGesture` is true. Remove those handlers on unmount and after the retained line succeeds or is superseded.

- [ ] **Step 7: Run focused integration tests**

Run:

```powershell
python -m pytest backend/tests/application/test_game_service.py -q
npm test -- --run src/__tests__/sceneFlow.test.ts src/__tests__/dialogueFlow.test.ts src/__tests__/voiceIntegration.test.ts
```

Expected: PASS.

- [ ] **Step 8: Commit**

```powershell
git add backend/application/game_service.py backend/tests/application/test_game_service.py frontend/src/components/ChatPanel.vue frontend/src/components/VoiceSubtitle.vue frontend/src/views/Game.vue frontend/src/views/Ending.vue frontend/src/composables/useScene.ts frontend/src/types/game.ts frontend/src/__tests__
git commit -m "feat: connect first act voice playback"
```

---

### Task 9: Cinematic Voice Controls

**Files:**
- Create: `frontend/src/components/VoiceControls.vue`
- Modify: `frontend/src/views/Game.vue`
- Modify: `frontend/src/views/Ending.vue`
- Modify: `frontend/src/styles/cinematic-game.css`
- Test: `frontend/src/__tests__/voiceControls.test.ts`

**Interfaces:**
- Consumes: `useVoicePlayback` and `useAudioMixer`.
- Produces: accessible pause/resume, replay, skip, voice volume, and mute controls.

- [ ] **Step 1: Write failing component tests**

```typescript
it('exposes pause, replay, skip, and voice volume controls', async () => {
  const wrapper = mount(VoiceControls, {
    props: {
      isSpeaking: true,
      isPaused: false,
      voiceVolume: 0.85,
      hasReplay: true,
    },
  })

  expect(wrapper.get('[aria-label="暂停对白"]').exists()).toBe(true)
  expect(wrapper.get('[aria-label="重播上一句"]').exists()).toBe(true)
  expect(wrapper.get('[aria-label="跳过当前对白"]').exists()).toBe(true)
  expect(wrapper.get('[aria-label="对白音量"]').attributes('type')).toBe('range')
})
```

Also test keyboard activation, disabled replay before any line, persisted volume update, and pause label changing to `继续对白`.

- [ ] **Step 2: Run tests and verify RED**

Run:

```powershell
npm test -- --run src/__tests__/voiceControls.test.ts
```

Expected: FAIL because the component does not exist.

- [ ] **Step 3: Implement the component**

Requirements:

- use native `<button>` and `<input type="range">`;
- show compact text labels, not orb icons;
- use the existing black/warm-gold cinematic tokens;
- preserve a 44 px touch target on narrow screens;
- show playback state through text and border emphasis;
- collapse secondary controls behind the existing `声` control on mobile;
- never cover the memory reasoning panel or the active NPC face.

- [ ] **Step 4: Integrate Game and Ending**

- Keep the existing global mute behavior.
- Add voice-only volume and playback controls.
- On ending entry, set voice priority to `ending` when an approved ending line becomes available.
- On restart/home navigation, stop voice and clear the replay buffer.

- [ ] **Step 5: Run component, lint, and build checks**

Run:

```powershell
npm test -- --run src/__tests__/voiceControls.test.ts
npm run lint
npm run build
```

Expected: PASS.

- [ ] **Step 6: Commit**

```powershell
git add frontend/src/components/VoiceControls.vue frontend/src/views/Game.vue frontend/src/views/Ending.vue frontend/src/styles/cinematic-game.css frontend/src/__tests__/voiceControls.test.ts
git commit -m "feat: add cinematic voice controls"
```

---

### Task 10: Age-Correct 2089 Xiaoyu Presentation

**Files:**
- Create: `frontend/src/assets/cinematic/xiaoyu-2089-aged-solid.webp`
- Modify: `frontend/src/stage/presentation.ts`
- Modify: `frontend/src/components/CinematicStage.vue`
- Modify: `frontend/src/__tests__/scenePresentation.test.ts`
- Modify: `frontend/src/__tests__/cinematicStageFallback.test.ts`
- Modify: `backend/tests/test_cinematic_assets.py`

**Interfaces:**
- Consumes: approved 2050 Xiaoyu portrait and existing 2089 scene composition.
- Produces: an 87-year-old physical Xiaoyu portrait that remains recognizably the same person.

- [ ] **Step 1: Write failing presentation tests**

```typescript
it('presents 2089 Xiaoyu as an aged physical character', () => {
  const scene = getScenePresentation('scene_2089')

  expect(scene?.portraits.xiaoyu).toContain('xiaoyu-2089-aged-solid')
  expect(resolveCharacterMode('scene_2089', 'xiaoyu')).toBe('solid')
})
```

Add a backend asset test asserting the new file exists, is WebP, exceeds the minimum accepted dimensions, and is not byte-identical to the 2050 portrait.

- [ ] **Step 2: Run tests and verify RED**

Run:

```powershell
npm test -- --run src/__tests__/scenePresentation.test.ts src/__tests__/cinematicStageFallback.test.ts
python -m pytest backend/tests/test_cinematic_assets.py -q
```

Expected: FAIL because the aged asset and solid mode do not exist.

- [ ] **Step 3: Generate the portrait with `imagegen`**

Use the 2050 Xiaoyu portrait and current 2089 portrait as references with this exact art direction:

```text
Create a production-ready transparent-background full-body character plate for the cinematic Chinese memory game “拾忆”. The subject is Xiaoyu at age 87 in the year 2089, clearly the same woman as the provided age-48 reference: preserve her facial structure, eyes, and restrained warmth, but age her naturally with silver hair, fine wrinkles, slightly reduced posture, and calm authority. She is a respected memory-technology guardian, not frail or helpless. Wardrobe: understated dark future-Chinese tailoring with subtle archival-gold details, no glowing hologram body, no sci-fi armor. Lighting must match the existing cool 2089 laboratory with a warm edge light from memory projections. Photorealistic cinematic realism, grounded human presence, full body, clean silhouette, transparent background, no text, no props covering the face.
```

Resize/crop to the same character-plate slot as the existing presentation assets and export lossless WebP.

- [ ] **Step 4: Replace projection semantics**

- Import `xiaoyu-2089-aged-solid.webp` in `presentation.ts`.
- Return `solid` for 2089 Xiaoyu in `CinematicStage.vue`.
- Remove only the projection-specific visual treatment for this character; preserve the laboratory projection effects belonging to the scene.

- [ ] **Step 5: Run asset and presentation tests**

Run:

```powershell
npm test -- --run src/__tests__/scenePresentation.test.ts src/__tests__/cinematicStageFallback.test.ts
python -m pytest backend/tests/test_cinematic_assets.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```powershell
git add frontend/src/assets/cinematic/xiaoyu-2089-aged-solid.webp frontend/src/stage/presentation.ts frontend/src/components/CinematicStage.vue frontend/src/__tests__/scenePresentation.test.ts frontend/src/__tests__/cinematicStageFallback.test.ts backend/tests/test_cinematic_assets.py
git commit -m "fix: age xiaoyu consistently in 2089"
```

---

### Task 11: Documentation, Packaging, and Observability

**Files:**
- Modify: `README.md`
- Modify: `CHANGELOG.md`
- Modify: `.env.example`
- Modify: `docker-compose.yml`
- Modify: `scripts/validate_content.py`
- Create: `docs/voice-production.md`
- Test: `backend/tests/test_config.py`
- Test: `backend/tests/test_voice_asset_pipeline.py`

**Interfaces:**
- Consumes: completed voice platform and generation tools.
- Produces: reproducible setup, deployment-safe defaults, production metrics, and operator runbook.

- [ ] **Step 1: Add failing configuration and validation assertions**

Assert:

- voice directories are outside the TTS cache;
- bridge token is required when CosyVoice is enabled outside test mode;
- `VOICE_PRIMARY_ENABLED=false` boots without CosyVoice;
- Docker Compose preserves voice cache and approved fixed assets separately;
- content validation reports profile/line/asset counts.

- [ ] **Step 2: Run tests and verify RED**

Run:

```powershell
python -m pytest backend/tests/test_config.py backend/tests/test_voice_asset_pipeline.py -q
```

Expected: FAIL until configuration and validation output are updated.

- [ ] **Step 3: Document exact operator flows**

`docs/voice-production.md` must contain runnable commands for:

1. pinned CosyVoice setup;
2. bridge start;
3. health check;
4. synthetic seed candidate generation;
5. first-act fixed candidate generation;
6. asset validation;
7. approved-asset promotion;
8. cache cleanup;
9. complete silent-degradation test.

Include the prohibition on human samples and the requirement to keep seed provenance JSON.

- [ ] **Step 4: Add packaging and runtime defaults**

- `.env.example` keeps `VOICE_PRIMARY_ENABLED=false`.
- `docker-compose.yml` mounts approved voice assets read-only and runtime cache read-write.
- Do not bundle CosyVoice weights in the web/backend image.
- Expose provider, cache-hit, latency, fallback, and silent-degradation metrics through structured logs without logging full player text.

- [ ] **Step 5: Update project documentation**

- README: describe the hybrid system and local optional bridge.
- CHANGELOG `Unreleased`: describe canonical voice content, provider fallback, first-act pilot, voice controls, and 2089 timeline correction.
- `scripts/validate_content.py`: print `voice profiles`, `voice lines`, and `approved voice assets`.

- [ ] **Step 6: Run documentation-adjacent tests and validators**

Run:

```powershell
python -m pytest backend/tests/test_config.py backend/tests/test_voice_asset_pipeline.py -q
python scripts/validate_content.py
git diff --check
```

Expected: PASS with no whitespace errors.

- [ ] **Step 7: Commit**

```powershell
git add README.md CHANGELOG.md .env.example docker-compose.yml scripts/validate_content.py docs/voice-production.md backend/tests/test_config.py backend/tests/test_voice_asset_pipeline.py
git commit -m "docs: add cinematic voice operations"
```

---

### Task 12: Full Verification and Browser Acceptance

**Files:**
- Modify: `design-qa.md`
- Create: `.codex-run/qa/voice-1972-desktop.png`
- Create: `.codex-run/qa/voice-1972-mobile.png`
- Create: `.codex-run/qa/voice-1972-console.txt`
- Create: `.codex-run/qa/voice-1972-playback-notes.md`

**Interfaces:**
- Consumes: complete voice platform and approved 1972 pilot.
- Produces: fresh automated evidence, browser evidence, audio audition notes, and a clean committed tree.

- [ ] **Step 1: Run the complete backend suite**

Run:

```powershell
python -m pytest
```

Expected: all tests pass; existing deprecation warnings may remain but no new warning class is introduced.

- [ ] **Step 2: Run the complete frontend suite, lint, and build**

Run:

```powershell
npm test
npm run lint
npm run build
```

Expected: all tests pass, ESLint exits 0, and Vite production build exits 0.

- [ ] **Step 3: Run content, asset, and whitespace validation**

Run:

```powershell
python scripts/validate_content.py
python scripts/voice/validate_voice_assets.py
git diff --check
git status --short
```

Expected:

- canonical content valid;
- exactly seven approved 1972 fixed voice lines;
- no stale or unapproved shipping voice assets;
- no whitespace errors;
- no generated caches, model weights, or `.local` files staged.

- [ ] **Step 4: Verify the browser flow in the in-app browser**

At desktop 1280 × 720 and mobile 390 × 844:

1. start a new 1972 game;
2. verify transition narration starts without delaying scene text;
3. verify each fixed phrase subtitle appears only during its reviewed cue interval and never covers a face, choice, or memory reasoning panel;
4. pause, resume, replay, change voice volume, and skip;
5. select Chen and hear the approved intro;
6. collect the knife and hear its memory line;
7. collect the second evidence item and confirm the hypothesis;
8. verify critical resolution audio preempts lower-priority narration;
9. start an AI dialogue and confirm text appears before dynamic speech;
10. stop the CosyVoice bridge and confirm Edge fallback;
11. disable both providers and confirm silent play remains fully usable;
12. move to the next scene and confirm no 1972 audio overlaps;
13. inspect 2089 and confirm Xiaoyu is an elderly physical character, recognizably continuous with her 2050 portrait;
14. verify the console contains no warning/error from voice playback.

- [ ] **Step 5: Record audio acceptance**

In `.codex-run/qa/voice-1972-playback-notes.md`, record:

- selected seed candidate IDs;
- first-audio latency for fixed, CosyVoice, Edge fallback, and silent paths;
- whether Chen remains the same person across five emotion samples;
- whether narration remains distinct from Chen;
- headphone and laptop-speaker intelligibility;
- any rejected pronunciation and its regenerated asset hash.

The final line must be either:

```text
final result: passed
```

or:

```text
final result: failed
```

Do not claim completion when the result is failed.

- [ ] **Step 6: Update design QA and commit any final corrections**

Add the voice QA evidence and explicit test gap notes to `design-qa.md`, then run the full verification commands again after every correction.

```powershell
git add design-qa.md
git commit -m "test: record first act voice acceptance"
```

- [ ] **Step 7: Preserve the narrative-production boundary**

Do not generate fixed assets for 1990, 2024, 2050, 2089, or endings in this plan. Open the separate narrative-and-gameplay expansion design next; after its scripts are approved, create a second asset-rollout plan using the same voice platform.
