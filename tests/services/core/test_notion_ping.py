from types import SimpleNamespace

from fastapi.testclient import TestClient

import hanuman.api.core.notion as notion_api
from hanuman.main import app

client = TestClient(app)


def _mock_response(status_code: int, json_data: dict | None = None, text: str = "") -> object:
    return SimpleNamespace(
        status_code=status_code,
        text=text,
        json=lambda: json_data or {},
    )


def test_notion_ping(monkeypatch) -> None:
    """Cas sans token → ok=False."""
    monkeypatch.delenv("NOTION_TOKEN", raising=False)

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


def test_notion_ping_success(monkeypatch) -> None:
    """Cas où l'API renvoie un utilisateur valide."""
    monkeypatch.setenv("NOTION_TOKEN", "super-secret")
    monkeypatch.setenv("NOTION_VERSION", "2025-10-05")

    captured_headers: dict = {}

    def fake_get(url: str, *, headers: dict, timeout: int) -> object:
        captured_headers.update(headers)
        assert url.endswith("/users/me")
        assert timeout == 10
        return _mock_response(200, {"bot": {"workspace": "Workspace"}})

    monkeypatch.setattr(notion_api.requests, "get", fake_get)

    response = client.get("/notion/ping")
    data = response.json()

    assert data["ok"] is True
    assert data["status"] == 200
    assert data["detail"]["user"] == {"bot": {"workspace": "Workspace"}}
    assert captured_headers["Authorization"] == "Bearer super-secret"
    assert captured_headers["Notion-Version"] == "2025-10-05"


def test_notion_ping_http_failure(monkeypatch) -> None:
    """Cas HTTP 403."""
    monkeypatch.setenv("NOTION_TOKEN", "token")

    def fake_get(url: str, *, headers: dict, timeout: int) -> object:
        return _mock_response(403, text="forbidden")

    monkeypatch.setattr(notion_api.requests, "get", fake_get)

    response = client.get("/notion/ping")
    data = response.json()

    assert data["ok"] is False
    assert data["status"] == 403
    assert "Notion API request failed" in data["error"]
    assert data["body"] == "forbidden"


def test_notion_ping_exception(monkeypatch) -> None:
    """Cas d'exception Python."""
    monkeypatch.setenv("NOTION_TOKEN", "token")

    def fake_get(url: str, *, headers: dict, timeout: int):
        raise TimeoutError("boom")

    monkeypatch.setattr(notion_api.requests, "get", fake_get)

    response = client.get("/notion/ping")
    data = response.json()

    assert data["ok"] is False
    assert data["error"] == "boom"
