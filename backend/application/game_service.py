from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from backend.content.models import (
    ChoiceContent,
    EndingContent,
    FragmentCollectedRequirementContent,
    HotspotContent,
    HypothesisConfirmedRequirementContent,
    HypothesisContent,
    NpcTrustAtLeastRequirementContent,
    SceneContent,
)
from backend.content.registry import ContentRegistry
from backend.domain.errors import DomainError
from backend.domain.game_state import GameState


class ApplicationModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class NpcSummaryView(ApplicationModel):
    id: str
    name: str
    title: str
    avatar: str
    initial_trust: int
    initial_voice_line_id: str | None = None


class SceneFragmentView(ApplicationModel):
    id: str
    name: str
    scene: str
    description: str
    unlock_method: str
    unlock_hint: str
    memory_text: str
    is_revealed: bool
    is_collected: bool
    memory_voice_line_id: str | None = None


class SceneView(ApplicationModel):
    scene: SceneContent
    npcs: list[NpcSummaryView]
    fragments: list[SceneFragmentView]
    hotspots: list[HotspotContent]
    choices: list[ChoiceContent]
    hypotheses: list[HypothesisContent]
    content_version: int = 1


class PresentationEvent(ApplicationModel):
    type: str
    content_id: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class ActionResult(ApplicationModel):
    state: GameState
    events: list[PresentationEvent] = Field(default_factory=list)


