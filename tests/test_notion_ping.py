# tests/test_notion_ping.py

from fastapi.testclient import TestClient

from hanuman.main import app

client = TestClient(app)


def test_notion_ping():
    response = client.get("/notion/ping")
    data = response.json()

    assert "ok" in data

    if data["ok"]:
        assert "user" in data
        assert isinstance(data["user"], dict)
        assert "name" in data["user"]
        assert "type" in data["user"]
    else:
        assert "error" in data
