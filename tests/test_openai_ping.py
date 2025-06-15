# tests/test_openai_ping.py

from fastapi.testclient import TestClient

from hanuman.main import app

client = TestClient(app)


def test_openai_ping():
    response = client.get("/openai/ping")
    data = response.json()

    assert "ok" in data

    if data["ok"]:
        assert "model_count" in data
        assert isinstance(data["model_count"], int)
    else:
        assert "error" in data
