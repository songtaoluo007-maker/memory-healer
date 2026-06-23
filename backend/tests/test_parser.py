"""
NPC对话输出解析器测试
"""
import pytest
from backend.engine.npc import _parse_json_response


class TestParseJsonResponse:
    """JSON解析测试"""

    def test_valid_json(self):
        """标准JSON格式"""
        content = '{"reply": "你好", "fragment": null, "trust_delta": 5, "emotion": "happy"}'
        reply, frag, trust, mood, inner = _parse_json_response(content)
        assert reply == "你好"
        assert frag is None
        assert trust == 5
        assert mood == "happy"

    def test_json_with_inner_thought(self):
        """带内心独白的JSON"""
        content = '{"reply": "你好", "fragment": null, "trust_delta": 0, "emotion": "neutral", "inner_thought": "这个人看起来很友善"}'
        reply, frag, trust, mood, inner = _parse_json_response(content)
        assert inner == "这个人看起来很友善"

    def test_json_with_fragment(self):
        """带碎片揭露的JSON"""
        content = '{"reply": "你看这个", "fragment": "old_photos", "trust_delta": 10, "emotion": "nostalgic"}'
        reply, frag, trust, mood, inner = _parse_json_response(content)
        assert frag == "old_photos"
        assert trust == 10

    def test_json_with_markdown_wrapper(self):
        """Markdown包裹的JSON"""
        content = '```json\n{"reply": "你好", "fragment": null, "trust_delta": 0, "emotion": "neutral"}\n```'
        reply, frag, trust, mood, inner = _parse_json_response(content)
        assert reply == "你好"

    def test_legacy_tag_fallback(self):
        """旧版标签格式降级"""
        content = '你好，我叫陈守义。[碎片:puppet_stage] [信任:+10] [情感:happy]'
        reply, frag, trust, mood, inner = _parse_json_response(content)
        assert "陈守义" in reply
        assert frag == "puppet_stage"
        assert trust == 10

    def test_invalid_emotion_fallback(self):
        """无效情感值降级"""
        content = '{"reply": "你好", "fragment": null, "trust_delta": 0, "emotion": "invalid_emotion"}'
        reply, frag, trust, mood, inner = _parse_json_response(content)
        assert mood == "neutral"

    def test_trust_delta_clamping(self):
        """信任度变化范围限制"""
        content = '{"reply": "你好", "fragment": null, "trust_delta": 100, "emotion": "neutral"}'
        reply, frag, trust, mood, inner = _parse_json_response(content)
        assert -20 <= trust <= 20

    def test_garbage_input(self):
        """垃圾输入降级"""
        content = "这是一段普通文本，不是JSON格式"
        reply, frag, trust, mood, inner = _parse_json_response(content)
        assert reply == content
        assert frag is None
        assert trust == 0
        assert mood == "neutral"

    def test_empty_input(self):
        """空输入"""
        content = ""
        reply, frag, trust, mood, inner = _parse_json_response(content)
        assert reply == ""
        assert frag is None
        assert trust == 0

    def test_partial_json(self):
        """不完整JSON — 应该能从正则提取reply"""
        content = '{"reply": "你好", "fragment":'
        reply, frag, trust, mood, inner = _parse_json_response(content)
        # 正则降级应该能提取reply
        assert reply == "你好"
        assert frag is None
        assert trust == 0


class TestEdgeCases:
    """边界情况测试"""

    def test_json_with_extra_fields(self):
        """JSON包含额外字段"""
        content = '{"reply": "你好", "fragment": null, "trust_delta": 0, "emotion": "neutral", "extra": "data"}'
        reply, frag, trust, mood, inner = _parse_json_response(content)
        assert reply == "你好"

    def test_json_with_unicode(self):
        """JSON包含Unicode"""
        content = '{"reply": "你好世界", "fragment": null, "trust_delta": 0, "emotion": "neutral"}'
        reply, frag, trust, mood, inner = _parse_json_response(content)
        assert reply == "你好世界"

    def test_json_with_newlines(self):
        """JSON包含换行"""
        content = '{"reply": "第一行\\n第二行", "fragment": null, "trust_delta": 0, "emotion": "neutral"}'
        reply, frag, trust, mood, inner = _parse_json_response(content)
        assert "第一行" in reply
