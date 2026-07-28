from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from backend.content.registry import ContentRegistry, ContentValidationError
from backend.domain.errors import DomainError


DATA_DIR = Path(__file__).resolve().parents[2] / "data"
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


@pytest.fixture
def shipping_documents() -> dict[str, object]:
    return {
        name: json.loads((DATA_DIR / filename).read_text(encoding="utf-8"))
        for name, filename in DOCUMENT_FILES.items()
    }


def expect_validation_code(documents: dict[str, object], code: str) -> None:
    with pytest.raises(ContentValidationError) as caught:
        ContentRegistry.from_documents(documents)
    assert caught.value.code == code


def voice_asset_candidate(
    line_id: str = "scene_1972.transition_in",
) -> dict[str, object]:
    line_text = next(
        (
            item["text"]
            for item in json.loads(
                (DATA_DIR / "voice_lines.json").read_text(encoding="utf-8")
            )
            if item["id"] == line_id
        ),
        "missing canonical line",
    )
    assert isinstance(line_text, str)
    return {
        "id": line_id,
        "filename": "fixed/scene-1972-transition-in.opus",
        "media_type": "audio/ogg; codecs=opus",
        "duration_ms": 1200,
        "sha256": "0" * 64,
        "text_sha256": hashlib.sha256(line_text.encode("utf-8")).hexdigest(),
        "integrated_lufs": -18.0,
        "true_peak_dbfs": -1.0,
        "generator": "edge_tts",
        "generator_revision": "7.2.8",
        "model_id": "zh-CN-XiaoxiaoNeural",
        "seed_provenance": "edge_tts_synthetic",
        "line_version": 1,
        "profile_version": 1,
        "postprocess_version": 1,
        "cues": [],
        "approved": True,
    }


def replace_voice_asset(
    documents: dict[str, object],
    candidate: dict[str, object],
) -> None:
    assets = documents["voice_assets"]
    assert isinstance(assets, list)
    line_id = candidate["id"]
    index = next(
        index for index, asset in enumerate(assets) if asset["id"] == line_id
    )
    assets[index] = candidate


def test_shipping_content_counts_and_references() -> None:
    registry = ContentRegistry.load(DATA_DIR)

    assert len(registry.scenes) == 5
    assert len(registry.npcs) == 7
    assert len(registry.fragments) == 17
    assert len(registry.hypotheses) == 1
    assert len(registry.endings) == 4
    assert len(registry.voice_profiles) == 9
    assert len(registry.voice_lines) == 7
    assert len(registry.voice_assets) == 7
    assert {
        hotspot.fragment_id
        for hotspot in registry.hotspots.values()
        if hotspot.fragment_id is not None
    } == set(registry.fragments)
    registry.validate()


def test_content_validator_reports_voice_registry() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/validate_content.py"],
        capture_output=True,
        check=False,
        text=True,
    )

    assert result.returncode == 0
    assert (
        "9 voice profiles, 7 voice lines, 7 approved voice assets"
        in result.stdout
    )


def test_registry_loads_first_act_hypothesis() -> None:
    registry = ContentRegistry.load(DATA_DIR)

    hypothesis = registry.get_hypothesis("hypothesis_1972_legacy")

    assert hypothesis.scene_id == "scene_1972"
    assert hypothesis.evidence_ids == (
        "fragment_grandpa_knife",
        "fragment_shadow_puppet",
    )


def test_registry_loads_voice_profiles_and_first_act_lines() -> None:
    registry = ContentRegistry.load(DATA_DIR)

    assert registry.get_npc("chen_shouyi_young").voice_profile_id == "chen_shouyi.age_25"
    assert registry.get_npc("xiaoyu").age == 87
    assert registry.get_npc("xiaoyu").voice_profile_id == "xiaoyu.age_87"
    assert registry.get_voice_profile("chen_shouyi.age_43").voice_lineage_id == "chen_shouyi"
    assert registry.get_voice_profile("xiaoyu.age_87").voice_lineage_id == "xiaoyu"
    assert registry.get_voice_line("hypothesis_1972_legacy.resolution").delivery == "pre_generated"
    assert (
        registry.get_voice_asset("hypothesis_1972_legacy.resolution").approved is True
    )


