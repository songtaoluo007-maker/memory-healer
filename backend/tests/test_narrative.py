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
    assert "1972年 西安老巷" in prompt
    assert "进入场景" in prompt
    assert "warm" in prompt
    assert "0/9" in prompt  # 0个碎片


def test_build_narrative_prompt_with_fragments():
    game_state = {
        "current_scene": "scene_2024",
        "collected_fragments": ["fragment_letter", "fragment_old_photos"],
        "key_choices": ["helped_old_man"],
        "current_mood": "melancholy",
    }
    prompt = build_narrative_prompt(game_state, "查看墙上的照片")
    assert "2/9" in prompt  # 2个碎片
    assert "helped_old_man" in prompt
    assert "melancholy" in prompt
    assert "查看墙上的照片" in prompt


def test_build_prompt_has_json_format():
    game_state = {"current_scene": "scene_2089", "collected_fragments": [], "key_choices": [], "current_mood": "neutral"}
    prompt = build_narrative_prompt(game_state, "探索")
    assert "scene_description" in prompt
    assert "available_actions" in prompt
    assert "JSON" in prompt or "json" in prompt
