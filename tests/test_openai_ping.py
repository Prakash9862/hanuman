from fastapi.testclient import TestClient

from hanuman.main import app

client = TestClient(app)


def test_openai_ping():
    response = client.get("/openai/ping")
    data = response.json()

    assert "ok" in data
    assert "timestamp" in data
    assert "source" in data
    assert data["source"] == "openai"

    if data["ok"]:
        assert "detail" in data
        assert "model_count" in data["detail"]
        assert isinstance(data["detail"]["model_count"], int)
    else:
        assert "error" in data
