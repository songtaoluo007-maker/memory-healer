from __future__ import annotations

from fastapi.testclient import TestClient

from backend.api import dialogue
from backend.application.dialogue_service import DialogueService
from backend.integrations.deepseek import DialogueSuggestion
from backend.main import app


class StubDialogueClient:
    def suggest(self, _context):
        return DialogueSuggestion(
            reply="影子要有光才站得住。",
            trust_change=3,
            npc_mood="warm",
            fragment_revealed="fragment_shadow_puppet",
            inner_thought="他真的在听。",
        )


def test_chat_returns_authoritative_state(monkeypatch) -> None:
    monkeypatch.setattr(
        dialogue,
        "dialogue_service",
        DialogueService(dialogue.CONTENT_REGISTRY, StubDialogueClient()),
    )
    with TestClient(app) as client:
        initial = client.get("/api/game/new").json()["state"]
        response = client.post(
            "/api/dialogue/chat",
            json={
                "npc_id": "chen_shouyi_young",
                "player_input": "皮影为什么能活起来？",
                "game_state": initial,
                "expected_revision": initial["revision"],
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["state"]["revision"] == initial["revision"] + 1
    assert body["state"]["npc_trust"]["chen_shouyi_young"] == 33
    assert body["fragment_revealed"] == "fragment_shadow_puppet"
    assert body["degraded"] is False


def test_chat_rejects_stale_revision(monkeypatch) -> None:
    monkeypatch.setattr(
        dialogue,
        "dialogue_service",
        DialogueService(dialogue.CONTENT_REGISTRY, StubDialogueClient()),
    )
    with TestClient(app) as client:
        initial = client.get("/api/game/new").json()["state"]
        response = client.post(
            "/api/dialogue/chat",
            json={
                "npc_id": "chen_shouyi_young",
                "player_input": "继续说。",
                "game_state": initial,
                "expected_revision": initial["revision"] + 1,
            },
        )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "GAME_REVISION_CONFLICT"
