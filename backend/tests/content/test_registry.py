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
        "generator_provenance": "edge_managed_cloud",
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
    assert len(registry.hypotheses) == 3
    assert len(registry.consequences) == 2
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


def test_shipping_fragment_unlock_metadata_is_globally_authoritative() -> None:
    registry = ContentRegistry.load(DATA_DIR)

    for fragment in registry.fragments.values():
        hotspot = next(
            item
            for item in registry.hotspots.values()
            if item.fragment_id == fragment.id
        )
        if fragment.unlock_method == "dialogue":
            assert fragment.unlock_npc_id is not None
            assert fragment.dialogue_prompt is not None
            assert fragment.dialogue_prompt.strip()
            assert fragment.minimum_trust is None
            assert hotspot.npc_id == fragment.unlock_npc_id
        elif fragment.unlock_method == "trust":
            assert fragment.unlock_npc_id is not None
            assert fragment.minimum_trust is not None
            assert fragment.dialogue_prompt is None
            assert fragment.dialogue_trust_reward == 0
            assert hotspot.npc_id == fragment.unlock_npc_id
        else:
            assert fragment.unlock_npc_id is None
            assert fragment.minimum_trust is None
            assert fragment.dialogue_prompt is None
            assert fragment.dialogue_trust_reward == 0


def test_shipping_1990_reasoning_and_consequences_match_the_story_contract() -> None:
    registry = ContentRegistry.load(DATA_DIR)

    hypotheses = [
        item
        for item in registry.hypotheses.values()
        if item.scene_id == "scene_1990"
    ]
    assert [item.id for item in hypotheses] == [
        "hypothesis_1990_survival",
        "hypothesis_1990_modern_story",
    ]
    assert hypotheses[0].outcome == "rejected"
    assert hypotheses[0].evidence_ids == (
        "train_ticket_fragment",
        "farewell_letter_fragment",
    )
    assert hypotheses[1].outcome == "confirmed"
    assert hypotheses[1].evidence_ids == (
        "puppet_trunk_fragment",
        "station_clock_fragment",
    )
    assert [item.variant for item in registry.consequences.values()] == [
        "legacy_carried",
        "legacy_suppressed",
    ]


def test_2050_xiaoyu_does_not_claim_to_personally_remember_1972() -> None:
    registry = ContentRegistry.load(DATA_DIR)

    prompt = registry.get_npc("xiaoyu_2050").system_prompt

    assert "回忆1972年爷爷教你" not in prompt
    assert "照片" in prompt
    assert "爷爷口述" in prompt


@pytest.mark.parametrize(
    ("fragment_id", "mutation", "code"),
    [
        (
            "puppet_trunk_fragment",
            {"dialogue_prompt": None},
            "FRAGMENT_DIALOGUE_PROMPT_REQUIRED",
        ),
        (
            "station_clock_fragment",
            {"minimum_trust": None},
            "FRAGMENT_TRUST_THRESHOLD_REQUIRED",
        ),
        (
            "train_ticket_fragment",
            {"dialogue_prompt": "不应存在的提示"},
            "FRAGMENT_EXPLORE_METADATA_FORBIDDEN",
        ),
        (
            "puppet_trunk_fragment",
            {"unlock_npc_id": "xiaoyu"},
            "FRAGMENT_UNLOCK_NPC_SCENE_MISMATCH",
        ),
        (
            "puppet_trunk_fragment",
            {"unlock_npc_id": "stranger_1990"},
            "FRAGMENT_HOTSPOT_NPC_MISMATCH",
        ),
    ],
)
def test_fragment_unlock_contract_rejects_invalid_metadata(
    shipping_documents: dict[str, object],
    fragment_id: str,
    mutation: dict[str, object],
    code: str,
) -> None:
    documents = copy.deepcopy(shipping_documents)
    fragments = documents["fragments"]
    assert isinstance(fragments, dict)
    fragments[fragment_id].update(mutation)

    expect_validation_code(documents, code)


