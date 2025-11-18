from __future__ import annotations

from typing import Iterable, List

import pytest

import hanuman.orchestrations.wikipedia_context_pack_to_notion as wc2n
from hanuman.orchestrations.wikipedia_context_pack_to_notion import (
    publish_wikipedia_context_pack,
)
from hanuman.orchestrations.wikipedia_to_notion import build_wikipedia_blocks
from hanuman.services.core.notion_service import NotionPageRef, NotionService
from hanuman.services.core.wikipedia_service import (
    WikipediaPage,
    WikipediaSearchResult,
    WikipediaSection,
    WikipediaService,
)


class DummyWikipediaService(WikipediaService):
    def __init__(
        self, results: List[WikipediaSearchResult], page: WikipediaPage
    ) -> None:  # pragma: no cover - init not used
        self._results = results
        self._page = page

    def search_pages(self, query: str, *, limit: int = 5):  # type: ignore[override]
        self.last_query = query
        self.last_limit = limit
        return self._results

    def fetch_page(self, title_or_url: str):  # type: ignore[override]
        self.last_fetch = title_or_url
        return self._page


class DummyNotionService(NotionService):
    def __init__(self) -> None:  # pragma: no cover - init not used
        self.created: List[dict] = []
        self.appended: list[tuple[str, list[dict]]] = []

    def create_page_under_parent(
        self, title: str, blocks: List[dict], parent_page_id: str | None = None
    ):  # type: ignore[override]
        ref = NotionPageRef(
            page_id=f"page-{len(self.created)}",
            url=f"https://notion.so/{len(self.created)}",
        )
        self.created.append(
            {"title": title, "blocks": blocks, "parent": parent_page_id}
        )
        return ref

    def append_blocks(self, page_id: str, blocks: List[dict]):  # type: ignore[override]
        self.appended.append((page_id, blocks))


@pytest.fixture(autouse=True)
def patch_notion_init(monkeypatch: pytest.MonkeyPatch) -> Iterable[None]:
    monkeypatch.setattr(NotionService, "__init__", lambda self: None)
    yield


def _sample_page() -> WikipediaPage:
    return WikipediaPage(
        title="OpenAI",
        summary="Organisation de recherche en IA.",
        url="https://fr.wikipedia.org/wiki/OpenAI",
        sections=[WikipediaSection(title="Historique", content="Fondée en 2015")],
        infobox=[],
        sources=[],
        images=[],
    )


