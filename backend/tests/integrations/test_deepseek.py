from __future__ import annotations

import json

import pytest

from backend.domain.errors import DomainError
from backend.integrations.deepseek import (
    DeepSeekDialogueClient,
    DialogueContext,
)


VALID_RESPONSE = {
    "reply": "额记得，那把刻刀是爷爷留下的。",
    "trust_change": 5,
    "npc_mood": "warm",
    "fragment_revealed": "fragment_grandpa_knife",
    "inner_thought": "他愿意听",
}


def context() -> DialogueContext:
    return DialogueContext(
        system_prompt="只输出 JSON 对象。",
        player_prompt="讲讲那把刻刀。",
    )


def test_parses_a_strict_structured_response() -> None:
    client = DeepSeekDialogueClient(
        completion_create=lambda _context: json.dumps(VALID_RESPONSE),
    )

    suggestion = client.suggest(context())

    assert suggestion.reply == VALID_RESPONSE["reply"]
    assert suggestion.trust_change == 5
    assert suggestion.npc_mood == "warm"
    assert suggestion.fragment_revealed == "fragment_grandpa_knife"


def test_retries_transient_timeout_then_succeeds() -> None:
    attempts = 0

    def complete(_context: DialogueContext) -> str:
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise TimeoutError("provider timed out")
        return json.dumps(VALID_RESPONSE)

    client = DeepSeekDialogueClient(
        completion_create=complete,
        max_retries=2,
        sleep=lambda _seconds: None,
    )

    suggestion = client.suggest(context())

    assert attempts == 3
    assert suggestion.reply == VALID_RESPONSE["reply"]


@pytest.mark.parametrize("status_code", [429, 500, 503])
def test_retries_transient_provider_statuses(status_code: int) -> None:
    attempts = 0

    class ProviderStatusError(Exception):
        def __init__(self) -> None:
            self.status_code = status_code

    def complete(_context: DialogueContext) -> str:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise ProviderStatusError
        return json.dumps(VALID_RESPONSE)

    client = DeepSeekDialogueClient(
        completion_create=complete,
        max_retries=2,
        sleep=lambda _seconds: None,
    )

    client.suggest(context())

    assert attempts == 2


@pytest.mark.parametrize(
    "payload",
    [
        "not-json",
        "{}",
        '{"reply":"x","trust_change":99,"npc_mood":"warm"}',
        '{"reply":"x","trust_change":0,"npc_mood":"invented"}',
    ],
)
def test_invalid_provider_output_is_not_exposed(payload: str) -> None:
    client = DeepSeekDialogueClient(completion_create=lambda _context: payload)

    with pytest.raises(DomainError) as caught:
        client.suggest(context())

    assert caught.value.code == "AI_UNAVAILABLE"
    assert payload not in caught.value.message
    assert "errors" not in caught.value.details


def test_circuit_opens_after_repeated_failed_calls() -> None:
    attempts = 0
    now = 100.0

    def complete(_context: DialogueContext) -> str:
        nonlocal attempts
        attempts += 1
        raise TimeoutError("offline")

    client = DeepSeekDialogueClient(
        completion_create=complete,
        max_retries=0,
        failure_threshold=2,
        cooldown_seconds=30,
        monotonic=lambda: now,
        sleep=lambda _seconds: None,
    )

    for _ in range(2):
        with pytest.raises(DomainError):
            client.suggest(context())

    with pytest.raises(DomainError) as caught:
        client.suggest(context())

    assert caught.value.code == "AI_UNAVAILABLE"
    assert attempts == 2