def test_npc_fragment_list_must_agree_with_fragment_unlock_owner(
    shipping_documents: dict[str, object],
) -> None:
    documents = copy.deepcopy(shipping_documents)
    npcs = documents["npcs"]
    assert isinstance(npcs, dict)
    npcs["chen_shouyi_1990"]["fragments_to_reveal"].remove(
        "puppet_trunk_fragment"
    )

    expect_validation_code(documents, "NPC_FRAGMENT_UNLOCK_MISMATCH")


@pytest.mark.parametrize("insert_offset", [0, 1])
def test_fragment_cannot_have_duplicate_hotspots_regardless_of_document_order(
    shipping_documents: dict[str, object],
    insert_offset: int,
) -> None:
    documents = copy.deepcopy(shipping_documents)
    hotspots = documents["hotspots"]
    assert isinstance(hotspots, list)
    canonical_index = next(
        index
        for index, hotspot in enumerate(hotspots)
        if hotspot["id"] == "hotspot_1990_puppet_trunk"
    )
    duplicate = copy.deepcopy(hotspots[canonical_index])
    duplicate["id"] = "hotspot_1990_puppet_trunk_duplicate"
    duplicate["npc_id"] = "stranger_1990"
    hotspots.insert(canonical_index + insert_offset, duplicate)

    expect_validation_code(documents, "FRAGMENT_HOTSPOT_DUPLICATE")


@pytest.mark.parametrize(
    ("field", "value", "code"),
    [
        ("source_choice_id", "choice_missing", "CONSEQUENCE_CHOICE_NOT_FOUND"),
        ("target_scene_id", "scene_missing", "CONSEQUENCE_SCENE_NOT_FOUND"),
    ],
)
def test_consequence_choice_and_scene_references_must_exist(
    shipping_documents: dict[str, object],
    field: str,
    value: str,
    code: str,
) -> None:
    documents = copy.deepcopy(shipping_documents)
    documents["consequences"] = [
        {
            "id": "consequence_test",
            "source_choice_id": "encourage_art",
            "target_scene_id": "scene_1990",
            "variant": "test",
            "scene_text": "测试后果。",
            "npc_context": {"chen_shouyi_1990": "测试上下文。"},
        }
    ]
    consequences = documents["consequences"]
    assert isinstance(consequences, list)
    consequences[0][field] = value

    expect_validation_code(documents, code)


def test_consequence_npc_must_belong_to_target_scene(
    shipping_documents: dict[str, object],
) -> None:
    documents = copy.deepcopy(shipping_documents)
    documents["consequences"] = [
        {
            "id": "consequence_test",
            "source_choice_id": "encourage_art",
            "target_scene_id": "scene_1990",
            "variant": "test",
            "scene_text": "测试后果。",
            "npc_context": {"xiaoyu": "错误场景的上下文。"},
        }
    ]

    expect_validation_code(documents, "CONSEQUENCE_NPC_SCENE_MISMATCH")


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


def test_choice_requirements_support_each_canonical_kind(
    shipping_documents: dict[str, object],
) -> None:
    documents = copy.deepcopy(shipping_documents)
    choices = documents["choices"]
    assert isinstance(choices, list)
    choices[0]["requirements"] = [
        {
            "kind": "hypothesis_confirmed",
            "hypothesis_id": "hypothesis_1972_legacy",
        },
        {
            "kind": "fragment_collected",
            "fragment_id": "fragment_grandpa_knife",
        },
        {
            "kind": "npc_trust_at_least",
            "npc_id": "chen_shouyi_young",
            "minimum": 60,
        },
    ]

    registry = ContentRegistry.from_documents(documents)

    assert [requirement.model_dump() for requirement in registry.get_choice("encourage_art").requirements] == choices[0]["requirements"]


@pytest.mark.parametrize(
    ("requirement", "code"),
    [
        (
            {
                "kind": "hypothesis_confirmed",
                "hypothesis_id": "hypothesis_missing",
            },
            "CHOICE_REQUIREMENT_HYPOTHESIS_NOT_FOUND",
        ),
        (
            {
                "kind": "fragment_collected",
                "fragment_id": "fragment_missing",
            },
            "CHOICE_REQUIREMENT_FRAGMENT_NOT_FOUND",
        ),
        (
            {
                "kind": "npc_trust_at_least",
                "npc_id": "npc_missing",
                "minimum": 60,
            },
            "CHOICE_REQUIREMENT_NPC_NOT_FOUND",
        ),
    ],
)
def test_choice_requirement_references_must_exist(
    shipping_documents: dict[str, object],
    requirement: dict[str, object],
    code: str,
) -> None:
    documents = copy.deepcopy(shipping_documents)
    choices = documents["choices"]
    assert isinstance(choices, list)
    choices[0]["requirements"] = [requirement]

    expect_validation_code(documents, code)


