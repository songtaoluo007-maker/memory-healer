"""Bounded Edge TTS synthesis with deterministic, atomic disk caching."""

from __future__ import annotations

import asyncio
import hashlib
import json
import re
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SUPPORTED_VOICES = frozenset(
    {
        "zh-CN-YunxiNeural",
        "zh-CN-YunjianNeural",
        "zh-CN-YunyangNeural",
        "zh-CN-XiaoxiaoNeural",
        "zh-CN-XiaoyiNeural",
    }
)
_RATE_PATTERN = re.compile(r"^[+-](\d{1,2})%$")
_PITCH_PATTERN = re.compile(r"^[+-](\d{1,2})Hz$")


@dataclass(frozen=True, slots=True)
class TtsRequest:
    text: str
    voice: str
    rate: str = "+0%"
    pitch: str = "+0Hz"


@dataclass(frozen=True, slots=True)
class TtsResult:
    filename: str
    cache_hit: bool

    @property
    def url(self) -> str:
        return f"/tts/{self.filename}"


def _edge_communicator_factory(**kwargs: str) -> Any:
    import edge_tts

    return edge_tts.Communicate(**kwargs)


class TtsService:
    def __init__(
        self,
        cache_dir: Path,
        *,
        communicator_factory: Callable[..., Any] | None = None,
        max_text_length: int = 500,
        max_concurrency: int = 2,
        max_cache_files: int = 500,
        max_cache_bytes: int = 256 * 1024 * 1024,
    ) -> None:
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.communicator_factory = communicator_factory or _edge_communicator_factory
        self.max_text_length = max_text_length
        self.max_cache_files = max_cache_files
        self.max_cache_bytes = max_cache_bytes
        self._semaphore = asyncio.Semaphore(max_concurrency)
        self._locks: dict[str, asyncio.Lock] = {}
        self._cleanup_lock = asyncio.Lock()
        self._active_files: set[Path] = set()

    def validate(self, request: TtsRequest) -> None:
        text = request.text.strip()
        if not text:
            raise ValueError("TTS text cannot be empty")
        if len(text) > self.max_text_length:
            raise ValueError(f"TTS text cannot exceed {self.max_text_length} characters")
        if request.voice not in SUPPORTED_VOICES:
            raise ValueError("unsupported TTS voice")

        rate_match = _RATE_PATTERN.fullmatch(request.rate)
        if rate_match is None or int(rate_match.group(1)) > 50:
            raise ValueError("TTS rate must be between -50% and +50%")
        pitch_match = _PITCH_PATTERN.fullmatch(request.pitch)
        if pitch_match is None or int(pitch_match.group(1)) > 50:
            raise ValueError("TTS pitch must be between -50Hz and +50Hz")

    def cache_key(self, request: TtsRequest) -> str:
        payload = json.dumps(
            {
                "text": request.text.strip(),
                "voice": request.voice,
                "rate": request.rate,
                "pitch": request.pitch,
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    async def synthesize(self, request: TtsRequest) -> TtsResult:
        self.validate(request)
        key = self.cache_key(request)
        cache_path = self.cache_dir / f"{key}.mp3"
        key_lock = self._locks.setdefault(key, asyncio.Lock())

        async with key_lock:
            if cache_path.is_file():
                cache_path.touch()
                return TtsResult(filename=cache_path.name, cache_hit=True)

            self._active_files.add(cache_path)
            temporary_path: Path | None = None
            try:
                async with self._semaphore:
                    with tempfile.NamedTemporaryFile(
                        delete=False,
                        dir=self.cache_dir,
                        prefix=f"{key}-",
                        suffix=".tmp",
                    ) as temporary_file:
                        temporary_path = Path(temporary_file.name)

                    communicator = self.communicator_factory(
                        text=request.text.strip(),
                        voice=request.voice,
                        rate=request.rate,
                        pitch=request.pitch,
                    )
                    await communicator.save(str(temporary_path))
                    if not temporary_path.is_file() or temporary_path.stat().st_size == 0:
                        raise RuntimeError("TTS provider returned empty audio")
                    if temporary_path.stat().st_size > self.max_cache_bytes:
                        raise RuntimeError("TTS result exceeds configured cache capacity")
                    temporary_path.replace(cache_path)
                    temporary_path = None

                await self.cleanup_cache()
                if not cache_path.is_file():
                    raise RuntimeError("TTS result exceeded configured cache capacity")
                return TtsResult(filename=cache_path.name, cache_hit=False)
            finally:
                self._active_files.discard(cache_path)
                if temporary_path is not None:
                    temporary_path.unlink(missing_ok=True)
                await self.cleanup_cache()

    async def cleanup_cache(self) -> None:
        async with self._cleanup_lock:
            files = [path for path in self.cache_dir.glob("*.mp3") if path.is_file()]
            removable = [path for path in files if path not in self._active_files]
            removable.sort(
                key=lambda path: (
                    path.stat().st_atime_ns,
                    path.stat().st_mtime_ns,
                    path.name,
                )
            )
            total_bytes = sum(path.stat().st_size for path in files)
            total_files = len(files)
            while removable and (
                total_files > self.max_cache_files or total_bytes > self.max_cache_bytes
            ):
                oldest = removable.pop(0)
                size = oldest.stat().st_size
                oldest.unlink(missing_ok=True)
                total_bytes -= size
                total_files -= 1
