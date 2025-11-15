from __future__ import annotations

from fastapi.testclient import TestClient

import hanuman.api.routers.chess_to_obsidian as chess_router
from hanuman.main import app

client = TestClient(app)


def test_chess_sync_router(monkeypatch) -> None:
    captured = {}

    def fake_sync(limit: int) -> None:
        captured["limit"] = limit

    monkeypatch.setattr(chess_router, "sync_chess_to_obsidian", fake_sync)

    response = client.post("/chess/sync", params={"limit": 42})
    data = response.json()

    assert response.status_code == 200
    assert captured["limit"] == 42
    assert data == {"status": "ok", "synced": True, "limit": 42}
