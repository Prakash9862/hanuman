# tests/test_ping_endpoints.py

import pytest
from fastapi.testclient import TestClient

from hanuman.main import app

client = TestClient(app)

# 🔁 Liste de tous les endpoints de ping + status
PING_ENDPOINTS = [
    "/status",
    "/calendar/ping",
    "/chess/ping",
    "/github/ping",
    "/notion/ping",
    "/obsidian/ping",
    "/openai/ping",
    "/wikipedia/ping",
]


@pytest.mark.parametrize("endpoint", PING_ENDPOINTS)
def test_ping_endpoint_response(endpoint: str) -> None:
    response = client.get(endpoint)
    assert response.status_code == 200
    data = response.json()

    if endpoint == "/status":
        assert data["status"] == "ok"
        assert "version" in data
        return

    assert "ok" in data
    if data["ok"]:
        assert "timestamp" in data
        assert "duration_ms" in data
