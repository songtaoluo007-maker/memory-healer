"""engine/narrative.py 单元测试（prompt 构建，不调用 API）"""
import pytest
from backend.prompts.narrative import build_narrative_prompt


def test_build_narrative_prompt_basic():
    game_state = {
        "current_scene": "scene_1972",
        "collected_fragments": [],
        "key_choices": [],
        "current_mood": "warm",
    }
    prompt = build_narrative_prompt(game_state, "进入场景")
    assert "scene_1972" in prompt
    assert "进入场景" in prompt
    assert "warm" in prompt


def test_build_narrative_prompt_with_fragments():
    game_state = {
        "current_scene": "scene_2024",
        "collected_fragments": ["fragment_letter", "fragment_old_photos"],
        "key_choices": ["helped_old_man"],
        "current_mood": "melancholy",
    }
    prompt = build_narrative_prompt(game_state, "查看墙上的照片")
    assert "fragment_letter" in prompt
    assert "fragment_old_photos" in prompt
    assert "helped_old_man" in prompt


def test_build_prompt_has_json_format():
    game_state = {"current_scene": "scene_2089", "collected_fragments": [], "key_choices": [], "current_mood": "neutral"}
    prompt = build_narrative_prompt(game_state, "探索")
    assert "scene_description" in prompt
    assert "available_actions" in prompt
    assert "JSON" in prompt or "json" in prompt
