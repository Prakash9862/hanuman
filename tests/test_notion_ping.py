from fastapi.testclient import TestClient

from hanuman.main import app

client = TestClient(app)


def test_notion_ping() -> None:
    response = client.get("/notion/ping")
    data = response.json()

    assert "ok" in data
    assert "timestamp" in data
    assert "source" in data
    assert data["source"] == "notion"

    if data["ok"]:
        assert "detail" in data
        assert "user" in data["detail"]
        assert isinstance(data["detail"]["user"], dict)
    else:
        assert "error" in data