def test_duplicate_internal_ids_are_rejected(shipping_documents: dict[str, object]) -> None:
    documents = copy.deepcopy(shipping_documents)
    scenes = documents["scenes"]
    assert isinstance(scenes, dict)
    scenes["duplicate_scene"] = copy.deepcopy(scenes["scene_1972"])

    expect_validation_code(documents, "CONTENT_DUPLICATE_ID")


def test_scene_npc_reference_must_exist(shipping_documents: dict[str, object]) -> None:
    documents = copy.deepcopy(shipping_documents)
    scenes = documents["scenes"]
    assert isinstance(scenes, dict)
    scenes["scene_1972"]["npcs"].append("missing_npc")

    expect_validation_code(documents, "SCENE_NPC_NOT_FOUND")


def test_hotspot_fragment_must_belong_to_same_scene(
    shipping_documents: dict[str, object],
) -> None:
    documents = copy.deepcopy(shipping_documents)
    hotspots = documents["hotspots"]
    assert isinstance(hotspots, list)
    hotspot = next(item for item in hotspots if item["scene_id"] == "scene_1972")
    hotspot["fragment_id"] = "train_ticket_fragment"

    expect_validation_code(documents, "HOTSPOT_FRAGMENT_SCENE_MISMATCH")


def test_choice_target_scene_must_exist(shipping_documents: dict[str, object]) -> None:
    documents = copy.deepcopy(shipping_documents)
    choices = documents["choices"]
    assert isinstance(choices, list)
    choices[0]["target_scene"] = "scene_missing"

    expect_validation_code(documents, "CHOICE_TARGET_SCENE_NOT_FOUND")


def test_npc_reveal_fragment_must_exist(shipping_documents: dict[str, object]) -> None:
    documents = copy.deepcopy(shipping_documents)
    npcs = documents["npcs"]
    assert isinstance(npcs, dict)
    npcs["chen_shouyi_young"]["fragments_to_reveal"].append("fragment_missing")

    expect_validation_code(documents, "NPC_FRAGMENT_NOT_FOUND")


def test_scene_requires_a_fallback_asset(shipping_documents: dict[str, object]) -> None:
    documents = copy.deepcopy(shipping_documents)
    scenes = documents["scenes"]
    assert isinstance(scenes, dict)
    scenes["scene_1972"]["fallback_asset"] = ""

    expect_validation_code(documents, "SCENE_FALLBACK_ASSET_REQUIRED")


def test_ending_condition_npcs_must_exist(shipping_documents: dict[str, object]) -> None:
    documents = copy.deepcopy(shipping_documents)
    endings = documents["endings"]
    assert isinstance(endings, list)
    endings[0]["conditions"]["required_npc_trust"] = {"missing_npc": 60}

    expect_validation_code(documents, "ENDING_NPC_NOT_FOUND")


def test_npc_voice_profile_must_exist(shipping_documents: dict[str, object]) -> None:
    documents = copy.deepcopy(shipping_documents)
    npcs = documents["npcs"]
    assert isinstance(npcs, dict)
    npcs["chen_shouyi_young"]["voice_profile_id"] = "missing.profile"

    expect_validation_code(documents, "NPC_VOICE_PROFILE_NOT_FOUND")


def test_duplicate_voice_line_ids_are_rejected(
    shipping_documents: dict[str, object],
) -> None:
    documents = copy.deepcopy(shipping_documents)
    lines = documents["voice_lines"]
    assert isinstance(lines, list)
    lines.append(copy.deepcopy(lines[0]))

    expect_validation_code(documents, "CONTENT_DUPLICATE_ID")


def test_voice_asset_line_must_exist(shipping_documents: dict[str, object]) -> None:
    documents = copy.deepcopy(shipping_documents)
    assets = documents["voice_assets"]
    assert isinstance(assets, list)
    assets.append(voice_asset_candidate("missing.line"))

    expect_validation_code(documents, "VOICE_ASSET_LINE_NOT_FOUND")


def test_unapproved_voice_asset_is_rejected(
    shipping_documents: dict[str, object],
) -> None:
    documents = copy.deepcopy(shipping_documents)
    assets = documents["voice_assets"]
    assert isinstance(assets, list)
    candidate = voice_asset_candidate()
    candidate["approved"] = False
    replace_voice_asset(documents, candidate)

    expect_validation_code(documents, "VOICE_ASSET_NOT_APPROVED")