class GameService:
    def __init__(
        self,
        registry: ContentRegistry,
        *,
        now_provider: Callable[[], datetime] | None = None,
    ) -> None:
        self.registry = registry
        self.now_provider = now_provider or (lambda: datetime.now(timezone.utc))

    def create_game(self, game_id: UUID | None = None) -> GameState:
        return GameState.new(self.registry, self.now_provider(), game_id)

    def get_scene_view(self, state: GameState) -> SceneView:
        state.validate_content_references(self.registry)
        scene = self.registry.get_scene(state.current_scene)
        return SceneView(
            scene=scene,
            npcs=[
                NpcSummaryView(
                    id=npc.id,
                    name=npc.name,
                    title=npc.title,
                    avatar=npc.avatar,
                    initial_trust=npc.initial_trust,
                    initial_voice_line_id=npc.initial_voice_line_id,
                )
                for npc in self.registry.npcs.values()
                if npc.scene == scene.id
            ],
            fragments=[
                SceneFragmentView(
                    id=fragment.id,
                    name=fragment.name,
                    scene=fragment.scene,
                    description=fragment.description,
                    unlock_method=fragment.unlock_method,
                    unlock_hint=fragment.unlock_hint,
                    memory_text=fragment.memory_text,
                    is_revealed=fragment.id in state.revealed_fragments,
                    is_collected=fragment.id in state.collected_fragments,
                    memory_voice_line_id=fragment.memory_voice_line_id,
                )
                for fragment in self.registry.fragments.values()
                if fragment.scene == scene.id
            ],
            hotspots=[
                hotspot
                for hotspot in self.registry.hotspots.values()
                if hotspot.scene_id == scene.id
            ],
            choices=[
                choice
                for choice in self.registry.choices.values()
                if choice.scene_id == scene.id
            ],
            hypotheses=[
                hypothesis
                for hypothesis in self.registry.hypotheses.values()
                if hypothesis.scene_id == scene.id
            ],
        )

    @staticmethod
    def _check_revision(state: GameState, expected_revision: int) -> None:
        if state.revision != expected_revision:
            raise DomainError(
                "GAME_REVISION_CONFLICT",
                "游戏状态已更新，请加载最新状态后重试",
                details={
                    "expected_revision": expected_revision,
                    "actual_revision": state.revision,
                },
            )

    def explore(
        self,
        state: GameState,
        hotspot_id: str,
        *,
        expected_revision: int,
    ) -> ActionResult:
        self._check_revision(state, expected_revision)
        state.validate_content_references(self.registry)
        hotspot = self.registry.get_hotspot(hotspot_id)
        if hotspot.scene_id != state.current_scene:
            raise DomainError(
                "HOTSPOT_INVALID",
                "该热区不属于当前场景",
                details={
                    "hotspot_id": hotspot.id,
                    "current_scene": state.current_scene,
                },
            )

        if hotspot.fragment_id is None:
            return ActionResult(state=state.model_copy(deep=True))
        if hotspot.fragment_id in state.collected_fragments:
            return ActionResult(state=state.model_copy(deep=True))

        payload = state.model_dump(mode="python")
        fragment_id = hotspot.fragment_id
        if fragment_id not in payload["revealed_fragments"]:
            payload["revealed_fragments"].append(fragment_id)
        payload["collected_fragments"].append(fragment_id)
        fragment_state = payload["fragment_states"][fragment_id]
        fragment_state["status"] = "collected"
        fragment_state["revealed"] = True
        fragment_state["collected"] = True
        payload["revision"] += 1

        next_state = GameState.model_validate(payload)
        next_state.validate_content_references(self.registry)
        return ActionResult(
            state=next_state,
            events=[
                PresentationEvent(
                    type="fragment.collected",
                    content_id=fragment_id,
                    payload={
                        "hotspot_id": hotspot.id,
                        "presentation_event": hotspot.presentation_event,
                    },
                )
            ],
        )

    def confirm_hypothesis(
        self,
        state: GameState,
        hypothesis_id: str,
        evidence_ids: list[str],
        *,
        expected_revision: int,
    ) -> ActionResult:
        self._check_revision(state, expected_revision)
        state.validate_content_references(self.registry)
        hypothesis = self.registry.get_hypothesis(hypothesis_id)
        if hypothesis.scene_id != state.current_scene:
            raise DomainError(
                "HYPOTHESIS_INVALID",
                "该推理不属于当前场景",
                details={
                    "hypothesis_id": hypothesis.id,
                    "current_scene": state.current_scene,
                },
            )
        if len(evidence_ids) != len(set(evidence_ids)):
            raise DomainError(
                "EVIDENCE_INVALID",
                "推理证据不能重复",
                details={"evidence_ids": evidence_ids},
            )
        if set(evidence_ids) != set(hypothesis.evidence_ids):
            raise DomainError(
                "EVIDENCE_INVALID",
                "证据不足以支持这项推理",
                details={
                    "evidence_ids": evidence_ids,
                    "required_evidence_ids": list(hypothesis.evidence_ids),
                },
            )
        if not set(evidence_ids).issubset(state.collected_fragments):
            raise DomainError(
                "EVIDENCE_NOT_COLLECTED",
                "仍有证据尚未取得",
                details={
                    "missing_evidence_ids": sorted(
                        set(evidence_ids) - set(state.collected_fragments)
                    ),
                },
            )
        if state.confirmed_hypotheses.get(state.current_scene) == hypothesis.id:
            return ActionResult(state=state.model_copy(deep=True))

        payload = state.model_dump(mode="python")
        payload["confirmed_hypotheses"][state.current_scene] = hypothesis.id
        payload["revision"] += 1
        next_state = GameState.model_validate(payload)
        next_state.validate_content_references(self.registry)
        return ActionResult(
            state=next_state,
            events=[
                PresentationEvent(
                    type="hypothesis.confirmed",
                    content_id=hypothesis.id,
                    payload={"evidence_ids": list(hypothesis.evidence_ids)},
                )
            ],
        )

    def record_choice(
        self,
        state: GameState,
        choice_id: str,
        *,
        expected_revision: int,
    ) -> ActionResult:
        self._check_revision(state, expected_revision)
        state.validate_content_references(self.registry)
        choice = self.registry.get_choice(choice_id)
        if choice.scene_id != state.current_scene:
            raise DomainError(
                "CHOICE_INVALID",
                "该选择不属于当前场景",
                details={
                    "choice_id": choice.id,
                    "current_scene": state.current_scene,
                },
            )

        previous_choice = state.butterfly_choices.get(choice.scene_id)
        if previous_choice == choice.id:
            return ActionResult(state=state.model_copy(deep=True))

        self._validate_choice_requirements(state, choice)

        if previous_choice is not None:
            raise DomainError(
                "CHOICE_INVALID",
                "当前场景已经完成关键选择",
                details={"previous_choice": previous_choice},
            )

        payload = state.model_dump(mode="python")
        next_revision = state.revision + 1
        payload["revision"] = next_revision
        payload["butterfly_choices"][choice.scene_id] = choice.id
        if choice.is_key:
            payload["key_choices"].append(
                {
                    "choice_id": choice.id,
                    "scene_id": choice.scene_id,
                    "made_at_revision": next_revision,
                }
            )

        events = [
            PresentationEvent(
                type="choice.recorded",
                content_id=choice.id,
            )
        ]
        for npc_id, change in choice.effects.trust_changes.items():
            payload["npc_trust"][npc_id] = max(
                0,
                min(100, payload["npc_trust"][npc_id] + change),
            )
        for fragment_id in choice.effects.reveal_fragments:
            if fragment_id in payload["revealed_fragments"]:
                continue
            payload["revealed_fragments"].append(fragment_id)
            fragment_state = payload["fragment_states"][fragment_id]
            fragment_state["status"] = "revealed"
            fragment_state["revealed"] = True
            fragment_state["collected"] = False
            events.append(
                PresentationEvent(
                    type="fragment.revealed",
                    content_id=fragment_id,
                )
            )
        if choice.effects.current_mood is not None:
            payload["current_mood"] = choice.effects.current_mood

        if choice.target_scene is not None:
            payload["current_scene"] = choice.target_scene
            if choice.target_scene not in payload["visited_scenes"]:
                payload["visited_scenes"].append(choice.target_scene)
            payload["chapter"] = list(self.registry.scenes).index(choice.target_scene) + 1
            events.append(
                PresentationEvent(
                    type="scene.entered",
                    content_id=choice.target_scene,
                )
            )

        next_state = GameState.model_validate(payload)
        next_state.validate_content_references(self.registry)
        return ActionResult(state=next_state, events=events)

    @staticmethod
    def _requirement_unmet(
        choice: ChoiceContent,
        requirement: FragmentCollectedRequirementContent
        | NpcTrustAtLeastRequirementContent,
    ) -> DomainError:
        return DomainError(
            "CHOICE_REQUIREMENT_UNMET",
            "尚未满足该选择的前置条件",
            details={
                "choice_id": choice.id,
                "requirement": requirement.model_dump(),
            },
        )

    def _validate_choice_requirements(
        self,
        state: GameState,
        choice: ChoiceContent,
    ) -> None:
        for requirement in choice.requirements:
            if isinstance(requirement, HypothesisConfirmedRequirementContent):
                if (
                    state.confirmed_hypotheses.get(choice.scene_id)
                    != requirement.hypothesis_id
                ):
                    raise DomainError(
                        "HYPOTHESIS_REQUIRED",
                        "请先用已经取得的证据完成本幕推理",
                        details={
                            "scene_id": choice.scene_id,
                            "hypothesis_id": requirement.hypothesis_id,
                        },
                    )
            elif isinstance(requirement, FragmentCollectedRequirementContent):
                if requirement.fragment_id not in state.collected_fragments:
                    raise self._requirement_unmet(choice, requirement)
            elif isinstance(requirement, NpcTrustAtLeastRequirementContent):
                if state.npc_trust[requirement.npc_id] < requirement.minimum:
                    raise self._requirement_unmet(choice, requirement)

    def evaluate_ending(self, state: GameState) -> EndingContent:
        state.validate_content_references(self.registry)
        collected_ratio = len(state.collected_fragments) / len(self.registry.fragments)
        key_choice_count = len(state.key_choices)

        for ending in sorted(
            self.registry.endings.values(),
            key=lambda candidate: candidate.priority,
            reverse=True,
        ):
            conditions = ending.conditions
            if collected_ratio < conditions.min_collected_ratio:
                continue
            if key_choice_count < conditions.min_key_choices:
                continue
            if any(
                state.npc_trust.get(npc_id, 0) < minimum
                for npc_id, minimum in conditions.required_npc_trust.items()
            ):
                continue
            return ending

        raise DomainError(
            "CONTENT_INVALID",
            "没有可匹配的结局，请检查结局内容配置",
        )
