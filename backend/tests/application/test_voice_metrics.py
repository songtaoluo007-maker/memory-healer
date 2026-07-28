from __future__ import annotations

import threading
import time

from backend.application.voice_metrics import VoiceMetricsDispatcher


def test_slow_metrics_sink_never_blocks_request_emitter() -> None:
    entered = threading.Event()
    release = threading.Event()
    received: list[dict[str, object]] = []

    def slow_sink(event: dict[str, object]) -> None:
        entered.set()
        release.wait(timeout=1)
        received.append(event)

    dispatcher = VoiceMetricsDispatcher(slow_sink, max_queue_size=4)
    started = time.perf_counter()
    assert dispatcher.emit({"event": "voice_synthesis"}) is True
    elapsed = time.perf_counter() - started

    assert elapsed < 0.05
    assert entered.wait(timeout=1)
    release.set()
    assert dispatcher.close(timeout=1) is True
    assert received == [{"event": "voice_synthesis"}]


def test_full_metrics_queue_drops_without_blocking() -> None:
    entered = threading.Event()
    release = threading.Event()

    def blocked_sink(_event: dict[str, object]) -> None:
        entered.set()
        release.wait(timeout=1)

    dispatcher = VoiceMetricsDispatcher(blocked_sink, max_queue_size=1)
    assert dispatcher.emit({"sequence": 1}) is True
    assert entered.wait(timeout=1)
    assert dispatcher.emit({"sequence": 2}) is True

    started = time.perf_counter()
    assert dispatcher.emit({"sequence": 3}) is False
    assert time.perf_counter() - started < 0.05
    assert dispatcher.dropped_events == 1

    release.set()
    assert dispatcher.close(timeout=1) is True


def test_metrics_sink_errors_are_isolated_and_worker_keeps_draining() -> None:
    calls: list[int] = []

    def failing_sink(event: dict[str, object]) -> None:
        calls.append(int(event["sequence"]))
        raise RuntimeError("collector unavailable")

    dispatcher = VoiceMetricsDispatcher(failing_sink, max_queue_size=4)
    assert dispatcher.emit({"sequence": 1}) is True
    assert dispatcher.emit({"sequence": 2}) is True

    assert dispatcher.close(timeout=1) is True
    assert calls == [1, 2]
    assert dispatcher.sink_errors == 2


def test_metrics_dispatcher_close_stops_worker_and_rejects_new_events() -> None:
    dispatcher = VoiceMetricsDispatcher(lambda _event: None, max_queue_size=2)
    assert dispatcher.emit({"sequence": 1}) is True

    assert dispatcher.close(timeout=1) is True
    assert dispatcher.is_alive is False
    assert dispatcher.emit({"sequence": 2}) is False
    assert dispatcher.dropped_events == 1
