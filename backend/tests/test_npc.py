"""engine/npc.py 单元测试（解析逻辑，不调用 API）"""
import pytest
from backend.engine.npc import _parse_json_response


def test_parse_basic_reply():
    content = '{"reply": "你好啊，我是陈守义。", "fragment": null, "trust_delta": 5, "emotion": "happy", "inner_thought": "他在打招呼"}'
    reply, frag, trust, mood, inner = _parse_json_response(content)
    assert reply == "你好啊，我是陈守义。"
    assert frag is None
    assert trust == 5
    assert mood == "happy"
    assert inner == "他在打招呼"


def test_parse_fragment_revealed():
    content = '{"reply": "我记得那个戏台……", "fragment": "fragment_shadow_puppet", "trust_delta": 10, "emotion": "thinking", "inner_thought": "记忆涌上心头"}'
    reply, frag, trust, mood, inner = _parse_json_response(content)
    assert "戏台" in reply
    assert frag == "fragment_shadow_puppet"
    assert trust == 10
    assert mood == "thinking"


def test_parse_no_tags():
    content = '{"reply": "今天天气不错。", "fragment": null, "trust_delta": 0, "emotion": "neutral", "inner_thought": ""}'
    reply, frag, trust, mood, inner = _parse_json_response(content)
    assert reply == "今天天气不错。"
    assert frag is None
    assert trust == 0
    assert mood == "neutral"


def test_parse_legacy_format():
    """测试旧版标签格式的降级解析"""
    content = "你好啊，我是陈守义。[碎片:无] [信任:+5] [心情:happy]"
    reply, frag, trust, mood, inner = _parse_json_response(content)
    assert reply == "你好啊，我是陈守义。"
    assert frag is None
    assert trust == 5
    assert mood == "happy"


def test_parse_markdown_json():
    """测试markdown包裹的JSON"""
    content = '''```json
{"reply": "你好", "fragment": null, "trust_delta": 3, "emotion": "happy", "inner_thought": ""}
```'''
    reply, frag, trust, mood, inner = _parse_json_response(content)
    assert reply == "你好"
    assert trust == 3
    assert mood == "happy"


def test_parse_invalid_emotion():
    """测试无效情感值的处理"""
    content = '{"reply": "你好", "fragment": null, "trust_delta": 0, "emotion": "invalid_emotion", "inner_thought": ""}'
    reply, frag, trust, mood, inner = _parse_json_response(content)
    assert mood == "neutral"  # 无效情感应降级为neutral


def test_parse_trust_clamp():
    """测试信任度边界值"""
    content = '{"reply": "你好", "fragment": null, "trust_delta": 100, "emotion": "happy", "inner_thought": ""}'
    reply, frag, trust, mood, inner = _parse_json_response(content)
    assert trust == 20  # 应被限制在20以内
