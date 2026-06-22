"""
NPC情感状态机测试
"""
import pytest
from backend.engine.emotion import (
    EmotionStateMachine,
    EMOTION_STATES,
    EMOTION_TRANSITIONS,
    get_emotion_machine,
    process_emotion,
)


class TestEmotionStateMachine:
    """情感状态机基本功能测试"""

    def test_initial_state(self):
        """初始状态为neutral"""
        machine = EmotionStateMachine("test_npc")
        assert machine.emotion == "neutral"

    def test_custom_initial_state(self):
        """自定义初始状态"""
        machine = EmotionStateMachine("test_npc", "happy")
        assert machine.emotion == "happy"

    def test_analyze_caring_input(self):
        """分析关心类输入"""
        machine = EmotionStateMachine("test_npc")
        trigger = machine.analyze_input("你好，身体怎么样？")
        assert trigger == "关心"

    def test_analyze_encouraging_input(self):
        """分析鼓励类输入"""
        machine = EmotionStateMachine("test_npc")
        trigger = machine.analyze_input("加油，你很厉害！")
        assert trigger == "鼓励"

    def test_analyze_rude_input(self):
        """分析冒犯类输入"""
        machine = EmotionStateMachine("test_npc")
        trigger = machine.analyze_input("烦死了，闭嘴！")
        assert trigger == "冒犯"

    def test_analyze_default_input(self):
        """分析默认输入"""
        machine = EmotionStateMachine("test_npc")
        trigger = machine.analyze_input("我想问一下路")
        assert trigger == "默认"

    def test_neutral_to_happy(self):
        """neutral → happy转移"""
        machine = EmotionStateMachine("test_npc")
        result = machine.transition("关心")
        assert result["current"] == "happy"
        assert result["changed"] is True

    def test_neutral_to_annoyed(self):
        """neutral → annoyed转移"""
        machine = EmotionStateMachine("test_npc")
        result = machine.transition("冒犯")
        assert result["current"] == "annoyed"
        assert result["changed"] is True

    def test_happy_to_touched(self):
        """happy → touched转移"""
        machine = EmotionStateMachine("test_npc", "happy")
        result = machine.transition("深入话题")
        assert result["current"] == "touched"
        assert result["changed"] is True

    def test_same_emotion_no_change(self):
        """相同情感无变化"""
        machine = EmotionStateMachine("test_npc")
        result = machine.transition("默认")
        assert result["current"] == "neutral"
        assert result["changed"] is False

    def test_transition_history(self):
        """转移历史记录"""
        machine = EmotionStateMachine("test_npc")
        machine.transition("关心")
        machine.transition("深入话题")
        assert len(machine.emotion_history) == 3  # neutral + happy + touched

    def test_transition_count(self):
        """转移计数"""
        machine = EmotionStateMachine("test_npc")
        machine.transition("关心")
        machine.transition("默认")
        assert machine.transition_count == 1  # 只有真正改变才算

    def test_fragment_bonus(self):
        """碎片揭露加成"""
        machine = EmotionStateMachine("test_npc", "touched")
        bonus = machine.get_fragment_bonus()
        assert bonus == 20

    def test_trust_multiplier(self):
        """信任度乘数"""
        machine = EmotionStateMachine("test_npc", "happy")
        multiplier = machine.get_trust_multiplier()
        assert multiplier == 1.2

    def test_prompt_hint(self):
        """Prompt提示"""
        machine = EmotionStateMachine("test_npc", "happy")
        hint = machine.get_prompt_hint()
        assert "开心" in hint

    def test_prompt_hint_neutral(self):
        """neutral状态无Prompt提示"""
        machine = EmotionStateMachine("test_npc", "neutral")
        hint = machine.get_prompt_hint()
        assert hint == ""

    def test_serialization(self):
        """序列化"""
        machine = EmotionStateMachine("test_npc", "happy")
        data = machine.to_dict()
        assert data["npc_id"] == "test_npc"
        assert data["emotion"] == "happy"


class TestProcessEmotion:
    """process_emotion函数测试"""

    def test_process_caring_input(self):
        """处理关心输入"""
        game_state = {"npc_trust": {}}
        result = process_emotion("test_npc_caring", "你好，身体怎么样？", game_state)
        assert result["emotion_change"]["current"] == "happy"
        assert result["trust_multiplier"] > 1.0

    def test_process_rude_input(self):
        """处理冒犯输入"""
        game_state = {"npc_trust": {}}
        result = process_emotion("test_npc_rude", "烦死了", game_state)
        assert result["emotion_change"]["current"] == "annoyed"
        assert result["trust_multiplier"] < 1.0

    def test_process_saves_to_game_state(self):
        """处理后保存到游戏状态"""
        game_state = {"npc_trust": {}}
        process_emotion("test_npc_save", "你好", game_state)
        assert "npc_emotions" in game_state
        assert game_state["npc_emotions"]["test_npc_save"] == "happy"

    def test_process_restores_from_game_state(self):
        """从游戏状态恢复情感"""
        game_state = {
            "npc_trust": {},
            "npc_emotions": {"test_npc_restore": "nostalgic"},
        }
        result = process_emotion("test_npc_restore", "我想问一下路", game_state)
        # 应该从nostalgic状态开始
        assert result["emotion_change"]["previous"] == "nostalgic"


class TestGetEmotionMachine:
    """get_emotion_machine函数测试"""

    def test_creates_new_machine(self):
        """创建新状态机"""
        machine = get_emotion_machine("new_npc")
        assert machine.emotion == "neutral"

    def test_returns_existing_machine(self):
        """返回已有状态机"""
        machine1 = get_emotion_machine("existing_npc")
        machine1.transition("关心")
        machine2 = get_emotion_machine("existing_npc")
        assert machine2.emotion == "happy"


class TestEmotionStates:
    """情感状态定义测试"""

    def test_all_states_defined(self):
        """所有状态都有定义"""
        expected = ["neutral", "happy", "touched", "nostalgic", "sad", "annoyed", "worried"]
        for state in expected:
            assert state in EMOTION_STATES

    def test_all_states_have_required_fields(self):
        """所有状态都有必要字段"""
        for state_name, state_data in EMOTION_STATES.items():
            assert "name" in state_data
            assert "description" in state_data
            assert "fragment_bonus" in state_data
            assert "trust_multiplier" in state_data
            assert "decay_target" in state_data

    def test_transitions_cover_all_states(self):
        """转移规则覆盖所有状态"""
        for state in EMOTION_STATES:
            assert state in EMOTION_TRANSITIONS
