from fastapi.testclient import TestClient

from hanuman.main import app

client = TestClient(app)


def test_obsidian_ping():
    response = client.get("/obsidian/ping")
    data = response.json()

    assert "ok" in data
    assert "timestamp" in data
    assert "source" in data
    assert data["source"] == "obsidian"

    if data["ok"]:
        assert "detail" in data
        assert "note_count" in data["detail"]
        assert isinstance(data["detail"]["note_count"], int)
    else:
        assert "error" in data
