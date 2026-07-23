from __future__ import annotations

from typing import Any, Dict, Tuple

import pytest
import requests

from hanuman.services.core.notion_service import (
    API_BASE_URL,
    NotionApiError,
    NotionAuthError,
    NotionPageRef,
    NotionService,
)


class DummyResponse:
    def __init__(
        self, status_code: int, json_data: Dict[str, Any] | None = None, text: str = ""
    ) -> None:
        self.status_code = status_code
        self._json_data = json_data or {}
        self.text = text

    def json(self) -> Dict[str, Any]:
        return self._json_data


# ---------------- helpers bas niveau (_url, _request) ---------------- #


def test_url_building() -> None:
    svc = NotionService(token="tok", api_base_url=API_BASE_URL, notion_version="2022-06-28")
    assert svc._url("pages") == f"{API_BASE_URL}/v1/pages"
    assert svc._url("/databases/123/query") == f"{API_BASE_URL}/v1/databases/123/query"


def test_request_success(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    def fake_request(
        method: str, url: str, headers: dict, json: dict | None, timeout: float
    ) -> DummyResponse:
        captured["method"] = method
        captured["url"] = url
        captured["headers"] = headers
        captured["json"] = json
        captured["timeout"] = timeout
        return DummyResponse(200, json_data={"ok": True})

    monkeypatch.setattr("hanuman.services.core.notion_service.requests.request", fake_request)

    svc = NotionService(token="tok", notion_version="2025-09-03")
    data = svc._request("POST", "pages", payload={"foo": "bar"})

    assert data == {"ok": True}
    assert captured["method"] == "POST"
    assert captured["url"] == f"{API_BASE_URL}/v1/pages"
    assert captured["json"] == {"foo": "bar"}


def test_request_unauthorized(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_request(
        method: str, url: str, headers: dict, json: dict | None, timeout: float
    ) -> DummyResponse:
        return DummyResponse(401, text="unauthorized")

    monkeypatch.setattr("hanuman.services.core.notion_service.requests.request", fake_request)

    svc = NotionService(token="bad")
    with pytest.raises(NotionAuthError):
        svc._request("GET", "pages/123")


def test_request_api_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_request(
        method: str, url: str, headers: dict, json: dict | None, timeout: float
    ) -> DummyResponse:
        return DummyResponse(404, text="not found")

    monkeypatch.setattr("hanuman.services.core.notion_service.requests.request", fake_request)

    svc = NotionService(token="tok")
    with pytest.raises(NotionApiError):
        svc._request("GET", "pages/does-not-exist")


def test_request_network_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_request(
        method: str, url: str, headers: dict, json: dict | None, timeout: float
    ) -> DummyResponse:
        raise requests.RequestException("boom")

    monkeypatch.setattr("hanuman.services.core.notion_service.requests.request", fake_request)

    svc = NotionService(token="tok")
    with pytest.raises(NotionApiError):
        svc._request("GET", "pages/any")


# ---------------- data_sources & query paths ---------------- #


def test_is_datasource_api_flag() -> None:
    svc_new = NotionService(token="tok", notion_version="2025-09-03")
    svc_old = NotionService(token="tok", notion_version="2022-06-28")
    assert svc_new._is_datasource_api() is True
    assert svc_old._is_datasource_api() is False


def test_get_data_source_id_for_database_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[Tuple[str, str]] = []

    def fake_request(
        self: NotionService, method: str, path: str, payload=None, timeout: float = 30.0
    ) -> Dict[str, Any]:
        calls.append((method, path))
        assert path == "databases/db123"
        return {
            "data_sources": [
                {"id": "ds_abc"},
            ]
        }

    svc = NotionService(token="tok", notion_version="2025-09-03")
    monkeypatch.setattr(svc, "_request", fake_request.__get__(svc, NotionService))

    ds_id = svc._get_data_source_id_for_database("db123")
    assert ds_id == "ds_abc"

    # Cache : second appel ne doit pas refaire de _request
    ds_id2 = svc._get_data_source_id_for_database("db123")
    assert ds_id2 == "ds_abc"
    assert len(calls) == 1


def test_get_data_source_id_for_database_no_datasource(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_request(
        self: NotionService, method: str, path: str, payload=None, timeout: float = 30.0
    ) -> Dict[str, Any]:
        return {
            "data_sources": [],
        }

    svc = NotionService(token="tok", notion_version="2025-09-03")
    monkeypatch.setattr(svc, "_request", fake_request.__get__(svc, NotionService))

    with pytest.raises(NotionApiError):
        svc._get_data_source_id_for_database("db123")


def test_query_path_for_database_datasource_vs_legacy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    svc_new = NotionService(token="tok", notion_version="2025-09-03")
    svc_old = NotionService(token="tok", notion_version="2022-06-28")

    monkeypatch.setattr(svc_new, "_get_data_source_id_for_database", lambda db: "ds_999")

    assert svc_new._query_path_for_database("db123") == "data_sources/ds_999/query"
    assert svc_old._query_path_for_database("db123") == "databases/db123/query"


# ---------------- pages & blocks ---------------- #


def test_create_page_under_parent_success(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    def fake_request(
        self: NotionService,
        method: str,
        path: str,
        payload: dict,
        timeout: float = 30.0,
    ) -> Dict[str, Any]:
        captured["method"] = method
        captured["path"] = path
        captured["payload"] = payload
        return {"id": "page123", "url": "https://notion.so/page123"}

    # On force NOTION_PARENT_ID via parent_page_id param → pas besoin de patcher la constante
    svc = NotionService(token="tok")
    monkeypatch.setattr(svc, "_request", fake_request.__get__(svc, NotionService))

    ref = svc.create_page_under_parent(
        title="Titre",
        blocks=[{"type": "paragraph"}],
        parent_page_id="parent123",
    )

    assert isinstance(ref, NotionPageRef)
    assert ref.page_id == "page123"
    assert ref.url == "https://notion.so/page123"
    assert captured["method"] == "POST"
    assert captured["path"] == "pages"
    assert captured["payload"]["parent"]["page_id"] == "parent123"
    assert captured["payload"]["properties"]["title"]["title"][0]["text"]["content"] == "Titre"
    assert captured["payload"]["children"] == [{"type": "paragraph"}]


def test_create_page_under_parent_missing_parent_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    svc = NotionService(token="tok")

    # On vide NOTION_PARENT_ID pour forcer l'erreur si parent_page_id est None
    monkeypatch.setattr("hanuman.services.core.notion_service.NOTION_PARENT_ID", "")

    with pytest.raises(NotionApiError):
        svc.create_page_under_parent("Titre", [], parent_page_id=None)


def test_create_page_in_database_success(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    def fake_request(
        self: NotionService,
        method: str,
        path: str,
        payload: dict,
        timeout: float = 30.0,
    ) -> Dict[str, Any]:
        captured["method"] = method
        captured["path"] = path
        captured["payload"] = payload
        return {"id": "page-in-db", "url": "https://notion.so/page-in-db"}

    svc = NotionService(token="tok")
    monkeypatch.setattr(svc, "_request", fake_request.__get__(svc, NotionService))

    ref = svc.create_page_in_database(
        database_id="db123",
        properties={"Name": {"title": [{"text": {"content": "Hello"}}]}},
        children=[{"type": "paragraph"}],
    )

    assert ref.page_id == "page-in-db"
    assert captured["path"] == "pages"
    assert captured["payload"]["parent"]["database_id"] == "db123"
    assert "children" in captured["payload"]


def test_append_blocks_with_empty_list_returns_empty_dict() -> None:
    svc = NotionService(token="tok")
    assert svc.append_blocks("page123", []) == {}


def test_append_blocks_success(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    def fake_request(
        self: NotionService,
        method: str,
        path: str,
        payload: dict,
        timeout: float = 30.0,
    ) -> Dict[str, Any]:
        captured["method"] = method
        captured["path"] = path
        captured["payload"] = payload
        return {"ok": True}

    svc = NotionService(token="tok")
    monkeypatch.setattr(svc, "_request", fake_request.__get__(svc, NotionService))

    blocks = [{"type": "paragraph"}]
    data = svc.append_blocks("block123", blocks)

    assert data == {"ok": True}
    assert captured["path"] == "blocks/block123/children"
    assert captured["payload"]["children"] == blocks


# ---------------- query_database & pagination ---------------- #


def test_query_database_single_page(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[dict[str, Any]] = []

    def fake_request(
        self: NotionService,
        method: str,
        path: str,
        payload: dict,
        timeout: float = 30.0,
    ) -> Dict[str, Any]:
        calls.append({"path": path, "payload": payload})
        return {
            "results": [{"id": "row1"}],
            "has_more": False,
        }

    svc = NotionService(token="tok", notion_version="2022-06-28")
    monkeypatch.setattr(svc, "_request", fake_request.__get__(svc, NotionService))

    rows = svc.query_database("db123", filter_={"property": "X"})
    assert rows == [{"id": "row1"}]
    assert calls[0]["path"] == "databases/db123/query"
    assert calls[0]["payload"]["filter"] == {"property": "X"}


def test_query_database_pagination(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[dict[str, Any]] = []

    def fake_request(
        self: NotionService,
        method: str,
        path: str,
        payload: dict,
        timeout: float = 30.0,
    ) -> Dict[str, Any]:
        calls.append(payload)
        if "start_cursor" not in payload:
            return {
                "results": [{"id": "r1"}],
                "has_more": True,
                "next_cursor": "cursor-2",
            }
        return {
            "results": [{"id": "r2"}],
            "has_more": False,
        }

    svc = NotionService(token="tok", notion_version="2025-09-03")
    monkeypatch.setattr(svc, "_query_path_for_database", lambda db_id: "data_sources/ds/query")
    monkeypatch.setattr(svc, "_request", fake_request.__get__(svc, NotionService))

    rows = svc.query_database("db123")
    assert rows == [{"id": "r1"}, {"id": "r2"}]
    assert calls[0] == {}  # premier appel sans start_cursor
    assert calls[1]["start_cursor"] == "cursor-2"


# ---------------- update_page_properties, retrieve_page, search ---------------- #


def test_update_page_properties(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    def fake_request(
        self: NotionService,
        method: str,
        path: str,
        payload: dict,
        timeout: float = 30.0,
    ) -> Dict[str, Any]:
        captured["method"] = method
        captured["path"] = path
        captured["payload"] = payload
        return {"id": "page123"}

    svc = NotionService(token="tok")
    monkeypatch.setattr(svc, "_request", fake_request.__get__(svc, NotionService))

    props = {"Name": {"title": [{"text": {"content": "Updated"}}]}}
    data = svc.update_page_properties("page123", props)

    assert data["id"] == "page123"
    assert captured["path"] == "pages/page123"
    assert captured["payload"]["properties"] == props


def test_retrieve_page(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_request(
        self: NotionService, method: str, path: str, payload=None, timeout: float = 30.0
    ) -> Dict[str, Any]:
        return {"id": "page123", "object": "page"}

    svc = NotionService(token="tok")
    monkeypatch.setattr(svc, "_request", fake_request.__get__(svc, NotionService))

    data = svc.retrieve_page("page123")
    assert data["id"] == "page123"
    assert data["object"] == "page"


def test_search(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    def fake_request(
        self: NotionService,
        method: str,
        path: str,
        payload: dict,
        timeout: float = 30.0,
    ) -> Dict[str, Any]:
        captured["path"] = path
        captured["payload"] = payload
        return {"results": [{"id": "x"}]}

    svc = NotionService(token="tok")
    monkeypatch.setattr(svc, "_request", fake_request.__get__(svc, NotionService))

    data = svc.search("hello", limit=10)
    assert data["results"][0]["id"] == "x"
    assert captured["path"] == "search"
    assert captured["payload"]["query"] == "hello"
    assert captured["payload"]["page_size"] == 10
