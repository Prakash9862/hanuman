from __future__ import annotations

from typing import Any

import pytest

from hanuman.services import resources_service as service


class FakeResponse:
    def __init__(
        self,
        *,
        json_payload: dict[str, Any] | None = None,
        text: str = "",
    ) -> None:
        self._json_payload = json_payload or {}
        self.text = text
        self.raise_for_status_called = False

    def raise_for_status(self) -> None:
        self.raise_for_status_called = True

    def json(self) -> dict[str, Any]:
        return self._json_payload


def test_youtube_configured_depends_on_api_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("YOUTUBE_API_KEY", raising=False)
    assert service.youtube_configured() is False

    monkeypatch.setenv("YOUTUBE_API_KEY", "secret")
    assert service.youtube_configured() is True


def test_search_youtube_requires_configuration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("YOUTUBE_API_KEY", raising=False)

    with pytest.raises(ValueError, match="YOUTUBE_API_KEY"):
        service.search_youtube("Massenet")


def test_search_youtube_maps_results_and_pagination(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("YOUTUBE_API_KEY", "secret")
    captured: dict[str, Any] = {}

    response = FakeResponse(
        json_payload={
            "items": [
                {
                    "id": {"videoId": "abc123"},
                    "snippet": {
                        "title": "Thaïs",
                        "description": "Méditation",
                        "channelTitle": "Opera Channel",
                        "publishedAt": "2026-01-01T00:00:00Z",
                        "thumbnails": {"medium": {"url": "https://example.test/thumbnail.jpg"}},
                    },
                },
                {
                    "id": {},
                    "snippet": {"title": "Résultat sans vidéo"},
                },
            ],
            "nextPageToken": "next",
            "prevPageToken": "previous",
            "pageInfo": {"totalResults": 42},
        }
    )

    def fake_get(url: str, **kwargs: Any) -> FakeResponse:
        captured["url"] = url
        captured.update(kwargs)
        return response

    monkeypatch.setattr(service.httpx, "get", fake_get)

    result = service.search_youtube(
        "Massenet",
        max_results=100,
        page_token="page-2",
    )

    assert response.raise_for_status_called is True
    assert captured["url"] == service.YOUTUBE_SEARCH_URL
    assert captured["params"]["maxResults"] == 50
    assert captured["params"]["pageToken"] == "page-2"
    assert captured["params"]["key"] == "secret"

    assert result == {
        "results": [
            {
                "id": "abc123",
                "title": "Thaïs",
                "description": "Méditation",
                "channel": "Opera Channel",
                "published_at": "2026-01-01T00:00:00Z",
                "thumbnail": "https://example.test/thumbnail.jpg",
                "url": "https://www.youtube.com/watch?v=abc123",
            }
        ],
        "next_page_token": "next",
        "prev_page_token": "previous",
        "total_results": 42,
    }


def test_search_youtube_enforces_minimum_result_count(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("YOUTUBE_API_KEY", "secret")
    captured: dict[str, Any] = {}

    def fake_get(url: str, **kwargs: Any) -> FakeResponse:
        captured.update(kwargs)
        return FakeResponse(json_payload={})

    monkeypatch.setattr(service.httpx, "get", fake_get)

    service.search_youtube("test", max_results=-4)

    assert captured["params"]["maxResults"] == 1
    assert "pageToken" not in captured["params"]


def test_build_gallica_search_url_encodes_query() -> None:
    url = service.build_gallica_search_url('Ambroise Thomas "Hamlet"')

    assert url.startswith(service.GALLICA_SEARCH_URL + "?")
    assert "maximumRecords=25" in url
    assert "Ambroise" in url
    assert "%22Hamlet%22" in url


def test_search_gallica_parses_records(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    xml = """<?xml version="1.0" encoding="UTF-8"?>
    <searchRetrieveResponse
        xmlns:srw="http://www.loc.gov/zing/srw/"
        xmlns:dc="http://purl.org/dc/elements/1.1/">
      <srw:records>
        <srw:record>
          <srw:recordData>
            <dc:title>Partition de Thaïs</dc:title>
            <dc:creator>Jules Massenet</dc:creator>
            <dc:date>1894</dc:date>
            <dc:type>partition</dc:type>
            <dc:identifier>https://gallica.bnf.fr/ark:/12148/test</dc:identifier>
          </srw:recordData>
        </srw:record>
        <srw:record>
          <srw:recordData>
            <dc:creator>Auteur inconnu</dc:creator>
          </srw:recordData>
        </srw:record>
      </srw:records>
    </searchRetrieveResponse>
    """
    captured: dict[str, Any] = {}
    response = FakeResponse(text=xml)

    def fake_get(url: str, **kwargs: Any) -> FakeResponse:
        captured["url"] = url
        captured.update(kwargs)
        return response

    monkeypatch.setattr(service.httpx, "get", fake_get)

    result = service.search_gallica("Massenet", max_results=100)

    assert response.raise_for_status_called is True
    assert captured["url"] == service.GALLICA_SRU_URL
    assert captured["params"]["maximumRecords"] == 25
    assert result == [
        {
            "title": "Partition de Thaïs",
            "creators": ["Jules Massenet"],
            "dates": ["1894"],
            "types": ["partition"],
            "ark": "https://gallica.bnf.fr/ark:/12148/test",
            "url": "https://gallica.bnf.fr/ark:/12148/test",
        },
        {
            "title": "Document sans titre",
            "creators": ["Auteur inconnu"],
            "dates": [],
            "types": [],
            "ark": None,
            "url": None,
        },
    ]


def test_search_gallica_rejects_sru_diagnostics(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    xml = """<?xml version="1.0" encoding="UTF-8"?>
    <response>
      <diagnostic>
        <message>Requête invalide</message>
      </diagnostic>
    </response>
    """
    monkeypatch.setattr(
        service.httpx,
        "get",
        lambda *args, **kwargs: FakeResponse(text=xml),
    )

    with pytest.raises(RuntimeError, match="Requête invalide"):
        service.search_gallica("test")


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (None, ""),
        ("", ""),
        ("<b>Massenet</b> &amp; Thomas", "Massenet & Thomas"),
        (" texte simple ", "texte simple"),
    ],
)
def test_plain_text(value: str | None, expected: str) -> None:
    assert service._plain_text(value) == expected


def test_search_imslp_maps_and_encodes_results(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}
    response = FakeResponse(
        json_payload={
            "query": {
                "search": [
                    {
                        "title": "Thaïs (Massenet, Jules)",
                        "snippet": "<span>French opera</span> &amp; score",
                    },
                    {
                        "title": "",
                        "snippet": None,
                    },
                ]
            }
        }
    )

    def fake_get(url: str, **kwargs: Any) -> FakeResponse:
        captured["url"] = url
        captured.update(kwargs)
        return response

    monkeypatch.setattr(service.httpx, "get", fake_get)

    result = service.search_imslp("Thaïs", max_results=80)

    assert response.raise_for_status_called is True
    assert captured["url"] == service.IMSLP_API_URL
    assert captured["params"]["srlimit"] == 50
    assert result == [
        {
            "title": "Thaïs (Massenet, Jules)",
            "description": "French opera & score",
            "url": "https://imslp.org/wiki/Tha%C3%AFs_(Massenet,_Jules)",
        },
        {
            "title": "Page IMSLP",
            "description": "",
            "url": "https://imslp.org/wiki/Page_IMSLP",
        },
    ]


def test_search_imslp_handles_missing_query_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        service.httpx,
        "get",
        lambda *args, **kwargs: FakeResponse(json_payload={}),
    )

    assert service.search_imslp("inconnu", max_results=0) == []


def test_google_maps_urls_encode_locations() -> None:
    location = "Bibliothèque nationale de France, Paris"

    assert service.build_google_maps_search_url(location) == (
        "https://www.google.com/maps/search/"
        "?api=1&query=Biblioth%C3%A8que+nationale+de+France%2C+Paris"
    )
    assert service.build_google_maps_directions_url(location) == (
        "https://www.google.com/maps/dir/"
        "?api=1&destination=Biblioth%C3%A8que+nationale+de+France%2C+Paris"
    )
