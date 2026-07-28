from __future__ import annotations

import json
from hashlib import sha256
from collections.abc import Mapping
from pathlib import Path
from types import MappingProxyType
from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

from backend.domain.errors import DomainError

from .models import (
    ChoiceContent,
    EndingContent,
    FragmentContent,
    HotspotContent,
    HypothesisContent,
    NpcContent,
    SceneContent,
    VoiceAssetContent,
    VoiceLineContent,
    VoiceProfileContent,
)


ContentItem = TypeVar("ContentItem", bound=BaseModel)

EDGE_TTS_REVISION = "7.2.8"


class ContentValidationError(DomainError):
    """Raised when canonical content cannot be safely loaded."""


class ContentRegistry:
    def __init__(
        self,
        *,
        scenes: Mapping[str, SceneContent],
        npcs: Mapping[str, NpcContent],
        fragments: Mapping[str, FragmentContent],
        hotspots: Mapping[str, HotspotContent],
        choices: Mapping[str, ChoiceContent],
        hypotheses: Mapping[str, HypothesisContent],
        endings: Mapping[str, EndingContent],
        voice_profiles: Mapping[str, VoiceProfileContent],
        voice_lines: Mapping[str, VoiceLineContent],
        voice_assets: Mapping[str, VoiceAssetContent],
    ) -> None:
        self.scenes = MappingProxyType(dict(scenes))
        self.npcs = MappingProxyType(dict(npcs))
        self.fragments = MappingProxyType(dict(fragments))
        self.hotspots = MappingProxyType(dict(hotspots))
        self.choices = MappingProxyType(dict(choices))
        self.hypotheses = MappingProxyType(dict(hypotheses))
        self.endings = MappingProxyType(dict(endings))
        self.voice_profiles = MappingProxyType(dict(voice_profiles))
        self.voice_lines = MappingProxyType(dict(voice_lines))
        self.voice_assets = MappingProxyType(dict(voice_assets))

    @classmethod
    def load(cls, data_dir: Path) -> "ContentRegistry":
        filenames = {
            "scenes": "scenes.json",
            "npcs": "npcs.json",
            "fragments": "fragments.json",
            "hotspots": "hotspots.json",
            "choices": "choices.json",
            "hypotheses": "hypotheses.json",
            "endings": "endings.json",
            "voice_profiles": "voice_profiles.json",
            "voice_lines": "voice_lines.json",
            "voice_assets": "voice_assets.json",
        }
        try:
            documents = {
                name: json.loads((data_dir / filename).read_text(encoding="utf-8"))
                for name, filename in filenames.items()
            }
        except (OSError, json.JSONDecodeError) as exc:
            raise ContentValidationError(
                "CONTENT_INVALID",
                "内容文件无法读取或不是合法 JSON",
                details={"reason": str(exc)},
            ) from exc
        return cls.from_documents(documents)

    @classmethod
    def from_documents(cls, documents: Mapping[str, object]) -> "ContentRegistry":
        try:
            scenes = cls._parse_mapping(documents["scenes"], SceneContent, "scenes")
            npcs = cls._parse_mapping(documents["npcs"], NpcContent, "npcs")
            fragments = cls._parse_mapping(
                documents["fragments"], FragmentContent, "fragments"
            )
            hotspots = cls._parse_list(documents["hotspots"], HotspotContent, "hotspots")
            choices = cls._parse_list(documents["choices"], ChoiceContent, "choices")
            hypotheses = cls._parse_list(
                documents["hypotheses"],
                HypothesisContent,
                "hypotheses",
            )
            endings = cls._parse_list(documents["endings"], EndingContent, "endings")
            voice_profiles = cls._parse_list(
                documents["voice_profiles"], VoiceProfileContent, "voice_profiles"
            )
            voice_lines = cls._parse_list(
                documents["voice_lines"], VoiceLineContent, "voice_lines"
            )
            voice_assets = cls._parse_list(
                documents["voice_assets"], VoiceAssetContent, "voice_assets"
            )
        except KeyError as exc:
            raise ContentValidationError(
                "CONTENT_DOCUMENT_MISSING",
                f"缺少内容文档：{exc.args[0]}",
            ) from exc
        except ValidationError as exc:
            raise ContentValidationError(
                "CONTENT_SCHEMA_INVALID",
                "内容字段不符合结构定义",
                details={"errors": exc.errors(include_url=False)},
            ) from exc

        registry = cls(
            scenes=scenes,
            npcs=npcs,
            fragments=fragments,
            hotspots=hotspots,
            choices=choices,
            hypotheses=hypotheses,
            endings=endings,
            voice_profiles=voice_profiles,
            voice_lines=voice_lines,
            voice_assets=voice_assets,
        )
        registry.validate()
        return registry

    @staticmethod
    def _parse_mapping(
        document: object,
        model: type[ContentItem],
        document_name: str,
    ) -> dict[str, ContentItem]:
        if not isinstance(document, dict):
            raise ContentValidationError(
                "CONTENT_SCHEMA_INVALID",
                f"{document_name} 必须是对象",
            )

        parsed: dict[str, ContentItem] = {}
        for key, raw_item in document.items():
            item = model.model_validate(raw_item)
            if item.id in parsed:
                raise ContentValidationError(
                    "CONTENT_DUPLICATE_ID",
                    f"{document_name} 存在重复 ID：{item.id}",
                )
            if key != item.id:
                if item.id in {
                    raw.get("id")
                    for raw in document.values()
                    if isinstance(raw, dict) and raw is not raw_item
                }:
                    raise ContentValidationError(
                        "CONTENT_DUPLICATE_ID",
                        f"{document_name} 存在重复 ID：{item.id}",
                    )
                raise ContentValidationError(
                    "CONTENT_KEY_ID_MISMATCH",
                    f"{document_name} 键 {key} 与内容 ID {item.id} 不一致",
                )
            parsed[item.id] = item
        return parsed

    @staticmethod
    def _parse_list(
        document: object,
        model: type[ContentItem],
        document_name: str,
    ) -> dict[str, ContentItem]:
        if not isinstance(document, list):
            raise ContentValidationError(
                "CONTENT_SCHEMA_INVALID",
                f"{document_name} 必须是数组",
            )

        parsed: dict[str, ContentItem] = {}
        for raw_item in document:
            item = model.model_validate(raw_item)
            if item.id in parsed:
                raise ContentValidationError(
                    "CONTENT_DUPLICATE_ID",
                    f"{document_name} 存在重复 ID：{item.id}",
                )
            parsed[item.id] = item
        return parsed

    @staticmethod
    def _raise(code: str, message: str, **details: Any) -> None:
        raise ContentValidationError(code, message, details=details)

    def validate(self) -> None:
        for scene in self.scenes.values():
            if not scene.fallback_asset.strip():
                self._raise(
                    "SCENE_FALLBACK_ASSET_REQUIRED",
                    f"场景 {scene.id} 缺少回退资产",
                    scene_id=scene.id,
                )
            for npc_id in scene.npcs:
                npc = self.npcs.get(npc_id)
                if npc is None:
                    self._raise(
                        "SCENE_NPC_NOT_FOUND",
                        f"场景 {scene.id} 引用了不存在的 NPC {npc_id}",
                    )
                if npc.scene != scene.id:
                    self._raise(
                        "SCENE_NPC_SCENE_MISMATCH",
                        f"NPC {npc_id} 不属于场景 {scene.id}",
                    )
            for fragment_id in scene.fragments:
                fragment = self.fragments.get(fragment_id)
                if fragment is None:
                    self._raise(
                        "SCENE_FRAGMENT_NOT_FOUND",
                        f"场景 {scene.id} 引用了不存在的碎片 {fragment_id}",
                    )
                if fragment.scene != scene.id:
                    self._raise(
                        "SCENE_FRAGMENT_SCENE_MISMATCH",
                        f"碎片 {fragment_id} 不属于场景 {scene.id}",
                    )
            for target_scene in scene.exits.values():
                if target_scene not in self.scenes:
                    self._raise(
                        "SCENE_EXIT_NOT_FOUND",
                        f"场景 {scene.id} 的出口指向不存在场景 {target_scene}",
                    )

        for npc in self.npcs.values():
            if npc.scene not in self.scenes:
                self._raise(
                    "NPC_SCENE_NOT_FOUND",
                    f"NPC {npc.id} 的场景不存在",
                )
            for fragment_id in npc.fragments_to_reveal:
                fragment = self.fragments.get(fragment_id)
                if fragment is None:
                    self._raise(
                        "NPC_FRAGMENT_NOT_FOUND",
                        f"NPC {npc.id} 引用了不存在的碎片 {fragment_id}",
                    )
                if fragment.scene != npc.scene:
                    self._raise(
                        "NPC_FRAGMENT_SCENE_MISMATCH",
                        f"NPC {npc.id} 不能揭露其他场景碎片 {fragment_id}",
                    )
            if npc.voice_profile_id not in self.voice_profiles:
                self._raise(
                    "NPC_VOICE_PROFILE_NOT_FOUND",
                    f"NPC {npc.id} 引用了不存在的声音档案 {npc.voice_profile_id}",
                )

        hotspot_fragments: set[str] = set()
        for hotspot in self.hotspots.values():
            if hotspot.scene_id not in self.scenes:
                self._raise(
                    "HOTSPOT_SCENE_NOT_FOUND",
                    f"热区 {hotspot.id} 的场景不存在",
                )
            if hotspot.fragment_id is not None:
                fragment = self.fragments.get(hotspot.fragment_id)
                if fragment is None:
                    self._raise(
                        "HOTSPOT_FRAGMENT_NOT_FOUND",
                        f"热区 {hotspot.id} 的碎片不存在",
                    )
                if fragment.scene != hotspot.scene_id:
                    self._raise(
                        "HOTSPOT_FRAGMENT_SCENE_MISMATCH",
                        f"热区 {hotspot.id} 引用了其他场景碎片",
                    )
                hotspot_fragments.add(fragment.id)
            if hotspot.npc_id is not None:
                npc = self.npcs.get(hotspot.npc_id)
                if npc is None:
                    self._raise(
                        "HOTSPOT_NPC_NOT_FOUND",
                        f"热区 {hotspot.id} 的 NPC 不存在",
                    )
                if npc.scene != hotspot.scene_id:
                    self._raise(
                        "HOTSPOT_NPC_SCENE_MISMATCH",
                        f"热区 {hotspot.id} 引用了其他场景 NPC",
                    )

        missing_hotspots = set(self.fragments) - hotspot_fragments
        if missing_hotspots:
            self._raise(
                "FRAGMENT_HOTSPOT_REQUIRED",
                "每个碎片必须有规范化热区入口",
                fragment_ids=sorted(missing_hotspots),
            )

        for choice in self.choices.values():
            if choice.scene_id not in self.scenes:
                self._raise(
                    "CHOICE_SCENE_NOT_FOUND",
                    f"选择 {choice.id} 的源场景不存在",
                )
            if choice.target_scene is not None and choice.target_scene not in self.scenes:
                self._raise(
                    "CHOICE_TARGET_SCENE_NOT_FOUND",
                    f"选择 {choice.id} 的目标场景不存在",
                )
            for npc_id in choice.effects.trust_changes:
                if npc_id not in self.npcs:
                    self._raise(
                        "CHOICE_NPC_NOT_FOUND",
                        f"选择 {choice.id} 引用了不存在的 NPC {npc_id}",
                    )
            for fragment_id in choice.effects.reveal_fragments:
                if fragment_id not in self.fragments:
                    self._raise(
                        "CHOICE_FRAGMENT_NOT_FOUND",
                        f"选择 {choice.id} 引用了不存在的碎片 {fragment_id}",
                    )
        for hypothesis in self.hypotheses.values():
            if hypothesis.scene_id not in self.scenes:
                self._raise(
                    "HYPOTHESIS_SCENE_NOT_FOUND",
                    f"推理命题 {hypothesis.id} 的场景不存在",
                )
            if len(hypothesis.evidence_ids) != len(set(hypothesis.evidence_ids)):
                self._raise(
                    "HYPOTHESIS_EVIDENCE_DUPLICATE",
                    f"推理命题 {hypothesis.id} 的证据不能重复",
                )
            for fragment_id in hypothesis.evidence_ids:
                fragment = self.fragments.get(fragment_id)
                if fragment is None:
                    self._raise(
                        "HYPOTHESIS_FRAGMENT_NOT_FOUND",
                        f"推理命题 {hypothesis.id} 引用了不存在的碎片 {fragment_id}",
                    )
                if fragment.scene != hypothesis.scene_id:
                    self._raise(
                        "HYPOTHESIS_FRAGMENT_SCENE_MISMATCH",
                        f"推理命题 {hypothesis.id} 引用了其他场景碎片 {fragment_id}",
                    )

        key_choice_count = sum(choice.is_key for choice in self.choices.values())
        for ending in self.endings.values():
            if ending.conditions.min_key_choices > key_choice_count:
                self._raise(
                    "ENDING_KEY_CHOICES_UNREACHABLE",
                    f"结局 {ending.id} 所需关键选择数量不可达",
                )
            for npc_id, trust in ending.conditions.required_npc_trust.items():
                if npc_id not in self.npcs:
                    self._raise(
                        "ENDING_NPC_NOT_FOUND",
                        f"结局 {ending.id} 引用了不存在的 NPC {npc_id}",
                    )
                if not 0 <= trust <= 100:
                    self._raise(
                        "ENDING_TRUST_INVALID",
                        f"结局 {ending.id} 的信任阈值无效",
                    )

        self._validate_voice_content()

    def _validate_voice_content(self) -> None:
        for line in self.voice_lines.values():
            if line.speaker_profile not in self.voice_profiles:
                self._raise(
                    "VOICE_LINE_PROFILE_NOT_FOUND",
                    f"语音行 {line.id} 引用了不存在的声音档案 {line.speaker_profile}",
                )
            source_text = self._voice_source_text(line.source_ref)
            if line.text != source_text:
                self._raise(
                    "VOICE_LINE_TEXT_STALE",
                    f"语音行 {line.id} 与规范内容不一致",
                    line_id=line.id,
                    source_ref=line.source_ref,
                )
            if line.delivery == "pre_generated" and (
                not line.subtitle_segments
                or "".join(line.subtitle_segments) != line.text
            ):
                self._raise(
                    "VOICE_LINE_SUBTITLE_MISMATCH",
                    f"预生成语音行 {line.id} 的字幕不能重建原文",
                    line_id=line.id,
                )

        for asset in self.voice_assets.values():
            line = self.voice_lines.get(asset.id)
            if line is None:
                self._raise(
                    "VOICE_ASSET_LINE_NOT_FOUND",
                    f"语音资产 {asset.id} 引用了不存在的语音行",
                )
            if not asset.approved:
                self._raise(
                    "VOICE_ASSET_NOT_APPROVED",
                    f"语音资产 {asset.id} 未获准进入运行时清单",
                )
            if asset.generator_revision != EDGE_TTS_REVISION:
                self._raise(
                    "VOICE_ASSET_GENERATOR_REVISION_INVALID",
                    f"语音资产 {asset.id} 的生成器版本不受信任",
                )
            profile = self.voice_profiles[line.speaker_profile]
            if asset.model_id != profile.provider.edge_voice:
                self._raise(
                    "VOICE_ASSET_MODEL_ID_INVALID",
                    f"语音资产 {asset.id} 的模型标识不受信任",
                )
            if asset.line_version != line.version:
                self._raise(
                    "VOICE_ASSET_LINE_VERSION_MISMATCH",
                    f"语音资产 {asset.id} 的语音行版本不匹配",
                )
            if asset.profile_version != profile.version:
                self._raise(
                    "VOICE_ASSET_PROFILE_VERSION_MISMATCH",
                    f"语音资产 {asset.id} 的声音档案版本不匹配",
                )
            if asset.seed_provenance != profile.seed_provenance:
                self._raise(
                    "VOICE_ASSET_SEED_PROVENANCE_MISMATCH",
                    f"语音资产 {asset.id} 的种子来源不匹配",
                )
            text_sha256 = sha256(line.text.encode("utf-8")).hexdigest()
            if asset.text_sha256 != text_sha256:
                self._raise(
                    "VOICE_ASSET_TEXT_HASH_MISMATCH",
                    f"语音资产 {asset.id} 的文本摘要不匹配",
                )

        for scene in self.scenes.values():
            self._validate_voice_reference(
                scene.transition_in_voice_line_id,
                f"scene:{scene.id}.transition_in",
            )
            self._validate_voice_reference(
                scene.transition_out_voice_line_id,
                f"scene:{scene.id}.transition_out",
            )
        for npc in self.npcs.values():
            self._validate_voice_reference(
                npc.initial_voice_line_id,
                f"npc:{npc.id}.fallback_dialogue",
            )
        for fragment in self.fragments.values():
            self._validate_voice_reference(
                fragment.memory_voice_line_id,
                f"fragment:{fragment.id}.memory_text",
            )
        for hypothesis in self.hypotheses.values():
            self._validate_voice_reference(
                hypothesis.resolution_voice_line_id,
                f"hypothesis:{hypothesis.id}.resolution",
            )
        for ending in self.endings.values():
            self._validate_voice_reference(
                ending.voice_line_id,
                f"ending:{ending.id}.description",
            )

    def _validate_voice_reference(self, line_id: str | None, source_ref: str) -> None:
        if line_id is None:
            return
        line = self.voice_lines.get(line_id)
        if line is None:
            self._raise(
                "VOICE_LINE_NOT_FOUND",
                f"规范内容引用了不存在的语音行 {line_id}",
            )
        if line.source_ref != source_ref:
            self._raise(
                "VOICE_LINE_SOURCE_MISMATCH",
                f"语音行 {line_id} 未引用规范内容 {source_ref}",
            )

    def _voice_source_text(self, source_ref: str) -> str:
        try:
            source_type, source_path = source_ref.split(":", maxsplit=1)
            source_id, field_name = source_path.rsplit(".", maxsplit=1)
            sources: Mapping[str, Mapping[str, BaseModel]] = {
                "scene": self.scenes,
                "npc": self.npcs,
                "fragment": self.fragments,
                "hypothesis": self.hypotheses,
                "ending": self.endings,
            }
            source = sources[source_type][source_id]
            text = getattr(source, field_name)
        except (AttributeError, KeyError, ValueError) as exc:
            self._raise(
                "VOICE_LINE_SOURCE_NOT_FOUND",
                f"语音行引用不存在的规范内容 {source_ref}",
            )
            raise AssertionError("unreachable") from exc
        if not isinstance(text, str):
            self._raise(
                "VOICE_LINE_SOURCE_INVALID",
                f"语音行引用的规范内容不是文本 {source_ref}",
            )
        return text

    def get_scene(self, scene_id: str) -> SceneContent:
        try:
            return self.scenes[scene_id]
        except KeyError as exc:
            raise DomainError("SCENE_NOT_FOUND", f"场景不存在：{scene_id}") from exc

    def get_npc(self, npc_id: str) -> NpcContent:
        try:
            return self.npcs[npc_id]
        except KeyError as exc:
            raise DomainError("NPC_NOT_FOUND", f"NPC 不存在：{npc_id}") from exc

    def get_fragment(self, fragment_id: str) -> FragmentContent:
        try:
            return self.fragments[fragment_id]
        except KeyError as exc:
            raise DomainError(
                "FRAGMENT_NOT_FOUND", f"碎片不存在：{fragment_id}"
            ) from exc

    def get_hotspot(self, hotspot_id: str) -> HotspotContent:
        try:
            return self.hotspots[hotspot_id]
        except KeyError as exc:
            raise DomainError("HOTSPOT_INVALID", f"热区不存在：{hotspot_id}") from exc

    def get_choice(self, choice_id: str) -> ChoiceContent:
        try:
            return self.choices[choice_id]
        except KeyError as exc:
            raise DomainError("CHOICE_INVALID", f"选择不存在：{choice_id}") from exc

    def get_hypothesis(self, hypothesis_id: str) -> HypothesisContent:
        try:
            return self.hypotheses[hypothesis_id]
        except KeyError as exc:
            raise DomainError(
                "HYPOTHESIS_INVALID",
                f"推理命题不存在：{hypothesis_id}",
            ) from exc

    def get_voice_profile(self, profile_id: str) -> VoiceProfileContent:
        try:
            return self.voice_profiles[profile_id]
        except KeyError as exc:
            raise DomainError("VOICE_PROFILE_NOT_FOUND", f"声音档案不存在：{profile_id}") from exc

    def get_voice_line(self, line_id: str) -> VoiceLineContent:
        try:
            return self.voice_lines[line_id]
        except KeyError as exc:
            raise DomainError("VOICE_LINE_NOT_FOUND", f"语音行不存在：{line_id}") from exc

    def get_voice_asset(self, line_id: str) -> VoiceAssetContent | None:
        asset = self.voice_assets.get(line_id)
        return asset if asset is None or asset.approved else None
