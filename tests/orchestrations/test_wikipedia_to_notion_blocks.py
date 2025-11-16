from __future__ import annotations

from types import SimpleNamespace
from typing import Any, Dict, List

from hanuman.orchestrations.wikipedia_to_notion import (
    build_wikipedia_blocks,
    publish_wikipedia_page_to_notion,
)
from hanuman.services.core.notion_service import NotionPageRef, NotionService
from hanuman.services.core.wikipedia_service import WikipediaService


def _types(blocks: List[Dict[str, Any]]) -> List[str]:
    return [b["type"] for b in blocks]


def test_build_wikipedia_blocks_full_page() -> None:
    # On utilise SimpleNamespace pour simuler les objets attendus
    sections = [
        SimpleNamespace(title="Origine", content="Texte sur l'origine."),
        SimpleNamespace(title="Symbolisme", content="Texte sur le symbolisme."),
    ]
    infobox = [
        SimpleNamespace(label="Pays", value="Inde"),
        SimpleNamespace(label="Religion", value="Bouddhisme"),
    ]

    page = SimpleNamespace(
        title="Dharmachakra",
        summary="Symbole de la roue de la Loi dans le bouddhisme.",
        url="https://fr.wikipedia.org/wiki/Dharmachakra",
        infobox=infobox,
        sections=sections,
        images=["https://upload.wikimedia.org/fake_dharmachakra.png"],
        sources=["Article Wikipédia 'Dharmachakra'"],
    )

    blocks = build_wikipedia_blocks(page)  # type: ignore[arg-type]

    types = _types(blocks)
    assert "heading_2" in types  # Résumé / Sections / etc.
    assert "table" in types  # infobox
    assert "image" in types  # images
    assert "numbered_list_item" in types  # sources

    # Vérifie qu'on a bien listé les sections en H3 avec leur contenu
    section_titles = {
        b["heading_3"]["rich_text"][0]["text"]["content"]
        for b in blocks
        if b["type"] == "heading_3"
    }
    assert {"Origine", "Symbolisme"} <= section_titles


class DummyWiki(WikipediaService):
    def __init__(self, page: Any) -> None:  # type: ignore[override]
        # On ne veut pas appeler le vrai __init__ (pas besoin), donc pas de super()
        self._page = page

    def fetch_page(self, title_or_url: str) -> Any:  # type: ignore[override]
        self.last_query = title_or_url
        return self._page


class DummyNotion(NotionService):
    def __init__(self) -> None:  # type: ignore[override]
        # Token factice pour satisfaire le constructeur
        super().__init__(
            token="dummy", api_base_url="http://dummy", notion_version="2025-09-03"
        )
        self.calls: List[Dict[str, Any]] = []

    def create_page_under_parent(  # type: ignore[override]
        self,
        title: str,
        blocks: List[Dict[str, Any]],
        parent_page_id: str | None = None,
    ) -> NotionPageRef:
        self.calls.append(
            {
                "title": title,
                "parent_page_id": parent_page_id,
                "blocks_count": len(blocks),
            }
        )
        return NotionPageRef(page_id="test-id", url="https://notion.so/test")


def test_publish_wikipedia_page_to_notion_uses_services() -> None:
    page = SimpleNamespace(
        title="Dharmachakra",
        summary="Symbole bouddhique.",
        url="https://fr.wikipedia.org/wiki/Dharmachakra",
        infobox=[],
        sections=[],
        images=[],
        sources=[],
    )

    wiki = DummyWiki(page=page)
    notion = DummyNotion()

    ref = publish_wikipedia_page_to_notion(
        "Dharmachakra",
        parent_page_id="parent-123",
        wikipedia_service=wiki,
        notion_service=notion,
    )

    # On a bien une NotionPageRef
    assert isinstance(ref, NotionPageRef)
    assert ref.page_id == "test-id"

    # Le service Notion a été appelé avec le bon titre et le bon parent
    assert len(notion.calls) == 1
    call = notion.calls[0]
    assert call["title"] == "Dharmachakra"
    assert call["parent_page_id"] == "parent-123"
    assert call["blocks_count"] >= 1
