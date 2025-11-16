from __future__ import annotations

from typing import Any, Dict, List, Tuple

import pytest

from hanuman.services.core import notion_service as ns


def _make_notion(token: str = "dummy", version: str = "2025-09-03") -> ns.NotionService:
    """
    Crée une instance de NotionService sans toucher au vrai NOTION_TOKEN.
    """
    return ns.NotionService(token=token, notion_version=version)


def test_query_database_uses_legacy_endpoint_for_old_versions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Si la version Notion ne commence pas par '2025-',
    query_database doit appeler databases/{db_id}/query.
    """
    calls: List[Tuple[str, str, Dict[str, Any]]] = []

    def fake_request(
        method: str, path: str, payload: Dict[str, Any] | None = None
    ) -> Dict[str, Any]:
        calls.append((method, path, payload or {}))
        # On simule une seule "page" de résultats
        return {"results": [{"id": "page-1"}], "has_more": False}

    notion = _make_notion(version="2022-06-28")
    monkeypatch.setattr(notion, "_request", fake_request)  # type: ignore[arg-type]

    results = notion.query_database("db123", filter_={"property": "Name"})

    assert len(results) == 1
    assert calls, "Aucun appel API enregistré"
    # Un seul POST sur l'ancien endpoint
    method, path, payload = calls[0]
    assert method == "POST"
    assert path == "databases/db123/query"
    assert "filter" in payload


def test_query_database_uses_datasource_endpoint_for_2025_version(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    En version 2025-09-03, query_database doit :

    - faire un GET databases/{db_id} pour trouver data_sources[0].id
    - faire un POST data_sources/{ds_id}/query
    """
    calls: List[Tuple[str, str, Dict[str, Any]]] = []

    def fake_request(
        method: str, path: str, payload: Dict[str, Any] | None = None
    ) -> Dict[str, Any]:
        calls.append((method, path, payload or {}))

        if method == "GET" and path == "databases/db456":
            return {
                "id": "db456",
                "data_sources": [
                    {"id": "ds-abc"},
                ],
            }

        if method == "POST" and path == "data_sources/ds-abc/query":
            return {
                "results": [{"id": "page-xyz"}],
                "has_more": False,
            }

        pytest.fail(f"Appel inattendu: {method} {path}")

    notion = _make_notion(version="2025-09-03")
    monkeypatch.setattr(notion, "_request", fake_request)  # type: ignore[arg-type]

    results = notion.query_database("db456")

    assert len(results) == 1
    assert len(calls) == 2

    # 1) GET databases/db456
    assert calls[0][0] == "GET"
    assert calls[0][1] == "databases/db456"

    # 2) POST data_sources/ds-abc/query
    assert calls[1][0] == "POST"
    assert calls[1][1] == "data_sources/ds-abc/query"


def test_get_data_source_id_is_cached(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    _get_data_source_id_for_database doit remplir le cache, pour éviter plusieurs GET.
    """
    notion = _make_notion(version="2025-09-03")

    calls: List[Tuple[str, str, Dict[str, Any]]] = []

    def fake_request(
        method: str, path: str, payload: Dict[str, Any] | None = None
    ) -> Dict[str, Any]:
        calls.append((method, path, payload or {}))
        assert method == "GET"
        assert path == "databases/db789"
        return {
            "id": "db789",
            "data_sources": [
                {"id": "ds-cache"},
            ],
        }

    monkeypatch.setattr(notion, "_request", fake_request)  # type: ignore[arg-type]

    # 1er appel → fait un GET et remplit le cache
    ds1 = notion._get_data_source_id_for_database("db789")
    # 2e appel → doit lire le cache, sans refaire de GET
    ds2 = notion._get_data_source_id_for_database("db789")

    assert ds1 == "ds-cache"
    assert ds2 == "ds-cache"
    # Un seul GET attendu
    assert len(calls) == 1
