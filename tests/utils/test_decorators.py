import os
from typing import Any

import pytest
from starlette.requests import Request

# Configure required environment variables before importing the decorator module
for env_key, env_value in {
    "NOTION_TOKEN": "dummy-notion-token",
    "GITHUB_TOKEN": "dummy-github-token",
    "OPENAI_API_KEY": "dummy-openai",
    "GOOGLE_CLIENT_ID": "dummy-client-id",
    "GOOGLE_CLIENT_SECRET": "dummy-client-secret",
    "GOOGLE_REDIRECT_URI": "https://dummy.redirect",
}.items():
    os.environ.setdefault(env_key, env_value)

from hanuman.models.ping import PingResult  # noqa: E402
from hanuman.utils import decorators  # noqa: E402


class DummyLogger:
    def __init__(self) -> None:
        self.bound_kwargs: dict[str, Any] | None = None
        self.info_messages: list[str] = []
        self.error_messages: list[str] = []

    def bind(self, **kwargs: Any) -> "DummyLogger":
        self.bound_kwargs = kwargs
        return self

    def info(self, message: str) -> None:
        self.info_messages.append(message)

    def error(self, message: str) -> None:
        self.error_messages.append(message)


async def _receive() -> dict[str, object]:
    return {"type": "http.request", "body": b"", "more_body": False}


def _make_request(method: str = "GET", path: str = "/hello") -> Request:
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": method,
        "path": path,
        "raw_path": path.encode(),
        "headers": [],
        "scheme": "http",
        "client": ("198.51.100.5", 4242),
        "server": ("testserver", 80),
        "query_string": b"",
    }
    return Request(scope, _receive)


def test_trace_endpoint_sync_ping_result(monkeypatch: pytest.MonkeyPatch) -> None:
    dummy_logger = DummyLogger()
    monkeypatch.setattr(decorators, "get_logger", lambda source: dummy_logger)

    @decorators.trace_endpoint("sync-test")
    def sample_endpoint(request: Request) -> PingResult:
        return PingResult(ok=True, source="sync-test")

    response = sample_endpoint(_make_request())

    assert response.ok is True
    assert response.source == "sync-test"
    assert response.duration_ms is not None
    assert response.timestamp.tzinfo is not None

    assert dummy_logger.bound_kwargs == {
        "ip": "198.51.100.5",
        "endpoint": "/hello",
        "method": "GET",
        "debug_mode": decorators.settings.debug,
    }
    assert dummy_logger.info_messages == ["📥 Requête reçue"]


def test_trace_endpoint_sync_error_caught(monkeypatch: pytest.MonkeyPatch) -> None:
    dummy_logger = DummyLogger()
    monkeypatch.setattr(decorators, "get_logger", lambda source: dummy_logger)

    @decorators.trace_endpoint("sync-error")
    def failing_endpoint(request: Request) -> PingResult:
        raise ValueError("boom")

    response = failing_endpoint(_make_request())

    assert response.ok is False
    assert response.source == "sync-error"
    assert response.error == "boom"
    assert response.duration_ms is not None
    assert dummy_logger.error_messages[0].startswith("❌ Erreur ValueError dans sync-error")


def test_trace_endpoint_sync_non_ping_logs_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dummy_logger = DummyLogger()
    monkeypatch.setattr(decorators, "get_logger", lambda source: dummy_logger)

    @decorators.trace_endpoint("sync-success")
    def sample_endpoint(request: Request) -> str:
        return "ok"

    assert sample_endpoint(_make_request()) == "ok"
    assert dummy_logger.info_messages[0] == "📥 Requête reçue"
    assert dummy_logger.info_messages[1].startswith("✅ Exécution réussie : sync-success")


def test_trace_endpoint_async_respects_catch_false(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dummy_logger = DummyLogger()
    monkeypatch.setattr(decorators, "get_logger", lambda source: dummy_logger)

    @decorators.trace_endpoint("async-error", catch=False)
    async def failing_async(request: Request) -> None:
        raise RuntimeError("async boom")

    with pytest.raises(RuntimeError):
        import asyncio

        asyncio.run(failing_async(_make_request()))

    assert dummy_logger.bound_kwargs == {
        "ip": "198.51.100.5",
        "endpoint": "/hello",
        "method": "GET",
        "debug_mode": decorators.settings.debug,
    }
    assert dummy_logger.info_messages == ["📥 Requête reçue"]
    assert dummy_logger.error_messages[0].startswith("❌ Erreur RuntimeError dans async-error")
