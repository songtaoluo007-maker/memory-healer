"""Provider-neutral authenticated HTTP voice adapter."""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import time
from pathlib import Path
from tempfile import NamedTemporaryFile

import httpx

from backend.integrations.voice_contracts import (
    VoiceSynthesisRequest,
    VoiceSynthesisResult,
)


class VoiceProviderError(RuntimeError):
    """A remote voice provider could not satisfy a request."""


class VoiceProviderTimeout(VoiceProviderError):
    """A remote voice provider exceeded its configured deadline."""


class RemoteVoiceHttpProvider:
    def __init__(
        self,
        *,
        base_url: str,
        token: str,
        cache_dir: Path,
        client: httpx.AsyncClient | None = None,
        connect_timeout_seconds: float = 0.5,
        total_timeout_seconds: float = 2.5,
        max_concurrency: int = 1,
        max_cache_files: int = 500,
        max_cache_bytes: int = 2_147_483_648,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.cache_dir = Path(cache_dir)
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
        cache_key = self._cache_key(request)
        cache_path = self.cache_dir / f"{cache_key}.wav"
        if cache_path.is_file():
            self._touch(cache_path)
            return self._result(request, cache_path, cache_hit=True)

        lock = self._key_locks.setdefault(cache_key, asyncio.Lock())
        async with lock:
            self._in_flight.add(cache_key)
            try:
                if cache_path.is_file():
                    self._touch(cache_path)
                    return self._result(request, cache_path, cache_hit=True)
                audio = await self._generate(request, cache_key)
                self._write_atomically(cache_path, audio)
                self._touch(cache_path)
                return self._result(request, cache_path, cache_hit=False)
            finally:
                self._in_flight.discard(cache_key)
                self._cleanup_cache(protected_keys={cache_key})

    @staticmethod
    def _request_identity(request: VoiceSynthesisRequest) -> dict[str, object]:
        return {
            "text": request.text.strip(),
            "profile_id": request.profile.id,
            "profile_version": request.profile.version,
            "emotion": request.emotion,
            "intensity": request.intensity,
        }

    def _cache_key(self, request: VoiceSynthesisRequest) -> str:
        serialized = json.dumps(
            self._request_identity(request),
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        return hashlib.sha256(serialized).hexdigest()

    async def _generate(
        self,
        request: VoiceSynthesisRequest,
        cache_key: str,
    ) -> bytes:
        payload = self._request_identity(request)
        payload["cache_key"] = cache_key
        async with self._generation_slots:
            try:
                response = await self._client.post(
                    f"{self.base_url}/v1/synthesize",
                    headers={"Authorization": f"Bearer {self.token}"},
                    json=payload,
                    timeout=self._timeout,
                )
            except httpx.TimeoutException as exc:
                raise VoiceProviderTimeout("Remote voice provider timed out") from exc
            except httpx.HTTPError as exc:
                raise VoiceProviderError("Remote voice provider request failed") from exc

        if response.status_code < 200 or response.status_code >= 300:
            raise VoiceProviderError(
                f"Remote voice provider returned HTTP {response.status_code}"
            )
        media_type = response.headers.get("content-type", "").split(";", 1)[0].strip()
        if media_type.casefold() != "audio/wav":
            raise VoiceProviderError("Remote voice provider did not return audio/wav")
        if not response.content:
            raise VoiceProviderError("Remote voice provider returned empty audio")
        return response.content

    def _write_atomically(self, cache_path: Path, audio: bytes) -> None:
        temporary_path: Path | None = None
        try:
            with NamedTemporaryFile(
                mode="wb",
                dir=self.cache_dir,
                prefix=f".{cache_path.stem}-",
                suffix=".tmp",
                delete=False,
            ) as temporary:
                temporary.write(audio)
                temporary.flush()
                os.fsync(temporary.fileno())
                temporary_path = Path(temporary.name)
            temporary_path.replace(cache_path)
        except OSError as exc:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)
            raise VoiceProviderError("Unable to write remote voice cache") from exc

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
            provider="remote",
            cache_hit=cache_hit,
            media_type="audio/wav",
            duration_ms=None,
            line_id=request.line_id,
            cues=(),
            degraded=False,
        )
