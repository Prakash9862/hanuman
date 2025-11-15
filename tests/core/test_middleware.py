from __future__ import annotations

import pytest
from starlette.requests import Request
from starlette.responses import Response

from hanuman.core import middleware


class DummyLogger:
    def __init__(self) -> None:
        self.messages: list[object] = []

    def info(self, message: object) -> None:
        self.messages.append(message)


@pytest.mark.asyncio
async def test_log_requests_logs_incoming_and_outgoing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dummy_logger = DummyLogger()
    monkeypatch.setattr(middleware, "logger", dummy_logger)

    scope = {
        "type": "http",
        "http_version": "1.1",
        "method": "GET",
        "path": "/example",
        "root_path": "",
        "scheme": "http",
        "server": ("testserver", 80),
        "client": ("127.0.0.1", 12345),
        "headers": [],
        "query_string": b"",
        "extensions": {},
    }

    async def receive() -> dict[str, object]:
        return {"type": "http.request", "body": b"", "more_body": False}

    request = Request(scope, receive)

    async def call_next(passed_request: Request) -> Response:
        assert passed_request is request
        return Response(content="ok", status_code=204)

    response = await middleware.log_requests(request, call_next)

    assert response.status_code == 204
    assert dummy_logger.messages == [
        "Requête reçue",
        {
            "method": "GET",
            "url": "http://testserver/example",
            "event": "Requête entrante",
        },
        {"status_code": 204, "event": "Réponse sortante"},
    ]
