# tests/test_status.py

from fastapi.testclient import TestClient

from hanuman.main import app

client = TestClient(app)


def test_status_endpoint() -> None:
    response = client.get("/status")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert "version" in response.json()


def test_status_ping() -> None:
    response = client.get("/status/ping")
    assert response.status_code == 200
    assert response.json() == {"ok": True}