def test_voice_asset_generator_must_be_edge_tts(
    shipping_documents: dict[str, object],
) -> None:
    documents = copy.deepcopy(shipping_documents)
    assets = documents["voice_assets"]
    assert isinstance(assets, list)
    candidate = voice_asset_candidate()
    candidate["generator"] = "human_recording"
    replace_voice_asset(documents, candidate)

    expect_validation_code(documents, "CONTENT_SCHEMA_INVALID")


def test_voice_asset_generator_revision_must_be_trusted(
    shipping_documents: dict[str, object],
) -> None:
    documents = copy.deepcopy(shipping_documents)
    assets = documents["voice_assets"]
    assert isinstance(assets, list)
    candidate = voice_asset_candidate()
    candidate["generator_revision"] = "untrusted-revision"
    replace_voice_asset(documents, candidate)

    expect_validation_code(documents, "VOICE_ASSET_GENERATOR_REVISION_INVALID")


def test_voice_asset_model_identity_must_be_trusted(
    shipping_documents: dict[str, object],
) -> None:
    documents = copy.deepcopy(shipping_documents)
    assets = documents["voice_assets"]
    assert isinstance(assets, list)
    candidate = voice_asset_candidate()
    candidate["model_id"] = "unknown-model"
    replace_voice_asset(documents, candidate)

    expect_validation_code(documents, "VOICE_ASSET_MODEL_ID_INVALID")


def test_voice_asset_line_version_must_match_canonical_line(
    shipping_documents: dict[str, object],
) -> None:
    documents = copy.deepcopy(shipping_documents)
    assets = documents["voice_assets"]
    assert isinstance(assets, list)
    candidate = voice_asset_candidate()
    candidate["line_version"] = 2
    replace_voice_asset(documents, candidate)

    expect_validation_code(documents, "VOICE_ASSET_LINE_VERSION_MISMATCH")


def test_voice_asset_profile_version_must_match_speaker_profile(
    shipping_documents: dict[str, object],
) -> None:
    documents = copy.deepcopy(shipping_documents)
    assets = documents["voice_assets"]
    assert isinstance(assets, list)
    candidate = voice_asset_candidate()
    candidate["profile_version"] = 2
    replace_voice_asset(documents, candidate)

    expect_validation_code(documents, "VOICE_ASSET_PROFILE_VERSION_MISMATCH")


def test_voice_asset_seed_provenance_must_be_edge_synthetic(
    shipping_documents: dict[str, object],
) -> None:
    documents = copy.deepcopy(shipping_documents)
    assets = documents["voice_assets"]
    assert isinstance(assets, list)
    candidate = voice_asset_candidate()
    candidate["seed_provenance"] = "cosyvoice_sft_synthetic"
    replace_voice_asset(documents, candidate)

    expect_validation_code(documents, "CONTENT_SCHEMA_INVALID")


def test_shipping_profiles_lock_five_edge_synthetic_seed_lineages(
    shipping_documents: dict[str, object],
) -> None:
    profiles = shipping_documents["voice_profiles"]
    assert isinstance(profiles, list)

    assert {
        item["provider"]["cosyvoice_seed"]
        for item in profiles
    } == {
        "seeds/chen_shouyi-base.wav",
        "seeds/xiaoyu-base.wav",
        "seeds/stranger-1990.wav",
        "seeds/journalist-2050.wav",
        "seeds/memory-narrator.wav",
    }
    assert {item["seed_provenance"] for item in profiles} == {
        "edge_tts_synthetic"
    }


def test_voice_asset_text_hash_must_match_canonical_line(
    shipping_documents: dict[str, object],
) -> None:
    documents = copy.deepcopy(shipping_documents)
    assets = documents["voice_assets"]
    assert isinstance(assets, list)
    candidate = voice_asset_candidate()
    candidate["text_sha256"] = "0" * 64
    replace_voice_asset(documents, candidate)

    expect_validation_code(documents, "VOICE_ASSET_TEXT_HASH_MISMATCH")


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


def test_unknown_lookup_raises_machine_readable_domain_error() -> None:
    registry = ContentRegistry.load(DATA_DIR)

    with pytest.raises(DomainError) as caught:
        registry.get_scene("scene_missing")

    assert caught.value.code == "SCENE_NOT_FOUND"
