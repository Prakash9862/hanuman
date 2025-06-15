# tests/test_wikipedia_ping.py

from fastapi.testclient import TestClient

from hanuman.main import app

client = TestClient(app)


def test_wikipedia_ping():
    response = client.get("/wikipedia/ping")
    data = response.json()

    assert "ok" in data

    if data["ok"]:
        assert "title" in data
        assert data["title"].lower() == "openai"
    else:
        assert "error" in data
