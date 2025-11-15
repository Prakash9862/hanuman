from starlette.requests import Request

from hanuman.utils.log_helpers import get_ip, get_method, get_path


def _make_request(
    method: str = "GET",
    path: str = "/hello",
    client: tuple[str, int] | None = ("203.0.113.1", 1234),
) -> Request:
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": method,
        "path": path,
        "raw_path": path.encode(),
        "headers": [],
        "scheme": "http",
        "client": client,
        "server": ("testserver", 80),
        "query_string": b"",
    }

    async def receive() -> dict[str, object]:
        return {"type": "http.request", "body": b"", "more_body": False}

    return Request(scope, receive)


def test_get_ip_without_request_returns_no_request() -> None:
    assert get_ip(None) == "no-request"


def test_get_ip_without_client_returns_no_client() -> None:
    request = _make_request(client=None)
    assert get_ip(request) == "no-client"


def test_log_helper_extractors_with_request() -> None:
    request = _make_request(method="POST", path="/api/ping")
    assert get_ip(request) == "203.0.113.1"
    assert get_method(request) == "POST"
    assert get_path(request) == "/api/ping"
