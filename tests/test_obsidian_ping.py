# tests/test_obsidian_ping.py

from fastapi.testclient import TestClient

from hanuman.main import app

client = TestClient(app)


def test_obsidian_ping():
    response = client.get("/obsidian/ping")
    data = response.json()

    assert "ok" in data

    if data["ok"]:
        assert "path" in data
        assert "note_count" in data
        assert isinstance(data["note_count"], int)
    else:
        assert "error" in data
