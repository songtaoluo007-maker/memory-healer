"""Generate, validate, and promote seven Edge-managed fixed 1972 lines."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import importlib.metadata
import json
import re
import shutil
import subprocess
import sys
import wave
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from backend.content.models import VoiceProfileContent  # noqa: E402
from backend.content.registry import ContentRegistry  # noqa: E402
from backend.integrations.tts import TtsRequest, TtsService  # noqa: E402
from scripts.voice.validate_voice_assets import (  # noqa: E402
    GENERATOR_REVISION,
    MEDIA_TYPE,
    inspect_audio,
    validate_voice_assets,
)


POSTPROCESS_VERSION = 1


@dataclass(frozen=True, slots=True)
class GenerationPlan:
    line_id: str
    text: str
    subtitle_segments: tuple[str, ...]
    profile: VoiceProfileContent
    edge_voice: str
    edge_rate: str
    edge_pitch: str
    line_version: int
    profile_version: int


def _audio_duration_ms(path: Path) -> int:
    if path.suffix.lower() == ".wav":
        with wave.open(str(path), "rb") as audio:
            return round(audio.getnframes() / audio.getframerate() * 1_000)
    return inspect_audio(path).duration_ms


def build_manifest_entry(
    *,
    line_id: str,
    canonical_text: str,
    audio_path: Path,
    generator: str,
    generator_revision: str,
    model_id: str,
    line_version: int,
    profile_version: int,
    postprocess_version: int,
    approved: bool,
    filename: str | None = None,
    seed_provenance: str = "edge_tts_synthetic",
    duration_ms: int | None = None,
    integrated_lufs: float = -18.0,
    true_peak_dbfs: float = -1.2,
    cues: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    media_type = MEDIA_TYPE if audio_path.suffix.lower() == ".opus" else "audio/wav"
    return {
        "id": line_id,
        "filename": filename or audio_path.name,
        "media_type": media_type,
        "duration_ms": duration_ms or _audio_duration_ms(audio_path),
        "sha256": hashlib.sha256(audio_path.read_bytes()).hexdigest(),
        "text_sha256": hashlib.sha256(canonical_text.encode("utf-8")).hexdigest(),
        "integrated_lufs": round(integrated_lufs, 2),
        "true_peak_dbfs": round(true_peak_dbfs, 2),
        "generator": generator,
        "generator_revision": generator_revision,
        "model_id": model_id,
        "seed_provenance": seed_provenance,
        "line_version": line_version,
        "profile_version": profile_version,
        "postprocess_version": postprocess_version,
        "cues": cues or [],
        "approved": approved,
    }


def allocate_cues(
    subtitle_segments: tuple[str, ...] | list[str],
    duration_ms: int,
) -> list[dict[str, object]]:
    if duration_ms <= 0:
        raise ValueError("duration must be strictly positive")
    if not subtitle_segments or any(not segment for segment in subtitle_segments):
        raise ValueError("subtitle segments must be non-empty")
    weights = [
        sum(not character.isspace() for character in segment)
        for segment in subtitle_segments
    ]
    if any(weight <= 0 for weight in weights):
        raise ValueError("subtitle segments must contain visible characters")
    if duration_ms < len(subtitle_segments):
        raise ValueError("duration is too short for positive cue spans")

    total_weight = sum(weights)
    cues: list[dict[str, object]] = []
    start_ms = 0
    cumulative_weight = 0
    for index, (segment, weight) in enumerate(zip(subtitle_segments, weights)):
        cumulative_weight += weight
        end_ms = (
            duration_ms
            if index == len(subtitle_segments) - 1
            else round(duration_ms * cumulative_weight / total_weight)
        )
        end_ms = max(end_ms, start_ms + 1)
        remaining = len(subtitle_segments) - index - 1
        end_ms = min(end_ms, duration_ms - remaining)
        cues.append({"start_ms": start_ms, "end_ms": end_ms, "text": segment})
        start_ms = end_ms
    return cues


def _run(command: list[str]) -> None:
    result = subprocess.run(
        command,
        capture_output=True,
        check=False,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        detail = result.stderr.strip().splitlines()
        last_line = detail[-1] if detail else f"exit {result.returncode}"
        raise RuntimeError(f"{command[0]} failed: {last_line}")


def _encode_normalized_opus(
    raw_path: Path,
    output_path: Path,
    attenuation_db: float,
) -> None:
    audio_filter = "loudnorm=I=-18:TP=-1:LRA=7"
    if attenuation_db > 0:
        audio_filter += f",volume=-{attenuation_db:.2f}dB"
    _run(
        [
            "ffmpeg",
            "-hide_banner",
            "-nostdin",
            "-y",
            "-i",
            str(raw_path),
            "-map_metadata",
            "-1",
            "-fflags",
            "+bitexact",
            "-flags:a",
            "+bitexact",
            "-af",
            audio_filter,
            "-ac",
            "1",
            "-ar",
            "48000",
            "-c:a",
            "libopus",
            "-b:a",
            "80k",
            "-serial_offset",
            "0",
            str(output_path),
        ]
    )


def postprocess_audio(
    raw_path: Path,
    output_path: Path,
    *,
    media_inspector: Callable[[Path], object] = inspect_audio,
    encoder: Callable[[Path, Path, float], None] = _encode_normalized_opus,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = output_path.with_suffix(".tmp.opus")
    attenuation_db = 0.0
    try:
        for _ in range(3):
            temporary_path.unlink(missing_ok=True)
            encoder(raw_path, temporary_path, attenuation_db)
            media = media_inspector(temporary_path)
            true_peak_dbfs = float(getattr(media, "true_peak_dbfs"))
            if true_peak_dbfs <= -1.0:
                temporary_path.replace(output_path)
                return
            attenuation_db = round(
                attenuation_db + true_peak_dbfs - (-1.0) + 0.05,
                2,
            )
        raise RuntimeError("Opus true peak remains above -1 dBTP after correction")
    finally:
        temporary_path.unlink(missing_ok=True)


def _slug(line_id: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", line_id.lower()).strip("-")


def _scene_line_ids(registry: ContentRegistry, scene_id: str) -> set[str]:
    scene = registry.scenes.get(scene_id)
    if scene is None:
        raise ValueError(f"unknown scene: {scene_id}")
    line_ids = {
        line_id
        for line_id in (
            scene.transition_in_voice_line_id,
            scene.transition_out_voice_line_id,
        )
        if line_id
    }
    for npc_id in scene.npcs:
        line_id = registry.npcs[npc_id].initial_voice_line_id
        if line_id:
            line_ids.add(line_id)
    for fragment_id in scene.fragments:
        line_id = registry.fragments[fragment_id].memory_voice_line_id
        if line_id:
            line_ids.add(line_id)
    for hypothesis in registry.hypotheses.values():
        if hypothesis.scene_id == scene_id and hypothesis.resolution_voice_line_id:
            line_ids.add(hypothesis.resolution_voice_line_id)
    return line_ids


def build_generation_plan(
    repository_root: Path,
    scene_id: str,
) -> tuple[GenerationPlan, ...]:
    if scene_id != "scene_1972":
        raise ValueError("this pilot may generate only scene_1972 fixed assets")
    registry = ContentRegistry.load(repository_root / "backend" / "data")
    allowed_line_ids = _scene_line_ids(registry, scene_id)
    plans = tuple(
        GenerationPlan(
            line_id=line.id,
            text=line.text,
            subtitle_segments=line.subtitle_segments,
            profile=registry.voice_profiles[line.speaker_profile],
            edge_voice=registry.voice_profiles[
                line.speaker_profile
            ].provider.edge_voice,
            edge_rate=registry.voice_profiles[line.speaker_profile].provider.edge_rate,
            edge_pitch=registry.voice_profiles[
                line.speaker_profile
            ].provider.edge_pitch,
            line_version=line.version,
            profile_version=registry.voice_profiles[line.speaker_profile].version,
        )
        for line in registry.voice_lines.values()
        if line.delivery == "pre_generated" and line.id in allowed_line_ids
    )
    if len(plans) != 7:
        raise RuntimeError(
            f"scene_1972 must resolve to exactly seven fixed lines, got {len(plans)}"
        )
    return plans


async def generate_candidates(
    *,
    scene_id: str,
    repository_root: Path,
) -> Path:
    installed_revision = importlib.metadata.version("edge-tts")
    if installed_revision != GENERATOR_REVISION:
        raise RuntimeError(
            f"edge-tts {GENERATOR_REVISION} is required, got {installed_revision}"
        )
    plans = build_generation_plan(repository_root, scene_id)
    render_root = repository_root / ".codex-run" / "voice-renders"
    edge_cache = render_root / "edge-cache"
    raw_root = render_root / "raw"
    fixed_root = render_root / "fixed"
    raw_root.mkdir(parents=True, exist_ok=True)
    fixed_root.mkdir(parents=True, exist_ok=True)
    service = TtsService(
        edge_cache,
        max_concurrency=1,
        max_cache_files=7,
        max_cache_bytes=256 * 1024 * 1024,
    )

    manifest: list[dict[str, object]] = []
    for plan in plans:
        result = await service.synthesize(
            TtsRequest(
                text=plan.text,
                voice=plan.edge_voice,
                rate=plan.edge_rate,
                pitch=plan.edge_pitch,
            )
        )
        slug = _slug(plan.line_id)
        raw_path = raw_root / f"{slug}.mp3"
        output_path = fixed_root / f"{slug}.opus"
        shutil.copy2(edge_cache / result.filename, raw_path)
        postprocess_audio(raw_path, output_path)
        media = inspect_audio(output_path)
        manifest.append(
            build_manifest_entry(
                line_id=plan.line_id,
                canonical_text=plan.text,
                audio_path=output_path,
                filename=f"fixed/{output_path.name}",
                generator="edge_tts",
                generator_revision=GENERATOR_REVISION,
                model_id=plan.edge_voice,
                seed_provenance="edge_tts_synthetic",
                line_version=plan.line_version,
                profile_version=plan.profile_version,
                postprocess_version=POSTPROCESS_VERSION,
                duration_ms=media.duration_ms,
                integrated_lufs=media.integrated_lufs,
                true_peak_dbfs=media.true_peak_dbfs,
                cues=allocate_cues(plan.subtitle_segments, media.duration_ms),
                approved=False,
            )
        )

    candidate_manifest = render_root / "voice_assets.candidate.json"
    candidate_manifest.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return candidate_manifest


def promote_candidates(*, repository_root: Path) -> None:
    data_root = repository_root / "backend" / "data"
    render_root = repository_root / ".codex-run" / "voice-renders"
    candidate_manifest = render_root / "voice_assets.candidate.json"
    manifest = json.loads(candidate_manifest.read_text(encoding="utf-8"))
    if (
        not isinstance(manifest, list)
        or len(manifest) != 7
        or any(not isinstance(asset, dict) for asset in manifest)
    ):
        raise ValueError("candidate manifest must contain exactly seven assets")

    staging_root = render_root / "promotion-staging"
    resolved_staging = staging_root.resolve()
    resolved_render = render_root.resolve()
    try:
        resolved_staging.relative_to(resolved_render)
    except ValueError as exc:  # pragma: no cover - paths are constants
        raise RuntimeError("unsafe promotion staging path") from exc
    if staging_root.exists():
        shutil.rmtree(staging_root)
    staging_public = staging_root / "voice_public"
    (staging_public / "fixed").mkdir(parents=True)

    approved_manifest: list[dict[str, object]] = []
    for raw_asset in manifest:
        asset = dict(raw_asset)
        if asset.get("approved") is not False:
            raise ValueError("candidate manifest entries must remain unapproved")
        filename = asset.get("filename")
        if not isinstance(filename, str) or Path(filename).parent.as_posix() != "fixed":
            raise ValueError("candidate asset filename must stay under fixed/")
        source = render_root / filename
        if not source.is_file():
            raise FileNotFoundError(f"candidate asset is missing: {source}")
        shutil.copy2(source, staging_public / filename)
        asset["approved"] = True
        approved_manifest.append(asset)

    staging_manifest = staging_root / "voice_assets.approved.json"
    staging_manifest.write_text(
        json.dumps(approved_manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    issues = validate_voice_assets(
        manifest_path=staging_manifest,
        lines_path=data_root / "voice_lines.json",
        profiles_path=data_root / "voice_profiles.json",
        public_root=staging_public,
    )
    if issues:
        rendered = "\n".join(issue.render() for issue in issues)
        raise RuntimeError(f"promotion validation failed:\n{rendered}")

    runtime_fixed = data_root / "voice_public" / "fixed"
    runtime_fixed.mkdir(parents=True, exist_ok=True)
    for path in runtime_fixed.iterdir():
        if path.is_file():
            path.unlink()
    for source in sorted((staging_public / "fixed").iterdir()):
        shutil.copy2(source, runtime_fixed / source.name)
    temporary_manifest = data_root / "voice_assets.json.tmp"
    temporary_manifest.write_text(
        json.dumps(approved_manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary_manifest.replace(data_root / "voice_assets.json")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scene", default="scene_1972")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--candidate-mode", action="store_true")
    mode.add_argument("--promote", action="store_true")
    return parser


def main(
    argv: list[str] | None = None,
    *,
    repository_root: Path = REPOSITORY_ROOT,
) -> int:
    args = build_parser().parse_args(argv)
    if args.scene != "scene_1972":
        raise ValueError("this pilot may generate only scene_1972 fixed assets")
    if args.dry_run:
        plans = build_generation_plan(repository_root, args.scene)
        print(f"{len(plans)} Edge fixed lines planned; no network calls made.")
    elif args.candidate_mode:
        candidate_manifest = asyncio.run(
            generate_candidates(
                scene_id=args.scene,
                repository_root=repository_root,
            )
        )
        print(f"Candidate manifest written: {candidate_manifest}")
    else:
        promote_candidates(repository_root=repository_root)
        print("Approved 1972 assets promoted after staging validation.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