def test_publish_wikipedia_context_pack_creates_overview_and_children(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    results = [
        WikipediaSearchResult(
            title="OpenAI",
            description="Organisation",
            url="https://fr.wikipedia.org/wiki/OpenAI",
        ),
        WikipediaSearchResult(
            title="ChatGPT",
            description="Modèle de langage",
            url="https://fr.wikipedia.org/wiki/ChatGPT",
        ),
    ]
    page = _sample_page()
    wiki = DummyWikipediaService(results, page)
    notion = DummyNotionService()

    # S'assure que l'orchestration utilise bien la fonction de build existante
    monkeypatch.setattr(
        "hanuman.orchestrations.wikipedia_context_pack_to_notion.build_wikipedia_blocks",
        build_wikipedia_blocks,
    )

    ref = publish_wikipedia_context_pack(
        "IA",
        parent_page_id="parent-xyz",
        max_pages=2,
        wikipedia_service=wiki,
        notion_service=notion,
    )

    assert ref.page_id == "page-0"
    assert wiki.last_query == "IA"
    assert wiki.last_limit == 2

    overview = notion.created[0]
    assert overview["parent"] == "parent-xyz"
    assert (
        "Pack Wikipedia"
        in overview["blocks"][0]["heading_2"]["rich_text"][0]["text"]["content"]
    )

    child_parents = {child["parent"] for child in notion.created[1:]}
    assert child_parents == {"page-0"}
    assert len(notion.created) == 3  # overview + 2 enfants

    assert notion.appended
    page_id, appended_blocks = notion.appended[0]
    assert page_id == "page-0"
    assert any(block.get("type") == "bulleted_list_item" for block in appended_blocks)


def test_publish_wikipedia_context_pack_requires_parent() -> None:
    wiki = DummyWikipediaService(
        [WikipediaSearchResult(title="OpenAI", description="", url="url")],
        _sample_page(),
    )
    notion = DummyNotionService()

    with pytest.raises(ValueError, match="parent Notion"):
        publish_wikipedia_context_pack(
            "OpenAI", wikipedia_service=wiki, notion_service=notion
        )


def test_bulleted_links_builds_expected_structure() -> None:
    block = wc2n._bulleted_links(
        [
            ("One", "https://one"),
            ("Two", None),
        ]
    )

    assert block["type"] == "bulleted_list_item"
    rich = block["bulleted_list_item"]["rich_text"]

    contents = [span["text"]["content"] for span in rich if span["type"] == "text"]
    assert "One" in contents
    assert "Two" in contents
    # On veut bien le séparateur "•" entre les items
    assert any("•" in span["text"]["content"] for span in rich)


def test_publish_wikipedia_context_pack_no_results_raises() -> None:
    class EmptyWiki(DummyWikipediaService):
        def search_pages(self, query: str, *, limit: int = 5):  # type: ignore[override]
            return []

    wiki = EmptyWiki([], _sample_page())
    notion = DummyNotionService()

    with pytest.raises(ValueError, match="Aucun résultat Wikipedia"):
        publish_wikipedia_context_pack(
            "sujet-introuvable",
            parent_page_id="parent-xyz",
            wikipedia_service=wiki,
            notion_service=notion,
        )


def test_publish_wikipedia_context_pack_wraps_value_error_message() -> None:
    class FailingWiki(DummyWikipediaService):
        def search_pages(self, query: str, *, limit: int = 5):  # type: ignore[override]
            raise ValueError("boom")

    wiki = FailingWiki([], _sample_page())
    notion = DummyNotionService()

    with pytest.raises(ValueError, match="vérifie l'orthographe"):
        publish_wikipedia_context_pack(
            "OpenAI",
            parent_page_id="parent-xyz",
            wikipedia_service=wiki,
            notion_service=notion,
        )


def test_main_non_interactive_uses_arguments_and_env(monkeypatch, capsys) -> None:
    """
    Couvre la CLI main() en mode non-interactif, avec publish patché.
    """
    called: dict[str, object] = {}

    def fake_publish(
        topic: str,
        *,
        max_pages: int,
        parent_page_id: str | None = None,
        wikipedia_service=None,
        notion_service=None,
    ):
        called["topic"] = topic
        called["max_pages"] = max_pages
        called["parent_page_id"] = parent_page_id
        return NotionPageRef(page_id="page-123", url="https://notion.so/page-123")

    monkeypatch.setattr(
        wc2n,
        "publish_wikipedia_context_pack",
        fake_publish,
    )
    # Pas de parent passé en CLI → on utilise l'env
    monkeypatch.setenv("NOTION_WIKIPEDIA_PARENT_ID", "env-parent")

    wc2n.main(["--topic", "IA", "--max-pages", "3"])
    out = capsys.readouterr().out

    assert "Pack Wikipedia créé" in out
    assert called == {
        "topic": "IA",
        "max_pages": 3,
        "parent_page_id": "env-parent",
    }


def test_main_requires_parent_page(monkeypatch) -> None:
    """
    Couvre la SystemExit quand aucun parent n'est dispo.
    """
    monkeypatch.delenv("NOTION_WIKIPEDIA_PARENT_ID", raising=False)
    monkeypatch.delenv("NOTION_PARENT_PAGE_ID", raising=False)

    with pytest.raises(SystemExit):
        wc2n.main(["--topic", "IA"])


def test_main_interactive_empty_topic_aborts(monkeypatch, capsys) -> None:
    """
    Mode interactif (argv=None) + input vide → sortie propre sans exception.
    """
    monkeypatch.setenv("NOTION_WIKIPEDIA_PARENT_ID", "parent-xyz")

    # On force input() à renvoyer vide → cas "aucun sujet"
    monkeypatch.setattr(
        "builtins.input",
        lambda _prompt: "",
    )

    # On neutralise le -q de pytest dans sys.argv
    import sys

    monkeypatch.setattr(
        sys,
        "argv",
        ["hanuman.orchestrations.wikipedia_context_pack_to_notion"],
    )

    wc2n.main(None)
    out = capsys.readouterr().out

    assert "Aucun sujet fourni" in out
