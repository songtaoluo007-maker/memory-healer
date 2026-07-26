from __future__ import annotations

import json
import time
from collections.abc import Callable
from typing import Literal

import httpx
from openai import OpenAI
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from backend.domain.errors import DomainError


class IntegrationModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class DialogueContext(IntegrationModel):
    system_prompt: str = Field(min_length=1)
    player_prompt: str = Field(min_length=1)


class DialogueSuggestion(IntegrationModel):
    reply: str = Field(min_length=1, max_length=1000)
    trust_change: int = Field(ge=-10, le=10)
    npc_mood: Literal["neutral", "warm", "guarded", "sad", "hopeful"]
    fragment_revealed: str | None = None
    inner_thought: str = Field(default="", max_length=300)


CompletionCreate = Callable[[DialogueContext], str]


class DeepSeekDialogueClient:
    """Structured DeepSeek adapter with bounded retry and a small circuit breaker."""

    def __init__(
        self,
        *,
        api_key: str = "",
        base_url: str = "https://api.deepseek.com",
        model: str = "deepseek-v4-flash",
        connect_timeout_seconds: float = 5,
        total_timeout_seconds: float = 30,
        max_retries: int = 2,
        failure_threshold: int = 5,
        cooldown_seconds: float = 30,
        completion_create: CompletionCreate | None = None,
        monotonic: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.connect_timeout_seconds = connect_timeout_seconds
        self.total_timeout_seconds = total_timeout_seconds
        self.max_retries = max(0, max_retries)
        self.failure_threshold = max(1, failure_threshold)
        self.cooldown_seconds = max(1, cooldown_seconds)
        self.completion_create = completion_create
        self.monotonic = monotonic
        self.sleep = sleep
        self._client: OpenAI | None = None
        self._consecutive_failures = 0
        self._circuit_open_until = 0.0

    def suggest(self, context: DialogueContext) -> DialogueSuggestion:
        if self.monotonic() < self._circuit_open_until:
            raise DomainError(
                "AI_UNAVAILABLE",
                "对话服务暂时不可用，已切换到本地对白",
                details={"circuit_open": True},
            )

        for attempt in range(self.max_retries + 1):
            try:
                raw_content = self._invoke(context)
                payload = json.loads(raw_content)
                suggestion = DialogueSuggestion.model_validate(payload)
            except (json.JSONDecodeError, ValidationError, TypeError, ValueError):
                self._record_failure()
                raise DomainError(
                    "AI_UNAVAILABLE",
                    "对话服务返回了无法使用的内容，已切换到本地对白",
                    details={"invalid_response": True},
                ) from None
            except DomainError:
                self._record_failure()
                raise
            except Exception as exc:
                is_transient = self._is_transient(exc)
                if is_transient and attempt < self.max_retries:
                    self.sleep(0.25 * (2**attempt))
                    continue
                self._record_failure()
                raise DomainError(
                    "AI_UNAVAILABLE",
                    "对话服务暂时不可用，已切换到本地对白",
                    details={"transient": is_transient},
                ) from None
            else:
                self._consecutive_failures = 0
                self._circuit_open_until = 0.0
                return suggestion

        raise AssertionError("retry loop must return or raise")

    def _invoke(self, context: DialogueContext) -> str:
        if self.completion_create is not None:
            return self.completion_create(context)
        if not self.api_key:
            raise DomainError(
                "AI_UNAVAILABLE",
                "未配置对话服务，已切换到本地对白",
                details={"not_configured": True},
            )

        if self._client is None:
            timeout = httpx.Timeout(
                self.total_timeout_seconds,
                connect=self.connect_timeout_seconds,
            )
            self._client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=timeout,
                max_retries=0,
            )

        response = self._client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": context.system_prompt},
                {"role": "user", "content": context.player_prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
            max_tokens=400,
        )
        content = response.choices[0].message.content
        if not content:
            raise ValueError("empty provider content")
        return content

    @staticmethod
    def _is_transient(exc: Exception) -> bool:
        if isinstance(exc, (TimeoutError, ConnectionError, httpx.TimeoutException)):
            return True
        status_code = getattr(exc, "status_code", None)
        return status_code == 429 or (
            isinstance(status_code, int) and status_code >= 500
        )

    def _record_failure(self) -> None:
        self._consecutive_failures += 1
        if self._consecutive_failures >= self.failure_threshold:
            self._circuit_open_until = self.monotonic() + self.cooldown_seconds
