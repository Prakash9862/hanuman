from __future__ import annotations

from typing import List

import pytest

from hanuman.api.routers import orchestrations as orchestrations_router
from hanuman.orchestrations.wikipedia_to_notion import (
    build_wikipedia_blocks,
    publish_wikipedia_page_to_notion,
)
from hanuman.services.core.notion_service import NotionPageRef, NotionService
from hanuman.services.core.wikipedia_service import (
    WikipediaInfoboxItem,
    WikipediaPage,
    WikipediaSection,
    WikipediaService,
)


class DummyWikipediaService(WikipediaService):
    def __init__(self, page: WikipediaPage) -> None:
        self._page = page

    def fetch_page(self, title_or_url: str) -> WikipediaPage:  # type: ignore[override]
        return self._page


class DummyNotionService(NotionService):
    def __init__(self) -> None:  # pragma: no cover - pas d'appel réel
        # Ne pas appeler le constructeur parent qui vérifie les tokens
        pass

    def create_page_under_parent(  # type: ignore[override]
        self,
        title: str,
        blocks: List[dict],
        parent_page_id: str | None = None,
    ) -> NotionPageRef:
        self.last_call = {
            "title": title,
            "blocks": blocks,
            "parent_page_id": parent_page_id,
        }
        return NotionPageRef(
            page_id="notion-page-id", url="https://notion.so/notion-page-id"
        )


def _sample_page() -> WikipediaPage:
    return WikipediaPage(
        title="OpenAI",
        summary="Laboratoire de recherche en intelligence artificielle.",
        url="https://fr.wikipedia.org/wiki/OpenAI",
        sections=[
            WikipediaSection(
                title="Historique", content="Fondé en 2015 à San Francisco."
            ),
            WikipediaSection(title="Produits", content="ChatGPT est lancé en 2022."),
        ],
        infobox=[
            WikipediaInfoboxItem(label="Fondation", value="2015"),
            WikipediaInfoboxItem(label="Siège", value="San Francisco"),
        ],
        sources=[
            "Sam Altman, Interview 2024",
            "Article scientifique sur GPT-4",
        ],
        images=["https://upload.wikimedia.org/example.png"],
    )


def test_build_wikipedia_blocks_structure() -> None:
    page = _sample_page()
    blocks = build_wikipedia_blocks(page)

    # Vérifie la présence des sections principales
    headings = [
        block.get("heading_2", {})
        .get("rich_text", [{}])[0]
        .get("text", {})
        .get("content")
        for block in blocks
        if block.get("type") == "heading_2"
    ]

    assert "Résumé" in headings
    assert "Infobox" in headings
    assert "Sections" in headings
    assert "Images" in headings
    assert "Sources" in headings

    # Vérifie que l'infobox est transformée en table avec les entrées attendues
    tables = [block for block in blocks if block.get("type") == "table"]
    assert tables, "Une table Notion doit être créée pour l'infobox"
    table_children = tables[0]["table"]["children"]
    first_data_row = table_children[1]["table_row"]["cells"]
    assert first_data_row[0][0]["text"]["content"] == "Fondation"
    assert first_data_row[1][0]["text"]["content"] == "2015"

    # Les images doivent être converties en blocs image
    image_blocks = [block for block in blocks if block.get("type") == "image"]
    assert image_blocks
    assert image_blocks[0]["image"]["external"]["url"].startswith("https://upload")


def test_publish_wikipedia_page_to_notion_calls_notion(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    page = _sample_page()
    wiki = DummyWikipediaService(page)
    notion = DummyNotionService()

    # Empêche la validation du token en NotionService en patchant l'init
    monkeypatch.setattr(NotionService, "__init__", lambda self: None)

    ref = publish_wikipedia_page_to_notion(
        "OpenAI",
        parent_page_id="parent-123",
        wikipedia_service=wiki,
        notion_service=notion,
    )

    assert ref.page_id == "notion-page-id"
    assert notion.last_call["title"] == "OpenAI"
    assert notion.last_call["parent_page_id"] == "parent-123"
    blocks = notion.last_call["blocks"]
    assert any(block.get("type") == "table" for block in blocks)
    assert any(block.get("type") == "image" for block in blocks)


def test_wikipedia_endpoint(monkeypatch: pytest.MonkeyPatch, client) -> None:
    called = {}

    def fake_publish(query: str, parent_page_id: str | None = None):
        called["query"] = query
        called["parent"] = parent_page_id
        return NotionPageRef(page_id="123", url="https://notion.so/123")

    monkeypatch.setattr(
        orchestrations_router, "publish_wikipedia_page_to_notion", fake_publish
    )

    response = client.post(
        "/orchestrations/wikipedia-to-notion",
        json={"query": "OpenAI", "parent_id": "parent-page"},
    )

    data = response.json()
    assert response.status_code == 200
    assert data["ok"] is True
    assert data["notion"]["id"] == "123"
    assert called == {"query": "OpenAI", "parent": "parent-page"}
