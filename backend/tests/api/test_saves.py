from __future__ import annotations

from contextlib import ExitStack

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.database import Base, get_db
from backend.main import app
from backend.persistence.models import SaveSlot


@pytest.fixture
def save_context():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    testing_session = sessionmaker(bind=engine, expire_on_commit=False)
    db = testing_session()

    def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    with ExitStack() as stack:
        alice = stack.enter_context(TestClient(app))
        bob = stack.enter_context(TestClient(app))
        alice.post(
            "/api/auth/register",
            json={
                "username": "alice1",
                "password": "correct-horse",
                "nickname": "阿澄",
            },
        )
        bob.post(
            "/api/auth/register",
            json={
                "username": "bob1",
                "password": "correct-horse",
                "nickname": "小川",
            },
        )
        yield alice, bob, db

    app.dependency_overrides.clear()
    db.close()


def new_state(client: TestClient) -> dict:
    response = client.get("/api/game/new")
    assert response.status_code == 200
    return response.json()["state"]


def save(
    client: TestClient,
    state: dict,
    *,
    slot_id: int = 1,
    expected_revision: int = 0,
    slot_name: str = "第一幕",
):
    return client.post(
        "/api/save/save",
        json={
            "slot_id": slot_id,
            "slot_name": slot_name,
            "game_state": state,
            "expected_revision": expected_revision,
        },
    )


def test_save_slots_are_isolated_per_user(save_context) -> None:
    alice, bob, _db = save_context
    alice_state = new_state(alice)
    bob_state = new_state(bob)

    alice_save = save(alice, alice_state)
    bob_before = bob.get("/api/save/list")
    bob_load_alice = bob.post("/api/save/load", json={"slot_id": 1})
    bob_delete_alice = bob.delete("/api/save/delete/1")
    bob_save = save(bob, bob_state)

    assert alice_save.status_code == 200
    assert bob_before.json() == {"saves": []}
    assert bob_load_alice.status_code == 404
    assert bob_delete_alice.status_code == 404
    assert bob_save.status_code == 200
    assert alice.get("/api/save/list").json()["saves"][0]["slot_id"] == 1
    assert bob.get("/api/save/list").json()["saves"][0]["slot_id"] == 1


def test_save_compare_and_swap_rejects_stale_writes(save_context) -> None:
    alice, _bob, db = save_context
    initial_state = new_state(alice)

    first = save(alice, initial_state, expected_revision=0)
    updated_state = {**initial_state, "revision": 1, "current_mood": "温暖"}
    second = save(
        alice,
        updated_state,
        expected_revision=first.json()["save_revision"],
        slot_name="更新后的第一幕",
    )
    stale_state = {**initial_state, "revision": 2, "current_mood": "过期覆盖"}
    stale = save(
        alice,
        stale_state,
        expected_revision=first.json()["save_revision"],
        slot_name="不应写入",
    )
    loaded = alice.post("/api/save/load", json={"slot_id": 1})

    assert first.json()["save_revision"] == 1
    assert second.status_code == 200
    assert second.json()["save_revision"] == 2
    assert stale.status_code == 409
    assert stale.json()["error"]["code"] == "GAME_REVISION_CONFLICT"
    assert loaded.json()["slot_name"] == "更新后的第一幕"
    assert loaded.json()["game_state"]["current_mood"] == "温暖"
    persisted = db.scalar(select(SaveSlot))
    assert persisted.save_revision == 2
    assert persisted.state_schema_version == 1
    assert persisted.state_revision == 1


def test_first_save_requires_expected_revision_zero(save_context) -> None:
    alice, _bob, _db = save_context

    response = save(alice, new_state(alice), expected_revision=9)

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "GAME_REVISION_CONFLICT"
    assert alice.get("/api/save/list").json() == {"saves": []}


def test_invalid_game_state_is_rejected_before_persistence(save_context) -> None:
    alice, _bob, db = save_context
    invalid_state = new_state(alice)
    invalid_state["unexpected_field"] = "must be rejected"

    response = save(alice, invalid_state)

    assert response.status_code == 422
    assert db.scalar(select(SaveSlot)) is None


def test_load_returns_schema_valid_state_and_delete_is_scoped(save_context) -> None:
    alice, _bob, _db = save_context
    state = new_state(alice)
    save(alice, state)

    loaded = alice.post("/api/save/load", json={"slot_id": 1})
    deleted = alice.delete("/api/save/delete/1")

    assert loaded.status_code == 200
    assert loaded.json()["game_state"] == state
    assert loaded.json()["save_revision"] == 1
    assert deleted.status_code == 200
    assert alice.get("/api/save/list").json() == {"saves": []}
