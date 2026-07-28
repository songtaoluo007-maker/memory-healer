from __future__ import annotations

import hashlib
import json
import math
import struct
import subprocess
import sys
import wave
from collections.abc import Callable
from pathlib import Path

import pytest

import scripts.voice.generate_fixed_assets as fixed_assets
from scripts.voice.generate_fixed_assets import (
    allocate_cues,
    build_generation_plan,
    build_manifest_entry,
    postprocess_audio,
)
from scripts.voice.validate_voice_assets import (
    MediaInfo,
    validate_seed_provenance,
    validate_voice_assets,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
LINE_ID = "scene_1972.transition_in"
LINE_TEXT = "戏要开场了。"
ASSET_BYTES = b"hermetic-opus-fixture"


def write_wav(path: Path, *, duration_ms: int = 100) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    sample_rate = 16_000
    frame_count = sample_rate * duration_ms // 1_000
    with wave.open(str(path), "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(sample_rate)
        audio.writeframes(b"\0\0" * frame_count)
    return path


def write_tone_wav(path: Path, *, duration_ms: int = 1_000) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    sample_rate = 16_000
    frame_count = sample_rate * duration_ms // 1_000
    frames = b"".join(
        struct.pack(
            "<h",
            round(10_000 * math.sin(2 * math.pi * 440 * index / sample_rate)),
        )
        for index in range(frame_count)
    )
    with wave.open(str(path), "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(sample_rate)
        audio.writeframes(frames)
    return path


def test_manifest_entry_contains_edge_reproducibility_fields(
    tmp_path: Path,
) -> None:
    audio_path = write_wav(tmp_path / "line.wav")

    entry = build_manifest_entry(
        line_id=LINE_ID,
        canonical_text=LINE_TEXT,
        audio_path=audio_path,
        generator="edge_tts",
        generator_revision="7.2.8",
        model_id="zh-CN-XiaoxiaoNeural",
        line_version=1,
        profile_version=1,
        postprocess_version=1,
        approved=True,
    )

    assert entry["id"] == LINE_ID
    assert entry["sha256"] == hashlib.sha256(audio_path.read_bytes()).hexdigest()
    assert entry["text_sha256"] == hashlib.sha256(LINE_TEXT.encode("utf-8")).hexdigest()
    assert entry["duration_ms"] > 0
    assert entry["generator"] == "edge_tts"
    assert entry["generator_revision"] == "7.2.8"
    assert entry["model_id"] == "zh-CN-XiaoxiaoNeural"
    assert "model_commit" not in entry
    assert entry["seed_provenance"] == "edge_tts_synthetic"
    assert entry["line_version"] == 1
    assert entry["approved"] is True


def test_seed_provenance_rejects_human_or_unknown_sources() -> None:
    for provenance in ("human_recording", "operator_upload", "unknown"):
        with pytest.raises(ValueError, match="synthetic seed provenance"):
            validate_seed_provenance(provenance)


def test_generation_plan_contains_only_seven_1972_edge_lines() -> None:
    plans = build_generation_plan(REPOSITORY_ROOT, "scene_1972")

    assert {plan.line_id for plan in plans} == {
        "scene_1972.transition_in",
        "scene_1972.transition_out",
        "npc.chen_shouyi_young.intro",
        "fragment_shadow_puppet.memory",
        "fragment_grandpa_knife.memory",
        "fragment_three_kings.memory",
        "hypothesis_1972_legacy.resolution",
    }
    assert len(plans) == 7
    assert {plan.line_id: plan.edge_voice for plan in plans}[
        "npc.chen_shouyi_young.intro"
    ] == "zh-CN-YunxiNeural"
    assert {
        plan.edge_voice
        for plan in plans
        if plan.line_id != "npc.chen_shouyi_young.intro"
    } == {"zh-CN-XiaoxiaoNeural"}


def test_dry_run_never_constructs_edge_service(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fail_if_constructed(*args, **kwargs):
        raise AssertionError("dry-run contacted Edge")

    monkeypatch.setattr(fixed_assets, "TtsService", fail_if_constructed)

    assert (
        fixed_assets.main(
            ["--scene", "scene_1972", "--dry-run"],
            repository_root=REPOSITORY_ROOT,
        )
        == 0
    )
    assert (
        "7 Edge fixed lines planned; no network calls made." in capsys.readouterr().out
    )


@pytest.mark.parametrize(
    "script",
    [
        "scripts/voice/generate_fixed_assets.py",
        "scripts/voice/validate_voice_assets.py",
    ],
)
def test_voice_pipeline_scripts_run_directly_from_repository(script: str) -> None:
    result = subprocess.run(
        [sys.executable, script, "--help"],
        capture_output=True,
        check=False,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    assert result.returncode == 0, result.stderr
    assert "usage:" in result.stdout


def test_phrase_cues_reconstruct_subtitles_and_cover_duration() -> None:
    cues = allocate_cues(("戏要开场了，", "你慢些听。"), 1_001)

    assert cues == [
        {"start_ms": 0, "end_ms": 546, "text": "戏要开场了，"},
        {"start_ms": 546, "end_ms": 1001, "text": "你慢些听。"},
    ]
    assert "".join(cue["text"] for cue in cues) == "戏要开场了，你慢些听。"


def test_postprocess_corrects_opus_true_peak_overshoot(tmp_path: Path) -> None:
    raw_path = tmp_path / "raw.mp3"
    output_path = tmp_path / "fixed.opus"
    raw_path.write_bytes(b"managed-cloud-mp3")
    attenuations: list[float] = []
    measurements = iter(
        [
            MediaInfo(1000, 1, 48_000, "opus", -17.45, -0.82),
            MediaInfo(1000, 1, 48_000, "opus", -17.68, -1.05),
        ]
    )

    def fake_encoder(source: Path, target: Path, attenuation_db: float) -> None:
        assert source == raw_path
        attenuations.append(attenuation_db)
        target.write_bytes(f"opus-{attenuation_db}".encode())

    postprocess_audio(
        raw_path,
        output_path,
        media_inspector=lambda _: next(measurements),
        encoder=fake_encoder,
    )

    assert attenuations == [0.0, 0.23]
    assert output_path.read_bytes() == b"opus-0.23"


def test_postprocess_is_byte_deterministic_for_same_input(tmp_path: Path) -> None:
    raw_path = write_tone_wav(tmp_path / "tone.wav")
    first_path = tmp_path / "first.opus"
    second_path = tmp_path / "second.opus"

    fixed_assets.postprocess_audio(raw_path, first_path)
    fixed_assets.postprocess_audio(raw_path, second_path)

    assert (
        hashlib.sha256(first_path.read_bytes()).digest()
        == hashlib.sha256(second_path.read_bytes()).digest()
    )


PROMOTION_LINE_IDS = (
    "scene_1972.transition_in",
    "scene_1972.transition_out",
    "npc.chen_shouyi_young.intro",
    "fragment_shadow_puppet.memory",
    "fragment_grandpa_knife.memory",
    "fragment_three_kings.memory",
    "hypothesis_1972_legacy.resolution",
)


def promotion_manifest_entry(
    *,
    line_id: str,
    filename: str,
    payload: bytes,
    approved: bool,
) -> dict[str, object]:
    line_text = f"canonical text for {line_id}"
    return {
        "id": line_id,
        "filename": f"fixed/{filename}",
        "media_type": "audio/ogg; codecs=opus",
        "duration_ms": 1200,
        "sha256": hashlib.sha256(payload).hexdigest(),
        "text_sha256": hashlib.sha256(line_text.encode("utf-8")).hexdigest(),
        "integrated_lufs": -18.0,
        "true_peak_dbfs": -1.2,
        "generator": "edge_tts",
        "generator_revision": "7.2.8",
        "model_id": "zh-CN-XiaoxiaoNeural",
        "seed_provenance": "edge_tts_synthetic",
        "line_version": 1,
        "profile_version": 1,
        "postprocess_version": 1,
        "cues": [{"start_ms": 0, "end_ms": 1200, "text": line_text}],
        "approved": approved,
    }


@pytest.fixture
def promotion_fixture(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[Path, Path, Path, dict[str, bytes], bytes]:
    data_root = tmp_path / "backend" / "data"
    runtime_fixed = data_root / "voice_public" / "fixed"
    runtime_fixed.mkdir(parents=True)
    runtime_manifest = data_root / "voice_assets.json"
    render_root = tmp_path / ".codex-run" / "voice-renders"
    candidate_fixed = render_root / "fixed"
    candidate_fixed.mkdir(parents=True)

    previous_files: dict[str, bytes] = {}
    previous_manifest: list[dict[str, object]] = []
    candidate_manifest: list[dict[str, object]] = []
    for index, line_id in enumerate(PROMOTION_LINE_IDS):
        old_name = f"old-{index}.opus"
        old_payload = f"old-runtime-{index}".encode()
        (runtime_fixed / old_name).write_bytes(old_payload)
        previous_files[old_name] = old_payload
        previous_manifest.append(
            promotion_manifest_entry(
                line_id=line_id,
                filename=old_name,
                payload=old_payload,
                approved=True,
            )
        )

        candidate_name = f"candidate-{index}.opus"
        candidate_payload = f"new-candidate-{index}".encode()
        (candidate_fixed / candidate_name).write_bytes(candidate_payload)
        candidate_manifest.append(
            promotion_manifest_entry(
                line_id=line_id,
                filename=candidate_name,
                payload=candidate_payload,
                approved=False,
            )
        )

    previous_manifest_bytes = (
        json.dumps(previous_manifest, ensure_ascii=False, indent=2) + "\n"
    ).encode()
    runtime_manifest.write_bytes(previous_manifest_bytes)
    (render_root / "voice_assets.candidate.json").write_text(
        json.dumps(candidate_manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (data_root / "voice_lines.json").write_text("[]\n", encoding="utf-8")
    (data_root / "voice_profiles.json").write_text("[]\n", encoding="utf-8")
    monkeypatch.setattr(fixed_assets, "validate_voice_assets", lambda **_: [])

    return (
        tmp_path,
        runtime_fixed,
        runtime_manifest,
        previous_files,
        previous_manifest_bytes,
    )


@pytest.mark.parametrize("failure_kind", ("unlink", "copy", "replace"))
def test_promotion_failure_restores_previous_runtime_bundle(
    promotion_fixture,
    monkeypatch: pytest.MonkeyPatch,
    failure_kind: str,
) -> None:
    (
        repository_root,
        runtime_fixed,
        runtime_manifest,
        previous_files,
        previous_manifest_bytes,
    ) = promotion_fixture
    failure_injected = False
    matched_calls = 0
    original_unlink = Path.unlink
    original_copy2 = fixed_assets.shutil.copy2
    original_replace = Path.replace

    def fail_during_unlink(path: Path, *args, **kwargs):
        nonlocal failure_injected, matched_calls
        if failure_kind == "unlink" and path.parent == runtime_fixed:
            matched_calls += 1
            if matched_calls == 2 and not failure_injected:
                failure_injected = True
                raise OSError("injected unlink failure")
        return original_unlink(path, *args, **kwargs)

    def fail_during_copy(source, destination, *args, **kwargs):
        nonlocal failure_injected, matched_calls
        destination_path = Path(destination)
        if failure_kind == "copy" and destination_path.parent == runtime_fixed:
            matched_calls += 1
            if matched_calls == 2 and not failure_injected:
                failure_injected = True
                raise OSError("injected copy failure")
        return original_copy2(source, destination, *args, **kwargs)

    def fail_during_replace(path: Path, target: Path):
        nonlocal failure_injected
        if (
            failure_kind == "replace"
            and Path(target) == runtime_manifest
            and not failure_injected
        ):
            failure_injected = True
            raise OSError("injected replace failure")
        return original_replace(path, target)

    monkeypatch.setattr(Path, "unlink", fail_during_unlink)
    monkeypatch.setattr(fixed_assets.shutil, "copy2", fail_during_copy)
    monkeypatch.setattr(Path, "replace", fail_during_replace)

    with pytest.raises(OSError, match=f"injected {failure_kind} failure"):
        fixed_assets.promote_candidates(repository_root=repository_root)

    assert failure_injected is True
    assert {
        path.name: path.read_bytes()
        for path in runtime_fixed.iterdir()
        if path.is_file()
    } == previous_files
    assert runtime_manifest.read_bytes() == previous_manifest_bytes
    assert not runtime_manifest.with_suffix(".json.tmp").exists()


@pytest.fixture
def pipeline_fixture(
    tmp_path: Path,
) -> tuple[
    dict[str, Path],
    dict[str, MediaInfo],
    Callable[[Path], MediaInfo],
]:
    lines = [
        {
            "id": LINE_ID,
            "source_ref": "scene:scene_1972.transition_in",
            "speaker_profile": "memory_narrator.archive",
            "text": LINE_TEXT,
            "subtitle_segments": [LINE_TEXT],
            "emotion": "neutral",
            "intensity": 0.35,
            "space": "memory_archive",
            "delivery": "pre_generated",
            "priority": "narration",
            "version": 1,
        }
    ]
    profiles = [
        {
            "id": "memory_narrator.archive",
            "voice_lineage_id": "memory_narrator",
            "register": "low_mid",
            "pace": 0.86,
            "dialect": {"name": "standard_mandarin", "strength": 0.0},
            "breathiness": 0.15,
            "emotion_limits": {"neutral": 0.8},
            "forbidden_traits": ["character imitation"],
            "provider": {
                "cosyvoice_seed": "seeds/memory-narrator.wav",
                "cosyvoice_instruction": "archive narration",
                "edge_voice": "zh-CN-XiaoxiaoNeural",
            },
            "seed_provenance": "edge_tts_synthetic",
            "version": 1,
        }
    ]
    asset_path = tmp_path / "public" / "fixed" / "line.opus"
    asset_path.parent.mkdir(parents=True)
    asset_path.write_bytes(ASSET_BYTES)
    assets = [
        {
            "id": LINE_ID,
            "filename": "fixed/line.opus",
            "media_type": "audio/ogg; codecs=opus",
            "duration_ms": 1_200,
            "sha256": hashlib.sha256(ASSET_BYTES).hexdigest(),
            "text_sha256": hashlib.sha256(LINE_TEXT.encode("utf-8")).hexdigest(),
            "integrated_lufs": -18.0,
            "true_peak_dbfs": -1.2,
            "generator": "edge_tts",
            "generator_revision": "7.2.8",
            "model_id": "zh-CN-XiaoxiaoNeural",
            "seed_provenance": "edge_tts_synthetic",
            "line_version": 1,
            "profile_version": 1,
            "postprocess_version": 1,
            "cues": [{"start_ms": 0, "end_ms": 1200, "text": LINE_TEXT}],
            "approved": True,
        }
    ]
    paths = {
        "lines": tmp_path / "voice_lines.json",
        "profiles": tmp_path / "voice_profiles.json",
        "manifest": tmp_path / "voice_assets.json",
        "public": tmp_path / "public",
        "asset": asset_path,
    }
    paths["lines"].write_text(json.dumps(lines, ensure_ascii=False), encoding="utf-8")
    paths["profiles"].write_text(
        json.dumps(profiles, ensure_ascii=False), encoding="utf-8"
    )
    paths["manifest"].write_text(
        json.dumps(assets, ensure_ascii=False), encoding="utf-8"
    )
    media = {
        str(asset_path.resolve()): MediaInfo(
            duration_ms=1_200,
            channels=1,
            sample_rate=48_000,
            codec_name="opus",
            integrated_lufs=-18.0,
            true_peak_dbfs=-1.2,
        )
    }

    def inspect(path: Path) -> MediaInfo:
        return media[str(path.resolve())]

    return paths, media, inspect


def run_validation(
    paths: dict[str, Path],
    inspect: Callable[[Path], MediaInfo],
) -> set[str]:
    return {
        issue.code
        for issue in validate_voice_assets(
            manifest_path=paths["manifest"],
            lines_path=paths["lines"],
            profiles_path=paths["profiles"],
            public_root=paths["public"],
            media_inspector=inspect,
        )
    }


def load_manifest(paths: dict[str, Path]) -> list[dict[str, object]]:
    raw = json.loads(paths["manifest"].read_text(encoding="utf-8"))
    assert isinstance(raw, list)
    return raw


def write_manifest(paths: dict[str, Path], manifest: list[dict[str, object]]) -> None:
    paths["manifest"].write_text(
        json.dumps(manifest, ensure_ascii=False), encoding="utf-8"
    )


def test_validation_never_contacts_edge(
    pipeline_fixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths, _, inspect = pipeline_fixture

    def fail_if_called(**kwargs):
        raise AssertionError("validation contacted Edge")

    monkeypatch.setattr(
        "backend.integrations.tts._edge_communicator_factory",
        fail_if_called,
    )

    assert run_validation(paths, inspect) == set()


def test_missing_fixed_asset_is_rejected(pipeline_fixture) -> None:
    paths, _, inspect = pipeline_fixture
    paths["asset"].unlink()

    assert "MISSING_FIXED_ASSET" in run_validation(paths, inspect)


def test_mismatched_audio_hash_is_rejected(pipeline_fixture) -> None:
    paths, _, inspect = pipeline_fixture
    manifest = load_manifest(paths)
    manifest[0]["sha256"] = "0" * 64
    write_manifest(paths, manifest)

    assert "ASSET_SHA256_MISMATCH" in run_validation(paths, inspect)


def test_unapproved_asset_is_rejected(pipeline_fixture) -> None:
    paths, _, inspect = pipeline_fixture
    manifest = load_manifest(paths)
    manifest[0]["approved"] = False
    write_manifest(paths, manifest)

    assert "ASSET_UNAPPROVED" in run_validation(paths, inspect)


@pytest.mark.parametrize(
    ("field", "value", "expected_code"),
    [
        ("line_version", 2, "LINE_VERSION_MISMATCH"),
        ("profile_version", 2, "PROFILE_VERSION_MISMATCH"),
        ("generator_revision", "7.2.7", "GENERATOR_REVISION_STALE"),
        ("model_id", "zh-CN-YunyangNeural", "MODEL_ID_INVALID"),
    ],
)
def test_stale_generation_locks_are_rejected(
    pipeline_fixture,
    field: str,
    value: object,
    expected_code: str,
) -> None:
    paths, _, inspect = pipeline_fixture
    manifest = load_manifest(paths)
    manifest[0][field] = value
    write_manifest(paths, manifest)

    assert expected_code in run_validation(paths, inspect)


def test_duplicate_line_id_is_rejected(pipeline_fixture) -> None:
    paths, _, inspect = pipeline_fixture
    manifest = load_manifest(paths)
    duplicate = dict(manifest[0])
    duplicate["filename"] = "fixed/duplicate.opus"
    write_manifest(paths, [manifest[0], duplicate])

    assert "DUPLICATE_LINE_ID" in run_validation(paths, inspect)


def test_duplicate_filename_is_rejected(pipeline_fixture) -> None:
    paths, _, inspect = pipeline_fixture
    lines = json.loads(paths["lines"].read_text(encoding="utf-8"))
    second_line = dict(lines[0])
    second_line["id"] = "scene_1972.transition_out"
    lines.append(second_line)
    paths["lines"].write_text(json.dumps(lines, ensure_ascii=False), encoding="utf-8")
    manifest = load_manifest(paths)
    second_asset = dict(manifest[0])
    second_asset["id"] = second_line["id"]
    manifest.append(second_asset)
    write_manifest(paths, manifest)

    assert "DUPLICATE_FILENAME" in run_validation(paths, inspect)


@pytest.mark.parametrize(
    ("replacement", "expected_code"),
    [
        ({"channels": 2}, "MEDIA_NOT_MONO"),
        ({"sample_rate": 44_100}, "MEDIA_SAMPLE_RATE_INVALID"),
        ({"integrated_lufs": -20.0}, "LOUDNESS_OUT_OF_RANGE"),
        ({"true_peak_dbfs": -0.5}, "TRUE_PEAK_EXCEEDED"),
    ],
)
def test_measured_media_constraints_are_enforced(
    pipeline_fixture,
    replacement: dict[str, object],
    expected_code: str,
) -> None:
    paths, media, inspect = pipeline_fixture
    key = str(paths["asset"].resolve())
    original = media[key]
    values = {
        "duration_ms": original.duration_ms,
        "channels": original.channels,
        "sample_rate": original.sample_rate,
        "codec_name": original.codec_name,
        "integrated_lufs": original.integrated_lufs,
        "true_peak_dbfs": original.true_peak_dbfs,
    }
    values.update(replacement)
    media[key] = MediaInfo(**values)

    assert expected_code in run_validation(paths, inspect)


@pytest.mark.parametrize(
    ("cues", "expected_code"),
    [
        (
            [
                {"start_ms": 0, "end_ms": 700, "text": "戏要"},
                {"start_ms": 600, "end_ms": 1200, "text": "开场了。"},
            ],
            "CUE_OVERLAP",
        ),
        (
            [
                {"start_ms": 700, "end_ms": 800, "text": "戏要"},
                {"start_ms": 600, "end_ms": 1200, "text": "开场了。"},
            ],
            "CUE_ORDER_INVALID",
        ),
        (
            [{"start_ms": 0, "end_ms": 1201, "text": LINE_TEXT}],
            "CUE_DURATION_EXCEEDED",
        ),
        (
            [
                {"start_ms": 0, "end_ms": 700, "text": "戏要"},
                {"start_ms": 700, "end_ms": 700, "text": "开场了。"},
            ],
            "CUE_SPAN_INVALID",
        ),
    ],
)
def test_cue_timing_constraints_are_enforced(
    pipeline_fixture,
    cues: list[dict[str, object]],
    expected_code: str,
) -> None:
    paths, _, inspect = pipeline_fixture
    manifest = load_manifest(paths)
    manifest[0]["cues"] = cues
    write_manifest(paths, manifest)

    assert expected_code in run_validation(paths, inspect)


def test_cue_text_must_reconstruct_subtitles_and_canonical_text(
    pipeline_fixture,
) -> None:
    paths, _, inspect = pipeline_fixture
    manifest = load_manifest(paths)
    manifest[0]["cues"] = [{"start_ms": 0, "end_ms": 1200, "text": "不一致。"}]
    write_manifest(paths, manifest)

    assert "CUE_TEXT_MISMATCH" in run_validation(paths, inspect)


def test_stale_runtime_file_is_rejected(pipeline_fixture) -> None:
    paths, _, inspect = pipeline_fixture
    (paths["public"] / "fixed" / "stale.opus").write_bytes(b"stale")

    assert "STALE_FIXED_ASSET" in run_validation(paths, inspect)
