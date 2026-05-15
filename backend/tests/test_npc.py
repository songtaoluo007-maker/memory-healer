"""engine/npc.py 单元测试（解析逻辑，不调用 API）"""
import pytest
from backend.engine.npc import _parse_npc_response


def test_parse_basic_reply():
    content = "你好啊，我是陈守义。[碎片:无] [信任:+5] [心情:happy]"
    reply, frag, trust, mood = _parse_npc_response(content)
    assert reply == "你好啊，我是陈守义。"
    assert frag is None
    assert trust == 5
    assert mood == "happy"


def test_parse_fragment_revealed():
    content = "我记得那个戏台……[碎片:fragment_shadow_puppet] [信任:+10] [心情:thinking]"
    reply, frag, trust, mood = _parse_npc_response(content)
    assert "戏台" in reply
    assert frag == "fragment_shadow_puppet"
    assert trust == 10
    assert mood == "thinking"


def test_parse_no_tags():
    content = "今天天气不错。"
    reply, frag, trust, mood = _parse_npc_response(content)
    assert reply == "今天天气不错。"
    assert frag is None
    assert trust == 0
    assert mood == "neutral"


def test_parse_negative_trust():
    content = "我不太想说。[碎片:无] [信任:-5] [心情:sad]"
    reply, frag, trust, mood = _parse_npc_response(content)
    assert trust == -5
    assert mood == "sad"


def test_parse_chinese_colon():
    """测试中文冒号分隔符"""
    content = "想起了……[碎片：fragment_letter] [信任：+3] [心情：neutral]"
    reply, frag, trust, mood = _parse_npc_response(content)
    assert frag == "fragment_letter"
    assert trust == 3
