import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from hanuman.main import app
from hanuman.services.core import openai_service

client = TestClient(app)


class DummyResponse:
    def __init__(self, status_code: int, payload: dict | None = None) -> None:
        self.status_code = status_code
        self._payload = payload or {}

    def json(self) -> dict:
        return self._payload


def test_openai_ping() -> None:
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


def test_ping_openai_returns_model_count(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(openai_service.settings, "openai_api_key", SecretStr("unit-test-token"))

    def fake_get(url: str, headers: dict, timeout: int) -> DummyResponse:
        assert url == openai_service.OPENAI_API_URL
        assert timeout == 5
        assert headers["Authorization"] == "Bearer **********"
        return DummyResponse(200, payload={"data": [1, 2, 3, 4]})

    monkeypatch.setattr(openai_service.httpx, "get", fake_get)

    result = openai_service.ping_openai()

    assert result.ok is True
    assert result.source == "openai"
    assert result.detail == {"model_count": 4}


def test_ping_openai_handles_unauthorized(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(openai_service.settings, "openai_api_key", SecretStr("unit-test-token"))
    monkeypatch.setattr(
        openai_service.httpx,
        "get",
        lambda *_, **__: DummyResponse(401),
    )

    result = openai_service.ping_openai()

    assert result.ok is False
    assert result.source == "openai"
    assert result.error == "Unauthorized"
    assert result.detail is None


def test_ping_openai_handles_missing_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(openai_service.settings, "openai_api_key", None)

    result = openai_service.ping_openai()

    assert result.ok is False
    assert result.source == "openai"
    assert result.detail is None
    assert result.error == "Missing token"


def test_ping_openai_handles_unexpected_status(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(openai_service.settings, "openai_api_key", SecretStr("unit-test-token"))
    monkeypatch.setattr(
        openai_service.httpx,
        "get",
        lambda *_, **__: DummyResponse(500),
    )

    result = openai_service.ping_openai()

    assert result.ok is False
    assert result.source == "openai"
    assert result.error == "Unexpected status: 500"
    assert result.detail is None
