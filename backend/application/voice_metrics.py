"""Bounded, best-effort delivery for voice observability events."""

from __future__ import annotations

import json
import queue
import threading
from collections.abc import Callable
from typing import Protocol

from loguru import logger


class VoiceMetricsEmitter(Protocol):
    def emit(self, event: dict[str, object]) -> bool: ...


def _log_voice_event(event: dict[str, object]) -> None:
    logger.info(
        "{}",
        json.dumps(
            event,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ),
    )


class VoiceMetricsDispatcher:
    """Moves metrics I/O off request tasks and sheds load when saturated."""

    def __init__(
        self,
        sink: Callable[[dict[str, object]], None],
        *,
        max_queue_size: int = 256,
    ) -> None:
        self._sink = sink
        self._queue: queue.Queue[dict[str, object]] = queue.Queue(
            maxsize=max(1, max_queue_size)
        )
        self._state_lock = threading.Lock()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._accepting = True
        self._dropped_events = 0
        self._sink_errors = 0

    def start(self) -> None:
        with self._state_lock:
            if self._thread is not None and self._thread.is_alive():
                return
            self._accepting = True
            self._start_locked()

    def emit(self, event: dict[str, object]) -> bool:
        with self._state_lock:
            if not self._accepting:
                self._dropped_events += 1
                return False
            if self._thread is None or not self._thread.is_alive():
                self._start_locked()
        try:
            self._queue.put_nowait(dict(event))
            return True
        except queue.Full:
            with self._state_lock:
                self._dropped_events += 1
            return False

    def close(self, *, timeout: float | None = None) -> bool:
        with self._state_lock:
            self._accepting = False
            thread = self._thread
            self._stop.set()
        if thread is None:
            return True
        thread.join(timeout=timeout)
        return not thread.is_alive()

    @property
    def dropped_events(self) -> int:
        with self._state_lock:
            return self._dropped_events

    @property
    def sink_errors(self) -> int:
        with self._state_lock:
            return self._sink_errors

    @property
    def is_alive(self) -> bool:
        with self._state_lock:
            return self._thread is not None and self._thread.is_alive()

    def _run(self) -> None:
        while not self._stop.is_set() or not self._queue.empty():
            try:
                event = self._queue.get(timeout=0.05)
            except queue.Empty:
                continue
            try:
                self._sink(event)
            except Exception:
                with self._state_lock:
                    self._sink_errors += 1
            finally:
                self._queue.task_done()

    def _start_locked(self) -> None:
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._run,
            name="voice-metrics",
            daemon=True,
        )
        self._thread.start()


default_voice_metrics = VoiceMetricsDispatcher(_log_voice_event)


def start_default_voice_metrics() -> None:
    default_voice_metrics.start()


def close_default_voice_metrics(*, timeout: float = 2) -> bool:
    return default_voice_metrics.close(timeout=timeout)
