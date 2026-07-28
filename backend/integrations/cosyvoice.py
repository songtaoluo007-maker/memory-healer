"""Authenticated HTTP adapter for the local pinned CosyVoice bridge."""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import time
from pathlib import Path, PurePosixPath, PureWindowsPath
from tempfile import NamedTemporaryFile
from typing import Any

import httpx

from backend.integrations.voice_contracts import (
    VoiceSynthesisRequest,
    VoiceSynthesisResult,
)


class VoiceProviderError(RuntimeError):
    """A voice provider rejected or could not satisfy a request."""


class VoiceProviderTimeout(VoiceProviderError):
    """A voice provider exceeded its configured deadline."""


class CosyVoiceHttpProvider:
    def __init__(
        self,
        *,
        base_url: str,
        bridge_token: str,
        cache_dir: Path,
        seed_root: Path,
        model_revision: str,
        client: httpx.AsyncClient | None = None,
        connect_timeout_seconds: float = 0.5,
        total_timeout_seconds: float = 2.5,
        max_concurrency: int = 1,
        max_cache_files: int = 500,
        max_cache_bytes: int = 2_147_483_648,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.bridge_token = bridge_token
        self.cache_dir = Path(cache_dir)
        self.seed_root = Path(seed_root).resolve()
        self.model_revision = model_revision
        self.max_cache_files = max_cache_files
        self.max_cache_bytes = max_cache_bytes
        self._timeout = httpx.Timeout(
            total_timeout_seconds,
            connect=connect_timeout_seconds,
        )
        self._client = client or httpx.AsyncClient()
        self._generation_slots = asyncio.Semaphore(max_concurrency)
        self._key_locks: dict[str, asyncio.Lock] = {}
        self._in_flight: set[str] = set()
        self._last_access_ns = 0
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    async def synthesize(self, request: VoiceSynthesisRequest) -> VoiceSynthesisResult:
        seed_path = self._resolve_seed(request.profile.provider.cosyvoice_seed)
        cache_key = self._cache_key(request)
        cache_path = self.cache_dir / f"{cache_key}.wav"

        if cache_path.is_file():
            self._touch(cache_path)
            return self._result(request, cache_path, cache_hit=True)

        lock = self._key_locks.setdefault(cache_key, asyncio.Lock())
        result: VoiceSynthesisResult | None = None
        async with lock:
            self._in_flight.add(cache_key)
            try:
                if cache_path.is_file():
                    self._touch(cache_path)
                    result = self._result(request, cache_path, cache_hit=True)
                else:
                    wav_bytes = await self._generate(request, seed_path)
                    self._write_atomically(cache_path, wav_bytes)
                    self._touch(cache_path)
                    result = self._result(request, cache_path, cache_hit=False)
            finally:
                self._in_flight.discard(cache_key)
                self._cleanup_cache(protected_keys={cache_key})

        if result is None:  # pragma: no cover - the guarded branches always assign
            raise VoiceProviderError("CosyVoice synthesis produced no result")
        return result

    def _resolve_seed(self, logical_name: str) -> Path:
        normalized = logical_name.strip().replace("\\", "/")
        if not normalized:
            raise VoiceProviderError("CosyVoice seed path is empty")

        logical = PurePosixPath(normalized)
        windows_logical = PureWindowsPath(normalized)
        if logical.is_absolute() or windows_logical.is_absolute() or windows_logical.drive:
            raise VoiceProviderError("CosyVoice seed path must be relative")

        parts = logical.parts
        if parts and parts[0] == "seeds":
            parts = parts[1:]
            if parts and parts[0] == "seeds":
                raise VoiceProviderError("CosyVoice seed path has a repeated seeds prefix")
        if not parts or any(part in {"", ".", ".."} for part in parts):
            raise VoiceProviderError("CosyVoice seed path is invalid")

        candidate = self.seed_root.joinpath(*parts).resolve()
        try:
            candidate.relative_to(self.seed_root)
        except ValueError as exc:
            raise VoiceProviderError("CosyVoice seed path escapes the seed root") from exc
        if not candidate.is_file():
            raise VoiceProviderError(f"CosyVoice seed file is missing: {logical_name}")
        return candidate

    def _cache_key(self, request: VoiceSynthesisRequest) -> str:
        payload: dict[str, Any] = {
            "text": request.text.strip(),
            "profile_id": request.profile.id,
            "profile_version": request.profile.version,
            "emotion": request.emotion,
            "intensity": request.intensity,
            "instruction": request.profile.provider.cosyvoice_instruction,
            "seed": request.profile.provider.cosyvoice_seed,
            "model_revision": self.model_revision,
        }
        serialized = json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        return hashlib.sha256(serialized).hexdigest()

    async def _generate(
        self,
        request: VoiceSynthesisRequest,
        seed_path: Path,
    ) -> bytes:
        async with self._generation_slots:
            try:
                response = await self._client.post(
                    f"{self.base_url}/v1/synthesize",
                    headers={"X-Voice-Bridge-Token": self.bridge_token},
                    data={
                        "tts_text": request.text.strip(),
                        "instruct_text": request.profile.provider.cosyvoice_instruction,
                    },
                    files={
                        "prompt_wav": (
                            seed_path.name,
                            seed_path.read_bytes(),
                            "audio/wav",
                        )
                    },
                    timeout=self._timeout,
                )
            except httpx.TimeoutException as exc:
                raise VoiceProviderTimeout("CosyVoice bridge timed out") from exc
            except httpx.HTTPError as exc:
                raise VoiceProviderError("CosyVoice bridge request failed") from exc

        if response.status_code < 200 or response.status_code >= 300:
            raise VoiceProviderError(
                f"CosyVoice bridge returned HTTP {response.status_code}"
            )
        media_type = response.headers.get("content-type", "").split(";", 1)[0].strip()
        if media_type.lower() != "audio/wav":
            raise VoiceProviderError("CosyVoice bridge did not return audio/wav")
        if not response.content:
            raise VoiceProviderError("CosyVoice bridge returned an empty WAV")
        return response.content

    def _write_atomically(self, cache_path: Path, wav_bytes: bytes) -> None:
        temporary_path: Path | None = None
        try:
            with NamedTemporaryFile(
                mode="wb",
                dir=self.cache_dir,
                prefix=f".{cache_path.stem}-",
                suffix=".tmp",
                delete=False,
            ) as temporary:
                temporary.write(wav_bytes)
                temporary.flush()
                os.fsync(temporary.fileno())
                temporary_path = Path(temporary.name)
            temporary_path.replace(cache_path)
        except OSError as exc:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)
            raise VoiceProviderError("Unable to write CosyVoice cache entry") from exc

    def _touch(self, path: Path) -> None:
        access_ns = max(time.time_ns(), self._last_access_ns + 1)
        self._last_access_ns = access_ns
        os.utime(path, ns=(access_ns, path.stat().st_mtime_ns))

    def _cleanup_cache(self, *, protected_keys: set[str]) -> None:
        protected = self._in_flight | protected_keys
        entries: list[tuple[int, int, str, Path, int]] = []
        total_bytes = 0
        for path in self.cache_dir.glob("*.wav"):
            if not path.is_file():
                continue
            stat = path.stat()
            total_bytes += stat.st_size
            entries.append(
                (stat.st_atime_ns, stat.st_mtime_ns, path.name, path, stat.st_size)
            )

        entries.sort()
        file_count = len(entries)
        for _, _, _, path, size in entries:
            if (
                file_count <= self.max_cache_files
                and total_bytes <= self.max_cache_bytes
            ):
                break
            if path.stem in protected:
                continue
            try:
                path.unlink()
            except FileNotFoundError:
                continue
            file_count -= 1
            total_bytes -= size

    @staticmethod
    def _result(
        request: VoiceSynthesisRequest,
        cache_path: Path,
        *,
        cache_hit: bool,
    ) -> VoiceSynthesisResult:
        return VoiceSynthesisResult(
            url=f"/voice/cache/{cache_path.name}",
            provider="cosyvoice",
            cache_hit=cache_hit,
            media_type="audio/wav",
            duration_ms=None,
            line_id=request.line_id,
            cues=(),
            degraded=False,
        )
