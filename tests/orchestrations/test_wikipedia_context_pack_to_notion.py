from __future__ import annotations

from typing import Iterable, List

import pytest

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
