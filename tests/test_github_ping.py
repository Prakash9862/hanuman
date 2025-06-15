# tests/test_github_ping.py

from fastapi.testclient import TestClient

from hanuman.main import app

client = TestClient(app)


def test_github_ping():
    response = client.get("/github/ping")
    data = response.json()

    assert "ok" in data

    if data["ok"]:
        assert "login" in data
        assert isinstance(data["login"], str)
    else:
        assert "error" in data
