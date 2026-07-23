from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

import pytest

from hanuman.services.core.wikipedia_service import (
    WIKIPEDIA_BASE_URL,
    WikipediaPage,
    WikipediaSection,
    WikipediaService,
    _build_long_summary,
    _extract_infobox_and_sources_from_html,
    _extract_title,
    _split_sections_from_html,
    _strip_html,
)


def test_strip_html_removes_tags_and_normalises_spaces() -> None:
    html_fragment = (
        "<p>Bonjour&nbsp;le monde<br/>Nouvelle ligne</p><div><strong>Suite</strong></div>"
    )
    text = _strip_html(html_fragment)

    # Nouveau design : _strip_html normalise mais conserve les retours à la ligne
    assert "Bonjour le monde" in text
    assert "Nouvelle ligne" in text
    assert "Suite" in text


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


def test_fetch_page_parses_sections_infobox_sources(monkeypatch):
    summary_url = f"{WIKIPEDIA_BASE_URL}/page/summary/OpenAI"

    responses = {
        summary_url: _DummyResponse(
            200,
            {
                "extract": "OpenAI est une organisation de recherche.",
                "title": "OpenAI",
                "content_urls": {"desktop": {"page": "https://fr.wikipedia.org/wiki/OpenAI"}},
                "originalimage": {"source": "https://upload.wikimedia.org/image.png"},
            },
        ),
    }

    dummy_client = _DummyClient(responses)
    service = WikipediaService(client=dummy_client)

    html_sample = """
    <html><body>
      <p>OpenAI est une organisation de recherche.</p>

      <table class="infobox">
        <tr><th>Création</th><td>2015</td></tr>
      </table>

      <h2>Historique</h2>
      <p>OpenAI est fondée en 2015.</p>

      <h2>Références</h2>
      <ol class="references">
        <li>Ref 1</li>
        <li>Ref 2</li>
      </ol>
    </body></html>
    """

    def fake_get_html(path, base_url, client=None, timeout=10.0):
        assert path == "page/html/OpenAI"
        return html_sample

    monkeypatch.setattr("hanuman.services.core.wikipedia_service._get_html", fake_get_html)

    page = service.fetch_page("OpenAI")

    assert isinstance(page, WikipediaPage)
    assert page.title == "OpenAI"
    assert page.summary.startswith("OpenAI est une organisation de recherche.")
    assert page.url == "https://fr.wikipedia.org/wiki/OpenAI"
    assert page.images == ["https://upload.wikimedia.org/image.png"]

    assert page.sections[0] == WikipediaSection(
        title="Historique",
        content="OpenAI est fondée en 2015.",
    )

    assert page.infobox[0].label == "Création"
    assert page.infobox[0].value == "2015"

    assert "Ref 1" in page.sources[0]


def test_fetch_page_handles_decommissioned_mobile_sections(monkeypatch):
    summary_payload = {
        "extract": "Synthèse",
        "displaytitle": "OpenAI (organisation)",
        "content_urls": {"desktop": {"page": "https://fr.wikipedia.org/wiki/OpenAI"}},
    }

    service = WikipediaService()

    def fake_get(path):
        assert path.startswith("page/summary")
        return summary_payload

    def fake_html(*args, **kwargs):
        raise RuntimeError("HTML service down")

    monkeypatch.setattr(service, "_get", fake_get)
    monkeypatch.setattr("hanuman.services.core.wikipedia_service._get_html", fake_html)

    page = service.fetch_page("OpenAI")

    assert page.title == "OpenAI (organisation)"
    assert page.summary == "Synthèse"
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
        client=_DummyClient({url: _DummyResponse(500, {"error": "server"}, text="server")})
    )

    with pytest.raises(RuntimeError, match="500"):
        service_error._get("page/summary/Inconnue")

    invalid_json_service = WikipediaService(
        client=_DummyClient({url: _DummyResponse(200, ["unexpected"])})
    )

    with pytest.raises(RuntimeError, match="inattendue"):
        invalid_json_service._get("page/summary/Inconnue")


def test_build_long_summary_truncates_long_intro() -> None:
    # Génère un HTML avec plein de paragraphes pour dépasser max_chars
    paragraphs = "".join(f"<p>Paragraphe {i} - Lorem ipsum dolor sit amet.</p>" for i in range(50))
    html_doc = (
        f"<html><body>{paragraphs}<h2>Section suivante</h2><p>Contenu ignoré</p></body></html>"
    )

    summary = _build_long_summary(html_doc, max_chars=200)

    # On doit avoir un résumé non vide, mais limité
    assert summary
    assert len(summary) <= 205  # 200 + éventuellement "…"
    # La section suivante ne doit pas apparaître
    assert "Section suivante" not in summary


def test_split_sections_from_html_without_headings_returns_empty() -> None:
    html_doc = "<html><body><p>Texte sans titres.</p><p>Autre texte.</p></body></html>"

    sections = _split_sections_from_html(html_doc)

    assert sections == []


def test_split_sections_from_html_parses_multiple_headings() -> None:
    html_doc = """
    <html><body>
      <h2>Histoire</h2>
      <p>Texte sur l'histoire.</p>
      <h3>Origines</h3>
      <p>Texte sur les origines.</p>
      <h2>Géographie</h2>
      <p>Texte sur la géographie.</p>
    </body></html>
    """

    sections = _split_sections_from_html(html_doc)

    titles = [s.title for s in sections]
    contents = [s.content for s in sections]

    assert titles == ["Histoire", "Origines", "Géographie"]
    assert any("histoire" in c.lower() for c in contents)
    assert any("origines" in c.lower() for c in contents)
    assert any("géographie" in c.lower() for c in contents)


def test_extract_infobox_and_sources_handles_html_without_any() -> None:
    html_doc = "<html><body><p>Pas d'infobox ni de références ici.</p></body></html>"

    infobox, sources = _extract_infobox_and_sources_from_html(html_doc)

    assert infobox == []
    assert sources == []


def test_extract_infobox_and_sources_parses_basic_table_and_references() -> None:
    html_doc = """
    <html><body>
      <table class="infobox">
        <tr><th>Fondation</th><td>2015</td></tr>
        <tr><th>Siège</th><td>San Francisco</td></tr>
      </table>
      <h2>Références</h2>
      <ol class="references">
        <li>Source 1</li>
        <li>Source 2</li>
      </ol>
    </body></html>
    """

    infobox, sources = _extract_infobox_and_sources_from_html(html_doc)

    assert len(infobox) == 2
    assert infobox[0].label == "Fondation"
    assert infobox[0].value == "2015"
    assert infobox[1].label == "Siège"
    assert "San Francisco" in infobox[1].value

    assert sources and "Source 1" in sources[0]
