from __future__ import annotations

from dataclasses import dataclass

import pytest
from fastapi import HTTPException

from hanuman.api.routers import resources


def test_youtube_status_reflects_configuration(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(resources, "youtube_configured", lambda: False)
    assert resources.youtube_status() == {
        "ok": False,
        "configured": False,
        "message": "YOUTUBE_API_KEY absente",
    }


def test_youtube_search_returns_page_metadata(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        resources,
        "search_youtube",
        lambda *args, **kwargs: {
            "results": [{"id": "one"}],
            "next_page_token": "next",
            "prev_page_token": None,
            "total_results": 12,
        },
    )

    result = resources.youtube_search("query", 10, "page")

    assert result["count"] == 1
    assert result["next_page_token"] == "next"
    assert result["total_results"] == 12


@pytest.mark.parametrize(
    ("error", "status", "detail"),
    [
        (ValueError("missing key"), 400, "missing key"),
        (RuntimeError("timeout"), 502, "Erreur YouTube : timeout"),
    ],
)
def test_youtube_search_maps_service_errors(
    monkeypatch: pytest.MonkeyPatch, error: Exception, status: int, detail: str
) -> None:
    monkeypatch.setattr(
        resources,
        "search_youtube",
        lambda *args, **kwargs: (_ for _ in ()).throw(error),
    )

    with pytest.raises(HTTPException) as caught:
        resources.youtube_search("query")

    assert caught.value.status_code == status
    assert caught.value.detail == detail


def test_gallica_search_returns_browser_fallback_on_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(resources, "build_gallica_search_url", lambda query: "fallback")
    monkeypatch.setattr(
        resources,
        "search_gallica",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("offline")),
    )

    result = resources.gallica_search("query")

    assert result["ok"] is False
    assert result["fallback_url"] == "fallback"
    assert "offline" in str(result["message"])


def test_simple_resource_endpoints_delegate_and_count(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(resources, "search_gallica", lambda *args, **kwargs: [{"id": 1}])
    monkeypatch.setattr(resources, "build_gallica_search_url", lambda query: "gallica")
    monkeypatch.setattr(resources, "search_imslp", lambda *args, **kwargs: [{"id": 2}])
    monkeypatch.setattr(resources, "build_google_maps_search_url", lambda value: "map")
    monkeypatch.setattr(resources, "build_google_maps_directions_url", lambda value: "directions")

    assert resources.gallica_status()["mode"] == "sru_with_browser_fallback"
    assert resources.gallica_search("query")["count"] == 1
    assert resources.imslp_status()["mode"] == "mediawiki_api"
    assert resources.imslp_search("query")["count"] == 1
    assert resources.maps_status()["mode"] == "universal_urls"
    assert resources.maps_search("Paris")["url"] == "map"
    assert resources.maps_directions("Paris")["url"] == "directions"


def test_imslp_search_maps_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        resources,
        "search_imslp",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("offline")),
    )

    with pytest.raises(HTTPException) as caught:
        resources.imslp_search("query")

    assert caught.value.status_code == 502
    assert caught.value.detail == "Erreur IMSLP : offline"


def test_program_and_chess_queue_endpoints_delegate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        resources,
        "inspect_programs",
        lambda: [{"id": "one", "ok": True}, {"id": "two", "ok": False}],
    )
    monkeypatch.setattr(resources, "inspect_program", lambda program_id: {"id": program_id})
    monkeypatch.setattr(resources, "count_analysis_queue", lambda: 4)
    monkeypatch.setattr(resources, "get_analysis_queue_status", lambda: {"running": True})
    monkeypatch.setattr(resources, "start_analysis_queue", lambda **kwargs: {"started": kwargs})
    monkeypatch.setattr(resources, "stop_analysis_queue", lambda: {"stopped": True})

    assert resources.programs_status()["ok"] is False
    assert resources.program_status("one") == {"id": "one"}
    assert resources.chess_analysis_status()["queue"] == 4
    assert resources.chess_analysis_start(14, 8) == {"started": {"depth": 14, "limit": 8}}
    assert resources.chess_analysis_stop() == {"stopped": True}


def test_program_status_maps_unknown_id_to_not_found(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        resources,
        "inspect_program",
        lambda program_id: (_ for _ in ()).throw(KeyError(program_id)),
    )

    with pytest.raises(HTTPException) as caught:
        resources.program_status("missing")

    assert caught.value.status_code == 404


@dataclass
class FakeReport:
    notes_discovered: int = 5
    analyses_valid: int = 3
    games_pending: int = 2
    analyses_invalid: int = 1
    analyses_orphaned: int = 4
    views_written: int = 6
    opening_indexes_written: int = 7


def test_chess_knowledge_refresh_serializes_report(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(resources, "_validated_chess_root", lambda: "root")
    monkeypatch.setattr(resources, "refresh_chess_knowledge", lambda root: FakeReport())

    result = resources.chess_knowledge_refresh()

    assert result["report"] == {
        "games_found": 5,
        "analyses_valid": 3,
        "games_pending": 2,
        "analyses_invalid": 1,
        "analyses_orphaned": 4,
        "views_written": 6,
        "opening_indexes_written": 7,
    }


def test_chess_knowledge_refresh_maps_expected_failures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        resources,
        "_validated_chess_root",
        lambda: (_ for _ in ()).throw(OSError("vault unavailable")),
    )

    with pytest.raises(HTTPException) as caught:
        resources.chess_knowledge_refresh()

    assert caught.value.status_code == 500
    assert "vault unavailable" in str(caught.value.detail)
