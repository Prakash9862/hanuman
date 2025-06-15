from fastapi.testclient import TestClient

from hanuman.main import app

client = TestClient(app)


def test_wikipedia_ping() -> None:
    response = client.get("/wikipedia/ping")
    data = response.json()

    assert "ok" in data
    assert "timestamp" in data
    assert "source" in data
    assert data["source"] == "wikipedia"

    if data["ok"]:
        assert "detail" in data
        assert "title" in data["detail"]
        assert data["detail"]["title"].lower() == "openai"
    else:
        assert "error" in data
