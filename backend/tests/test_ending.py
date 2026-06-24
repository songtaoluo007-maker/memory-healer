"""结局引擎测试"""
import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from engine.ending import evaluate_ending, get_ending_hint, KEY_CHOICES, KEY_NPCS, KEY_TRUST_THRESHOLD, BUTTERFLY_RULES


def make_game_state(**overrides):
    """创建测试用游戏状态"""
    state = {
        'collected_fragments': [],
        'fragment_states': {},
        'npc_trust': {},
        'butterfly_choices': {},
        'current_scene': 'scene_2089',
    }
    state.update(overrides)
    return state


class TestEndingEvaluation:
    """结局评估测试"""

    def test_hope_ending_high_fragments(self):
        """碎片≥80% → hope结局"""
        fragments = [f'f{i}' for i in range(14)]  # 14/17 ≈ 82%
        state = make_game_state(collected_fragments=fragments)
        result = evaluate_ending(state)
        assert result['type'] == 'hope'

    def test_bittersweet_ending_medium_fragments(self):
        """碎片40%-79% → bittersweet结局"""
        fragments = [f'f{i}' for i in range(9)]  # 9/17 ≈ 53%
        state = make_game_state(collected_fragments=fragments)
        result = evaluate_ending(state)
        assert result['type'] == 'bittersweet'

    def test_tragic_ending_low_fragments(self):
        """碎片<40% → tragic结局"""
        fragments = [f'f{i}' for i in range(5)]  # 5/17 ≈ 29%
        state = make_game_state(collected_fragments=fragments)
        result = evaluate_ending(state)
        assert result['type'] == 'tragic'

    def test_legacy_ending_all_conditions_met(self):
        """全碎片+关键选择+关键NPC信任≥60 → legacy结局"""
        from engine.ending import KEY_CHOICES, KEY_NPCS, KEY_TRUST_THRESHOLD
        all_frags = [f'fragment_{i}' for i in range(17)]
        trust = {npc: 70 for npc in KEY_NPCS}
        choices = {}
        for scene, choice_list in KEY_CHOICES.items():
            choices[scene] = choice_list[0]
        state = make_game_state(
            collected_fragments=all_frags,
            npc_trust=trust,
            butterfly_choices=choices,
        )
        result = evaluate_ending(state)
        assert result['type'] == 'legacy'

    def test_legacy_requires_all_fragments(self):
        """缺少碎片 → 不触发legacy"""
        from engine.ending import KEY_CHOICES, KEY_NPCS
        all_frags = [f'fragment_{i}' for i in range(16)]  # 少1个
        trust = {npc: 70 for npc in KEY_NPCS}
        choices = {}
        for scene, choice_list in KEY_CHOICES.items():
            choices[scene] = choice_list[0]
        state = make_game_state(
            collected_fragments=all_frags,
            npc_trust=trust,
            butterfly_choices=choices,
        )
        result = evaluate_ending(state)
        assert result['type'] != 'legacy'

    def test_legacy_requires_key_choices(self):
        """缺少关键选择 → 不触发legacy"""
        from engine.ending import KEY_NPCS
        all_frags = [f'fragment_{i}' for i in range(17)]
        trust = {npc: 70 for npc in KEY_NPCS}
        state = make_game_state(
            collected_fragments=all_frags,
            npc_trust=trust,
            butterfly_choices={},  # 无选择
        )
        result = evaluate_ending(state)
        assert result['type'] != 'legacy'

    def test_legacy_requires_key_npc_trust(self):
        """关键NPC信任不足 → 不触发legacy"""
        from engine.ending import KEY_CHOICES, KEY_NPCS
        all_frags = [f'fragment_{i}' for i in range(17)]
        trust = {npc: 30 for npc in KEY_NPCS}  # 信任不足
        choices = {}
        for scene, choice_list in KEY_CHOICES.items():
            choices[scene] = choice_list[0]
        state = make_game_state(
            collected_fragments=all_frags,
            npc_trust=trust,
            butterfly_choices=choices,
        )
        result = evaluate_ending(state)
        assert result['type'] != 'legacy'

    def test_empty_state_tragic(self):
        """空状态 → tragic"""
        state = make_game_state()
        result = evaluate_ending(state)
        assert result['type'] == 'tragic'

    def test_result_has_all_fields(self):
        """结果包含所有必要字段"""
        state = make_game_state(collected_fragments=['f1'])
        result = evaluate_ending(state)
        assert 'type' in result
        assert 'collected' in result
        assert 'total' in result
        assert 'percent' in result
        assert 'butterfly_triggered' in result
        assert 'butterfly_total' in result


class TestEndingHint:
    """结局提示测试"""

    def test_hint_for_low_fragments(self):
        """低碎片 → 提示收集"""
        state = make_game_state(collected_fragments=['f1'])
        hint = get_ending_hint(state)
        assert isinstance(hint, str)
        assert len(hint) > 0
        assert '碎片不足' in hint or '记忆' in hint

    def test_hint_for_high_fragments(self):
        """高碎片 → 不同提示"""
        fragments = [f'f{i}' for i in range(15)]
        state = make_game_state(collected_fragments=fragments)
        hint = get_ending_hint(state)
        assert isinstance(hint, str)
        assert '进展良好' in hint or '88' in hint


