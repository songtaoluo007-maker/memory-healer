from __future__ import annotations

import copy
import json
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
    "endings": "endings.json",
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


def test_shipping_content_counts_and_references() -> None:
    registry = ContentRegistry.load(DATA_DIR)

    assert len(registry.scenes) == 5
    assert len(registry.npcs) == 7
    assert len(registry.fragments) == 17
    assert len(registry.endings) == 4
    assert {
        hotspot.fragment_id
        for hotspot in registry.hotspots.values()
        if hotspot.fragment_id is not None
    } == set(registry.fragments)
    registry.validate()


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


def test_unknown_lookup_raises_machine_readable_domain_error() -> None:
    registry = ContentRegistry.load(DATA_DIR)

    with pytest.raises(DomainError) as caught:
        registry.get_scene("scene_missing")

    assert caught.value.code == "SCENE_NOT_FOUND"
