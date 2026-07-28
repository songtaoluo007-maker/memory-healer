"""Validate approved Edge-generated fixed voice assets."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from backend.integrations.tts import SUPPORTED_VOICES  # noqa: E402


GENERATOR_REVISION = "7.2.8"
MEDIA_TYPE = "audio/ogg; codecs=opus"
LOUDNESS_MIN = -19.0
LOUDNESS_MAX = -17.0
TRUE_PEAK_MAX = -1.0
MEASUREMENT_TOLERANCE = 0.35
DURATION_TOLERANCE_MS = 25


@dataclass(frozen=True, slots=True)
class MediaInfo:
    duration_ms: int
    channels: int
    sample_rate: int
    codec_name: str
    integrated_lufs: float
    true_peak_dbfs: float


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    line_id: str
    code: str
    path: Path

    def render(self) -> str:
        return f"line_id={self.line_id} reason={self.code} path={self.path}"


def validate_seed_provenance(provenance: str) -> None:
    if provenance != "edge_tts_synthetic":
        raise ValueError(
            "synthetic seed provenance must be edge_tts_synthetic; "
            "human, operator-supplied, and unknown sources are prohibited"
        )


def _run(command: list[str]) -> subprocess.CompletedProcess[str]:
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
    return result


def inspect_audio(path: Path) -> MediaInfo:
    probe = _run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "a:0",
            "-show_entries",
            "stream=codec_name,channels,sample_rate:format=duration",
            "-of",
            "json",
            str(path),
        ]
    )
    payload = json.loads(probe.stdout)
    streams = payload.get("streams", [])
    if len(streams) != 1:
        raise RuntimeError("audio must contain exactly one audio stream")
    stream = streams[0]
    duration = payload.get("format", {}).get("duration")
    if duration is None:
        raise RuntimeError("audio duration is unavailable")

    loudness = _run(
        [
            "ffmpeg",
            "-hide_banner",
            "-nostats",
            "-i",
            str(path),
            "-af",
            "loudnorm=I=-18:TP=-1:LRA=7:print_format=json",
            "-f",
            "null",
            "-",
        ]
    )
    matches = re.findall(r'\{\s*"input_i".*?\}', loudness.stderr, re.DOTALL)
    if not matches:
        raise RuntimeError("FFmpeg loudness measurement is unavailable")
    measured = json.loads(matches[-1])
    return MediaInfo(
        duration_ms=round(float(duration) * 1_000),
        channels=int(stream["channels"]),
        sample_rate=int(stream["sample_rate"]),
        codec_name=str(stream["codec_name"]),
        integrated_lufs=float(measured["input_i"]),
        true_peak_dbfs=float(measured["input_tp"]),
    )


def _load_list(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list) or any(
        not isinstance(item, dict) for item in payload
    ):
        raise ValueError(f"{path} must contain a JSON array of objects")
    return payload


def _issue(
    issues: list[ValidationIssue],
    line_id: object,
    code: str,
    path: Path,
) -> None:
    issues.append(ValidationIssue(str(line_id or "<unknown>"), code, path))


def _safe_asset_path(public_root: Path, filename: object) -> Path | None:
    if not isinstance(filename, str) or not filename.strip():
        return None
    root = public_root.resolve()
    candidate = (root / filename).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        return None
    return candidate


def _validate_cues(
    *,
    issues: list[ValidationIssue],
    line_id: str,
    asset_path: Path,
    cues: object,
    duration_ms: int,
    line: dict[str, Any],
) -> None:
    if not isinstance(cues, list) or not cues:
        _issue(issues, line_id, "CUES_MISSING", asset_path)
        return
    previous_start = -1
    previous_end = 0
    cue_text_parts: list[str] = []
    for cue in cues:
        if not isinstance(cue, dict):
            _issue(issues, line_id, "CUE_SCHEMA_INVALID", asset_path)
            continue
        start = cue.get("start_ms")
        end = cue.get("end_ms")
        text = cue.get("text")
        if (
            not isinstance(start, int)
            or not isinstance(end, int)
            or not isinstance(text, str)
        ):
            _issue(issues, line_id, "CUE_SCHEMA_INVALID", asset_path)
            continue
        cue_text_parts.append(text)
        if start < 0 or end <= start:
            _issue(issues, line_id, "CUE_SPAN_INVALID", asset_path)
        if start < previous_start:
            _issue(issues, line_id, "CUE_ORDER_INVALID", asset_path)
        elif start < previous_end:
            _issue(issues, line_id, "CUE_OVERLAP", asset_path)
        if end > duration_ms:
            _issue(issues, line_id, "CUE_DURATION_EXCEEDED", asset_path)
        previous_start = start
        previous_end = end

    subtitle_segments = line.get("subtitle_segments")
    subtitle_text = (
        "".join(subtitle_segments)
        if isinstance(subtitle_segments, list)
        and all(isinstance(item, str) for item in subtitle_segments)
        else ""
    )
    canonical_text = line.get("text")
    cue_text = "".join(cue_text_parts)
    if (
        not isinstance(canonical_text, str)
        or cue_text != subtitle_text
        or subtitle_text != canonical_text
    ):
        _issue(issues, line_id, "CUE_TEXT_MISMATCH", asset_path)


def validate_voice_assets(
    *,
    manifest_path: Path,
    lines_path: Path,
    profiles_path: Path,
    public_root: Path,
    media_inspector: Callable[[Path], MediaInfo] = inspect_audio,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    try:
        manifest = _load_list(manifest_path)
        lines_list = _load_list(lines_path)
        profiles_list = _load_list(profiles_path)
    except (OSError, ValueError, json.JSONDecodeError):
        _issue(issues, "<manifest>", "MANIFEST_INVALID", manifest_path)
        return issues

    lines = {
        str(line.get("id")): line
        for line in lines_list
        if isinstance(line.get("id"), str)
    }
    profiles = {
        str(profile.get("id")): profile
        for profile in profiles_list
        if isinstance(profile.get("id"), str)
    }

    seen_ids: set[str] = set()
    seen_filenames: set[str] = set()
    expected_asset_paths: set[Path] = set()
    for asset in manifest:
        line_id = str(asset.get("id") or "<unknown>")
        filename = asset.get("filename")
        asset_path = _safe_asset_path(public_root, filename)
        report_path = asset_path or public_root
        if line_id in seen_ids:
            _issue(issues, line_id, "DUPLICATE_LINE_ID", report_path)
        seen_ids.add(line_id)
        if isinstance(filename, str):
            if filename in seen_filenames:
                _issue(issues, line_id, "DUPLICATE_FILENAME", report_path)
            seen_filenames.add(filename)
        if asset_path is None:
            _issue(issues, line_id, "ASSET_PATH_INVALID", public_root)
            continue
        expected_asset_paths.add(asset_path)

        line = lines.get(line_id)
        if line is None:
            _issue(issues, line_id, "LINE_NOT_FOUND", asset_path)
            continue
        profile = profiles.get(str(line.get("speaker_profile")))
        if profile is None:
            _issue(issues, line_id, "PROFILE_NOT_FOUND", asset_path)
            continue
        provider = profile.get("provider")
        expected_voice = (
            provider.get("edge_voice") if isinstance(provider, dict) else None
        )

        if asset.get("approved") is not True:
            _issue(issues, line_id, "ASSET_UNAPPROVED", asset_path)
        if asset.get("generator") != "edge_tts":
            _issue(issues, line_id, "GENERATOR_INVALID", asset_path)
        if asset.get("generator_revision") != GENERATOR_REVISION:
            _issue(issues, line_id, "GENERATOR_REVISION_STALE", asset_path)
        if (
            asset.get("model_id") != expected_voice
            or expected_voice not in SUPPORTED_VOICES
        ):
            _issue(issues, line_id, "MODEL_ID_INVALID", asset_path)
        if asset.get("media_type") != MEDIA_TYPE:
            _issue(issues, line_id, "MEDIA_TYPE_INVALID", asset_path)
        if asset.get("line_version") != line.get("version"):
            _issue(issues, line_id, "LINE_VERSION_MISMATCH", asset_path)
        if asset.get("profile_version") != profile.get("version"):
            _issue(issues, line_id, "PROFILE_VERSION_MISMATCH", asset_path)
        if asset.get("seed_provenance") != "edge_tts_synthetic":
            _issue(issues, line_id, "SEED_PROVENANCE_INVALID", asset_path)

        text = line.get("text")
        expected_text_hash = (
            hashlib.sha256(text.encode("utf-8")).hexdigest()
            if isinstance(text, str)
            else ""
        )
        if asset.get("text_sha256") != expected_text_hash:
            _issue(issues, line_id, "TEXT_SHA256_MISMATCH", asset_path)

        if not asset_path.is_file():
            _issue(issues, line_id, "MISSING_FIXED_ASSET", asset_path)
            continue
        if hashlib.sha256(asset_path.read_bytes()).hexdigest() != asset.get("sha256"):
            _issue(issues, line_id, "ASSET_SHA256_MISMATCH", asset_path)
        try:
            media = media_inspector(asset_path)
        except (OSError, RuntimeError, ValueError, KeyError):
            _issue(issues, line_id, "MEDIA_INSPECTION_FAILED", asset_path)
            continue

        if media.codec_name != "opus":
            _issue(issues, line_id, "MEDIA_CODEC_INVALID", asset_path)
        if media.channels != 1:
            _issue(issues, line_id, "MEDIA_NOT_MONO", asset_path)
        if media.sample_rate != 48_000:
            _issue(issues, line_id, "MEDIA_SAMPLE_RATE_INVALID", asset_path)
        duration = asset.get("duration_ms")
        if (
            not isinstance(duration, int)
            or abs(duration - media.duration_ms) > DURATION_TOLERANCE_MS
        ):
            _issue(issues, line_id, "DURATION_MISMATCH", asset_path)
        if not LOUDNESS_MIN <= media.integrated_lufs <= LOUDNESS_MAX:
            _issue(issues, line_id, "LOUDNESS_OUT_OF_RANGE", asset_path)
        if media.true_peak_dbfs > TRUE_PEAK_MAX:
            _issue(issues, line_id, "TRUE_PEAK_EXCEEDED", asset_path)
        recorded_loudness = asset.get("integrated_lufs")
        if (
            not isinstance(recorded_loudness, (int, float))
            or abs(float(recorded_loudness) - media.integrated_lufs)
            > MEASUREMENT_TOLERANCE
        ):
            _issue(issues, line_id, "LOUDNESS_MEASUREMENT_MISMATCH", asset_path)
        recorded_peak = asset.get("true_peak_dbfs")
        if (
            not isinstance(recorded_peak, (int, float))
            or abs(float(recorded_peak) - media.true_peak_dbfs) > MEASUREMENT_TOLERANCE
        ):
            _issue(issues, line_id, "TRUE_PEAK_MEASUREMENT_MISMATCH", asset_path)
        _validate_cues(
            issues=issues,
            line_id=line_id,
            asset_path=asset_path,
            cues=asset.get("cues"),
            duration_ms=media.duration_ms,
            line=line,
        )

    for line in lines_list:
        if line.get("delivery") == "pre_generated" and line.get("id") not in seen_ids:
            _issue(
                issues,
                line.get("id"),
                "MISSING_FIXED_ASSET",
                manifest_path,
            )

    active_roots = {
        Path(str(asset.get("filename", ""))).parent
        for asset in manifest
        if isinstance(asset, dict)
    }
    for active_root in active_roots:
        scan_root = (public_root / active_root).resolve()
        if scan_root.is_dir():
            for path in sorted(scan_root.iterdir()):
                if path.is_file() and path.resolve() not in expected_asset_paths:
                    _issue(issues, "<stale>", "STALE_FIXED_ASSET", path)
    return issues


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest",
        type=Path,
        help="Override the shipping manifest path (tests and staging only).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    repository_root = Path(__file__).resolve().parents[2]
    data_root = repository_root / "backend" / "data"
    manifest_path = args.manifest or data_root / "voice_assets.json"
    issues = validate_voice_assets(
        manifest_path=manifest_path,
        lines_path=data_root / "voice_lines.json",
        profiles_path=data_root / "voice_profiles.json",
        public_root=data_root / "voice_public",
    )
    if issues:
        for issue in issues:
            print(issue.render())
        return 1
    manifest = _load_list(manifest_path)
    print(f"Voice assets valid: {len(manifest)} approved lines, 0 stale files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
