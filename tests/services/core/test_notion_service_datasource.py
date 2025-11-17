from __future__ import annotations

from typing import Any, Dict, List

import pytest

from hanuman.services.core.notion_service import NotionApiError, NotionService


def test_get_data_source_id_is_cached(monkeypatch: Any) -> None:
    """_get_data_source_id_for_database should fetch once and then reuse the cache."""

    calls: List[Dict[str, Any]] = []

    def fake_request(
        self: NotionService,
        method: str,
        path: str,
        payload: Dict[str, Any] | None = None,
        timeout: float = 30.0,
    ) -> Dict[str, Any]:
        calls.append({"method": method, "path": path, "payload": payload})
        return {"data_sources": [{"id": "ds-123"}]}

    monkeypatch.setattr(NotionService, "_request", fake_request)
    service = NotionService(token="dummy", notion_version="2025-09-03")

    first = service._get_data_source_id_for_database("db-abc")
    second = service._get_data_source_id_for_database("db-abc")

    assert first == "ds-123"
    assert second == "ds-123"
    assert calls == [
        {"method": "GET", "path": "databases/db-abc", "payload": None},
    ]


def test_query_path_uses_datasource_endpoint(monkeypatch: Any) -> None:
    """When using a 2025+ Notion API version, queries go through the data source endpoint."""

    service = NotionService(token="dummy", notion_version="2025-09-03")
    monkeypatch.setattr(
        service,
        "_get_data_source_id_for_database",
        lambda db_id: (
            "ds-999"
            if db_id == "db-xyz"
            else pytest.fail("Unexpected database id passed to helper")
        ),
    )

    assert service._query_path_for_database("db-xyz") == "data_sources/ds-999/query"


def test_get_data_source_id_errors_without_sources(monkeypatch: Any) -> None:
    """The helper should raise a clear error when Notion returns no data_sources."""

    def fake_request(
        self: NotionService,
        method: str,
        path: str,
        payload: Dict[str, Any] | None = None,
        timeout: float = 30.0,
    ) -> Dict[str, Any]:
        return {"data_sources": []}

    monkeypatch.setattr(NotionService, "_request", fake_request)
    service = NotionService(token="dummy", notion_version="2025-09-03")

    with pytest.raises(NotionApiError):
        service._get_data_source_id_for_database("db-no-source")
