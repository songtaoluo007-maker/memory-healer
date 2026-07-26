from __future__ import annotations

import asyncio
import os
from pathlib import Path

import pytest

from backend.integrations.tts import TtsRequest, TtsService


class FakeCommunicator:
    def __init__(
        self,
        *,
        payload: bytes = b"ID3-fake-audio",
        error: Exception | None = None,
        delay: float = 0,
    ) -> None:
        self.payload = payload
        self.error = error
        self.delay = delay
        self.calls = 0
        self.paths: list[Path] = []

    def factory(self, **_kwargs):
        owner = self

        class Communicator:
            async def save(self, path: str) -> None:
                owner.calls += 1
                owner.paths.append(Path(path))
                if owner.delay:
                    await asyncio.sleep(owner.delay)
                if owner.error is not None:
                    Path(path).write_bytes(b"partial")
                    raise owner.error
                Path(path).write_bytes(owner.payload)

        return Communicator()


def request(**overrides) -> TtsRequest:
    values = {
        "text": "那年戏台下，所有人都屏住了呼吸。",
        "voice": "zh-CN-YunxiNeural",
        "rate": "+0%",
        "pitch": "+0Hz",
    }
    values.update(overrides)
    return TtsRequest(**values)


def test_cache_key_includes_all_synthesis_inputs(tmp_path: Path) -> None:
    service = TtsService(tmp_path, communicator_factory=FakeCommunicator().factory)
    baseline = service.cache_key(request())

    assert service.cache_key(request(text="另一段台词")) != baseline
    assert service.cache_key(request(voice="zh-CN-XiaoxiaoNeural")) != baseline
    assert service.cache_key(request(rate="-10%")) != baseline
    assert service.cache_key(request(pitch="-5Hz")) != baseline
    assert len(baseline) == 64


@pytest.mark.parametrize(
    "invalid_request",
    [
        request(text="字" * 501),
        request(voice="unsupported-voice"),
        request(rate="+80%"),
        request(rate="fast"),
        request(pitch="-80Hz"),
        request(pitch="low"),
    ],
)
def test_invalid_inputs_are_rejected(tmp_path: Path, invalid_request: TtsRequest) -> None:
    service = TtsService(tmp_path, communicator_factory=FakeCommunicator().factory)

    with pytest.raises(ValueError):
        service.validate(invalid_request)


@pytest.mark.asyncio
async def test_concurrent_identical_requests_synthesize_once(tmp_path: Path) -> None:
    communicator = FakeCommunicator(delay=0.02)
    service = TtsService(
        tmp_path,
        communicator_factory=communicator.factory,
        max_concurrency=2,
    )

    results = await asyncio.gather(*(service.synthesize(request()) for _ in range(8)))

    assert communicator.calls == 1
    assert len({result.filename for result in results}) == 1
    assert all((tmp_path / result.filename).read_bytes() == communicator.payload for result in results)


@pytest.mark.asyncio
async def test_success_atomically_renames_and_removes_temp_file(tmp_path: Path) -> None:
    communicator = FakeCommunicator()
    service = TtsService(tmp_path, communicator_factory=communicator.factory)

    result = await service.synthesize(request())

    assert (tmp_path / result.filename).is_file()
    assert communicator.paths[0] != tmp_path / result.filename
    assert not communicator.paths[0].exists()
    assert list(tmp_path.glob("*.tmp")) == []


@pytest.mark.asyncio
async def test_failed_synthesis_leaves_no_partial_files(tmp_path: Path) -> None:
    communicator = FakeCommunicator(error=RuntimeError("provider unavailable"))
    service = TtsService(tmp_path, communicator_factory=communicator.factory)

    with pytest.raises(RuntimeError, match="provider unavailable"):
        await service.synthesize(request())

    assert list(tmp_path.iterdir()) == []


@pytest.mark.asyncio
async def test_cleanup_respects_file_count_and_total_bytes(tmp_path: Path) -> None:
    communicator = FakeCommunicator(payload=b"x" * 8)
    service = TtsService(
        tmp_path,
        communicator_factory=communicator.factory,
        max_cache_files=2,
        max_cache_bytes=16,
    )
    for index in range(3):
        path = tmp_path / f"old-{index}.mp3"
        path.write_bytes(b"x" * 8)
        os.utime(path, (index + 1, index + 1))

    await service.cleanup_cache()

    files = list(tmp_path.glob("*.mp3"))
    assert len(files) <= 2
    assert sum(path.stat().st_size for path in files) <= 16
    assert not (tmp_path / "old-0.mp3").exists()
