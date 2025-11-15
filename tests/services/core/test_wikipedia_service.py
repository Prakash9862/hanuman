from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

import pytest

from hanuman.services.core.wikipedia_service import (
    WIKIPEDIA_BASE_URL,
    WikipediaInfoboxItem,
    WikipediaPage,
    WikipediaSection,
    WikipediaService,
    _extract_title,
    _strip_html,
)


def test_strip_html_removes_tags_and_normalises_spaces() -> None:
    html_fragment = "<p>Bonjour&nbsp;le monde<br/>Nouvelle ligne</p><div><strong>Suite</strong></div>"
    assert _strip_html(html_fragment) == "Bonjour le monde Nouvelle ligne Suite"
    assert _strip_html("") == ""


@pytest.mark.parametrize(
    "value, expected",
    [
        ("OpenAI", "OpenAI"),
        ("OpenAI Research", "OpenAI_Research"),
        ("https://fr.wikipedia.org/wiki/OpenAI#Historique", "OpenAI"),
    ],
)
def test_extract_title_accepts_plain_titles_and_urls(value: str, expected: str) -> None:
    assert _extract_title(value) == expected


def test_extract_title_raises_on_empty_input() -> None:
    with pytest.raises(ValueError):
        _extract_title("   ")


@dataclass
class _DummyResponse:
    status_code: int
    json_data: Any
    text: str = ""

    def json(self) -> Any:
        return self.json_data


class _DummyClient:
    def __init__(self, responses: Dict[str, _DummyResponse]) -> None:
        self._responses = responses
        self.requested_urls: list[str] = []

    def get(
        self, url: str, *, headers: Dict[str, str], timeout: float
    ) -> _DummyResponse:  # type: ignore[override]
        self.requested_urls.append(url)
        if url not in self._responses:
            raise AssertionError(f"URL inattendue appelée: {url}")
        return self._responses[url]


def test_fetch_page_parses_sections_infobox_sources() -> None:
    summary_url = f"{WIKIPEDIA_BASE_URL}/page/summary/OpenAI"
    sections_url = f"{WIKIPEDIA_BASE_URL}/page/mobile-sections/OpenAI"

    responses = {
        summary_url: _DummyResponse(
            200,
            {
                "extract": "OpenAI est une organisation de recherche.",
                "title": "OpenAI",
                "content_urls": {
                    "desktop": {"page": "https://fr.wikipedia.org/wiki/OpenAI"}
                },
                "originalimage": {"source": "https://upload.wikimedia.org/image.png"},
            },
        ),
        sections_url: _DummyResponse(
            200,
            {
                "lead": {
                    "sections": [
                        {
                            "line": "Historique",
                            "text": "<p>OpenAI est fondée en 2015.</p>",
                        }
                    ],
                    "infobox": [
                        {"label": "<b>Création</b>", "value": "<i>2015</i>"},
                    ],
                },
                "remaining": {
                    "sections": [
                        {
                            "line": "Références",
                            "anchor": "References",
                            "text": "<li>Ref&nbsp;1</li><li><a href='#'>Ref 2</a></li>",
                        }
                    ]
                },
            },
        ),
    }

    dummy_client = _DummyClient(responses)
    service = WikipediaService(client=dummy_client)

    page = service.fetch_page("https://fr.wikipedia.org/wiki/OpenAI#Historique")

    assert isinstance(page, WikipediaPage)
    assert page.title == "OpenAI"
    assert page.summary == "OpenAI est une organisation de recherche."
    assert page.url == "https://fr.wikipedia.org/wiki/OpenAI"
    assert page.images == ["https://upload.wikimedia.org/image.png"]

    assert page.sections[0] == WikipediaSection(
        title="Historique", content="OpenAI est fondée en 2015."
    )
    assert any(section.title == "Références" for section in page.sections)

    assert page.infobox == [WikipediaInfoboxItem(label="Création", value="2015")]
    assert page.sources == ["Ref 1", "Ref 2"]

    assert dummy_client.requested_urls == [summary_url, sections_url]


def test_fetch_page_handles_decommissioned_mobile_sections(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    summary_payload = {
        "extract": "Synthèse",
        "displaytitle": "OpenAI (organisation)",
        "content_urls": {"desktop": {"page": "https://fr.wikipedia.org/wiki/OpenAI"}},
    }

    service = WikipediaService()

    def fake_get(path: str) -> Dict[str, Any]:
        if path.startswith("page/summary"):
            return summary_payload
        raise RuntimeError("Mobile Content Service is decommissioned")

    monkeypatch.setattr(service, "_get", fake_get)

    page = service.fetch_page("OpenAI")

    assert page.title == "OpenAI (organisation)"
    assert page.sections == []
    assert page.infobox == []
    assert page.sources == []


def test_wikipedia_get_raises_on_http_errors() -> None:
    url = f"{WIKIPEDIA_BASE_URL}/page/summary/Inconnue"
    service = WikipediaService(
        client=_DummyClient({url: _DummyResponse(404, {"error": "not found"})})
    )

    with pytest.raises(ValueError, match="introuvable"):
        service._get("page/summary/Inconnue")

    service_error = WikipediaService(
        client=_DummyClient(
            {url: _DummyResponse(500, {"error": "server"}, text="server")}
        )
    )

    with pytest.raises(RuntimeError, match="500"):
        service_error._get("page/summary/Inconnue")

    invalid_json_service = WikipediaService(
        client=_DummyClient({url: _DummyResponse(200, ["unexpected"])})
    )

    with pytest.raises(RuntimeError, match="inattendue"):
        invalid_json_service._get("page/summary/Inconnue")
