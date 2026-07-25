from __future__ import annotations

from fastapi.testclient import TestClient

import hanuman.api.routers.chess_to_obsidian as chess_router
from hanuman.main import app

client = TestClient(app)


def test_chess_sync_router(monkeypatch) -> None:
    captured: dict[str, int] = {}

    def fake_sync(limit: int) -> dict[str, object]:
        captured["limit"] = limit
        return {
            "status": "ok",
            "username": "prakasch",
            "destination": "/tmp/Echecs",
            "games_received": 2,
            "games_created": 2,
            "games_skipped": 0,
            "openings_updated": 1,
        }

    monkeypatch.setattr(chess_router, "sync_chess_to_obsidian", fake_sync)

    response = client.post("/chess/sync", params={"limit": 42})
    data = response.json()

    assert response.status_code == 200
    assert captured["limit"] == 42
    assert data["status"] == "ok"
    assert data["games_received"] == 2
    assert data["openings_updated"] == 1