@pytest.mark.parametrize(
    ("choice_id", "requirement", "code"),
    [
        (
            "talk_to_stranger",
            {
                "kind": "hypothesis_confirmed",
                "hypothesis_id": "hypothesis_1972_legacy",
            },
            "CHOICE_REQUIREMENT_HYPOTHESIS_SCENE_MISMATCH",
        ),
        (
            "encourage_art",
            {
                "kind": "fragment_collected",
                "fragment_id": "train_ticket_fragment",
            },
            "CHOICE_REQUIREMENT_FRAGMENT_SCENE_MISMATCH",
        ),
    ],
)
def test_choice_requirements_must_belong_to_choice_scene(
    shipping_documents: dict[str, object],
    choice_id: str,
    requirement: dict[str, object],
    code: str,
) -> None:
    documents = copy.deepcopy(shipping_documents)
    choices = documents["choices"]
    assert isinstance(choices, list)
    choice = next(item for item in choices if item["id"] == choice_id)
    choice["requirements"] = [requirement]

    expect_validation_code(documents, code)


def test_choice_trust_requirement_may_reference_canonical_npc_from_another_scene(
    shipping_documents: dict[str, object],
) -> None:
    documents = copy.deepcopy(shipping_documents)
    choices = documents["choices"]
    assert isinstance(choices, list)
    choice = next(item for item in choices if item["id"] == "talk_to_stranger")
    choice["requirements"] = [
        {
            "kind": "npc_trust_at_least",
            "npc_id": "chen_shouyi_young",
            "minimum": 60,
        }
    ]

    registry = ContentRegistry.from_documents(documents)

    assert registry.get_choice("talk_to_stranger").requirements[0].npc_id == "chen_shouyi_young"


@pytest.mark.parametrize("minimum", [-1, 101])
def test_choice_trust_requirement_rejects_out_of_range_thresholds(
    shipping_documents: dict[str, object],
    minimum: int,
) -> None:
    documents = copy.deepcopy(shipping_documents)
    choices = documents["choices"]
    assert isinstance(choices, list)
    choice = next(item for item in choices if item["id"] == "talk_to_stranger")
    choice["requirements"] = [
        {
            "kind": "npc_trust_at_least",
            "npc_id": "chen_shouyi_young",
            "minimum": minimum,
        }
    ]

    expect_validation_code(documents, "CONTENT_SCHEMA_INVALID")


def test_shipping_1972_choices_explicitly_require_legacy_hypothesis() -> None:
    registry = ContentRegistry.load(DATA_DIR)

    for choice_id in ("encourage_art", "discourage_art"):
        assert [
            requirement.model_dump()
            for requirement in registry.get_choice(choice_id).requirements
        ] == [
            {
                "kind": "hypothesis_confirmed",
                "hypothesis_id": "hypothesis_1972_legacy",
            }
        ]


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


def test_voice_asset_generator_provenance_must_be_edge_managed_cloud(
    shipping_documents: dict[str, object],
) -> None:
    documents = copy.deepcopy(shipping_documents)
    assets = documents["voice_assets"]
    assert isinstance(assets, list)
    candidate = voice_asset_candidate()
    candidate["generator_provenance"] = "local_model"
    replace_voice_asset(documents, candidate)

    expect_validation_code(documents, "CONTENT_SCHEMA_INVALID")


def test_shipping_profiles_expose_only_managed_edge_provider_fields(
    shipping_documents: dict[str, object],
) -> None:
    profiles = shipping_documents["voice_profiles"]
    assert isinstance(profiles, list)

    assert all(
        set(item["provider"]) <= {"edge_voice", "edge_rate", "edge_pitch"}
        for item in profiles
    )


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
