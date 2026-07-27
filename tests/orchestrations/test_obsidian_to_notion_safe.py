from __future__ import annotations

import io
import json
import urllib.error
from pathlib import Path
from typing import Any

import pytest

from hanuman.orchestrations import obsidian_to_notion_safe as safe


def test_chunks_preserves_all_values() -> None:
    values = [{"n": index} for index in range(205)]
    chunks = list(safe._chunks(values, 100))
    assert [len(chunk) for chunk in chunks] == [100, 100, 5]
    assert [item for chunk in chunks for item in chunk] == values


@pytest.mark.parametrize(
    ("payload", "expected"),
    [
        (b'{"message": "bad parent"}', "bad parent"),
        (b'{"code": "validation_error"}', "validation_error"),
        (b'["unexpected", "payload"]', "['unexpected', 'payload']"),
        (b"plain failure", "plain failure"),
    ],
)
def test_decode_http_error_extracts_useful_detail(payload: bytes, expected: str) -> None:
    error = urllib.error.HTTPError(
        "https://api.notion.test", 400, "Bad Request", {}, io.BytesIO(payload)
    )
    assert safe._decode_http_error(error) == expected


def test_request_json_builds_request_and_decodes_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    class Response:
        def __enter__(self) -> Response:
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def read(self) -> bytes:
            return b'{"id": "page"}'

    def fake_urlopen(request: Any, timeout: int) -> Response:
        captured["request"] = request
        captured["timeout"] = timeout
        return Response()

    monkeypatch.setattr(safe.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(safe, "_notion_headers", lambda: {"Authorization": "Bearer test"})

    assert safe._request_json("https://api.test", "POST", {"name": "value"}) == {"id": "page"}
    assert captured["request"].method == "POST"
    assert json.loads(captured["request"].data) == {"name": "value"}
    assert captured["timeout"] == 30


def test_request_json_rejects_non_object_response(monkeypatch: pytest.MonkeyPatch) -> None:
    class Response:
        def __enter__(self) -> Response:
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def read(self) -> bytes:
            return b"[]"

    monkeypatch.setattr(safe.urllib.request, "urlopen", lambda *args, **kwargs: Response())

    with pytest.raises(RuntimeError, match="inattendue"):
        safe._request_json("https://api.test", "POST", {})


def test_request_json_wraps_http_error(monkeypatch: pytest.MonkeyPatch) -> None:
    error = urllib.error.HTTPError(
        "https://api.test",
        429,
        "Too Many Requests",
        {},
        io.BytesIO(b'{"message": "slow down"}'),
    )
    monkeypatch.setattr(
        safe.urllib.request,
        "urlopen",
        lambda *args, **kwargs: (_ for _ in ()).throw(error),
    )

    with pytest.raises(RuntimeError, match="Notion API 429: slow down"):
        safe._request_json("https://api.test", "POST", {})


def test_create_page_batches_children_after_creation(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, str, dict[str, Any]]] = []

    def fake_request(url: str, method: str, body: dict[str, Any]) -> dict[str, Any]:
        calls.append((url, method, body))
        return {"id": "page-id"}

    monkeypatch.setattr(safe, "_request_json", fake_request)
    children = [{"n": index} for index in range(205)]

    page = safe._create_page({"parent": {}, "children": children})

    assert page == {"id": "page-id"}
    assert [len(call[2]["children"]) for call in calls] == [100, 100, 5]
    assert [call[1] for call in calls] == ["POST", "PATCH", "PATCH"]
    assert calls[1][0].endswith("/blocks/page-id/children")


def test_create_page_requires_page_id(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(safe, "_request_json", lambda *args: {})
    with pytest.raises(RuntimeError, match="sans identifiant"):
        safe._create_page({"children": []})


def test_send_retries_with_alternative_parent_type(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    markdown = tmp_path / "note.md"
    markdown.write_text("# Note", encoding="utf-8")
    parent_types: list[bool] = []

    def fake_build(**kwargs: Any) -> dict[str, Any]:
        parent_types.append(kwargs["parent_is_db"])
        return {"parent_is_db": kwargs["parent_is_db"]}

    attempts = 0

    def fake_create(body: dict[str, Any]) -> dict[str, Any]:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise RuntimeError("parent should be a database_id")
        return {"id": "page"}

    monkeypatch.setattr(safe, "sanitize_markdown_for_notion", lambda value: value)
    monkeypatch.setattr(safe, "split_frontmatter", lambda value: ({}, value))
    monkeypatch.setattr(safe, "build_notion_body", fake_build)
    monkeypatch.setattr(safe, "_create_page", fake_create)

    assert safe.send_markdown_to_notion_safe(str(markdown), "parent") == {"id": "page"}
    assert parent_types == [False, True]


def test_send_does_not_retry_unrelated_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    markdown = tmp_path / "note.md"
    markdown.write_text("# Note", encoding="utf-8")
    monkeypatch.setattr(safe, "sanitize_markdown_for_notion", lambda value: value)
    monkeypatch.setattr(safe, "split_frontmatter", lambda value: ({}, value))
    monkeypatch.setattr(safe, "build_notion_body", lambda **kwargs: {})
    monkeypatch.setattr(
        safe,
        "_create_page",
        lambda body: (_ for _ in ()).throw(RuntimeError("rate limited")),
    )

    with pytest.raises(RuntimeError, match="rate limited"):
        safe.send_markdown_to_notion_safe(str(markdown), "parent")


def test_send_reports_second_parent_type_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    markdown = tmp_path / "note.md"
    markdown.write_text("# Note", encoding="utf-8")
    errors = iter(
        [
            RuntimeError("parent type is a database"),
            RuntimeError("alternative rejected"),
        ]
    )
    monkeypatch.setattr(safe, "sanitize_markdown_for_notion", lambda value: value)
    monkeypatch.setattr(safe, "split_frontmatter", lambda value: ({}, value))
    monkeypatch.setattr(safe, "build_notion_body", lambda **kwargs: {})
    monkeypatch.setattr(safe, "_create_page", lambda body: (_ for _ in ()).throw(next(errors)))

    with pytest.raises(RuntimeError, match="alternative rejected"):
        safe.send_markdown_to_notion_safe(str(markdown), "parent")
