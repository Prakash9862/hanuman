from fastapi.testclient import TestClient

from hanuman.main import app

client = TestClient(app)


def test_github_ping() -> None:
    response = client.get("/github/ping")
    data = response.json()

    assert "ok" in data
    assert "timestamp" in data
    assert "source" in data
    assert data["source"] == "github"

    if data["ok"]:
        assert "detail" in data
        assert "login" in data["detail"]
    else:
        assert "error" in data
