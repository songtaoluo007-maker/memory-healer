"""prompts/npc_dialogue.py 单元测试"""
import pytest
from backend.prompts.npc_dialogue import build_npc_prompt


NPC = {
    "id": "chen_shouyi_young",
    "name": "陈守义",
    "system_prompt": "你是陈守义，一个25岁的皮影戏匠人。",
    "background": "第五代皮影戏传人。",
    "initial_trust": 30,
    "fragments_to_reveal": ["fragment_shadow_puppet", "fragment_grandpa_knife"],
}

SCENE = {
    "id": "scene_1972",
    "description": "黄昏的余晖洒在青石板路上。",
}


def test_prompt_basic():
    game_state = {
        "collected_fragments": [],
        "revealed_fragments": [],
        "npc_trust": {},
        "dialogue_history": [],
    }
    prompt = build_npc_prompt(NPC, SCENE, game_state, "你好")
    assert "陈守义" in prompt
    assert "皮影戏" in prompt
    assert "你好" in prompt
    assert "30/100" in prompt


def test_prompt_with_trust():
    game_state = {
        "collected_fragments": [],
        "revealed_fragments": [],
        "npc_trust": {"chen_shouyi_young": 75},
        "dialogue_history": [],
    }
    prompt = build_npc_prompt(NPC, SCENE, game_state, "聊聊你的手艺")
    assert "75/100" in prompt


def test_prompt_with_history():
    game_state = {
        "collected_fragments": [],
        "revealed_fragments": [],
        "npc_trust": {},
        "dialogue_history": [
            {"role": "player", "content": "你是谁"},
            {"role": "npc", "content": "我是陈守义"},
        ],
    }
    prompt = build_npc_prompt(NPC, SCENE, game_state, "继续说")
    assert "你是谁" in prompt
    assert "我是陈守义" in prompt


def test_prompt_fragment_status():
    game_state = {
        "collected_fragments": ["fragment_shadow_puppet"],
        "revealed_fragments": ["fragment_grandpa_knife"],
        "npc_trust": {},
        "dialogue_history": [],
    }
    prompt = build_npc_prompt(NPC, SCENE, game_state, "说说你的故事")
    assert "已收集" in prompt
    assert "已透露但未收集" in prompt
