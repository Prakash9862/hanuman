from fastapi.testclient import TestClient

from hanuman.main import app

client = TestClient(app)


def test_chess_ping():
    response = client.get("/chess/ping")
    data = response.json()

    assert "ok" in data
    assert "timestamp" in data
    assert "source" in data
    assert data["source"] == "chess"

    if data["ok"]:
        assert "detail" in data
        assert "username" in data["detail"]
    else:
        assert "error" in data
