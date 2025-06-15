# tests/test_chess_ping.py

from fastapi.testclient import TestClient

from hanuman.main import app

client = TestClient(app)


def test_chess_ping():
    response = client.get("/chess/ping")
    data = response.json()

    assert "ok" in data

    if data["ok"]:
        assert "username" in data
        assert isinstance(data["username"], str)
    else:
        assert "error" in data
