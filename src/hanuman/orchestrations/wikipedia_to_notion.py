from __future__ import annotations

import os
from typing import Any, Dict, Iterable, List, Optional

from hanuman.services.core.notion_service import NotionPageRef, NotionService
from hanuman.services.core.wikipedia_service import (
    WikipediaInfoboxItem,
    WikipediaPage,
    WikipediaService,
)

MAX_RICH_TEXT = 2000


def _chunk_text(text: str) -> Iterable[str]:
    cleaned = text.replace("\r\n", "\n").strip()
    if not cleaned:
        return []
    return (
        cleaned[i : i + MAX_RICH_TEXT] for i in range(0, len(cleaned), MAX_RICH_TEXT)
    )


def _rich_text(text: str, *, link: str | None = None) -> List[Dict[str, Any]]:
    rich: List[Dict[str, Any]] = []
    for index, chunk in enumerate(_chunk_text(text)):
        payload: Dict[str, Any] = {"content": chunk}
        if link and index == 0:
            payload["link"] = {"url": link}
        rich.append({"type": "text", "text": payload})
    return rich


def _paragraph(text: str, *, link: str | None = None) -> Dict[str, Any]:
    return {
        "object": "block",
        "type": "paragraph",
        "paragraph": {"rich_text": _rich_text(text, link=link)},
    }


def _heading(text: str, level: int = 2) -> Dict[str, Any]:
    level = min(max(level, 1), 3)
    key = f"heading_{level}"
    return {"object": "block", "type": key, key: {"rich_text": _rich_text(text)}}


def _bulleted(text: str) -> Dict[str, Any]:
    return {
        "object": "block",
        "type": "bulleted_list_item",
        "bulleted_list_item": {"rich_text": _rich_text(text)},
    }


def _numbered(text: str) -> Dict[str, Any]:
    return {
        "object": "block",
        "type": "numbered_list_item",
        "numbered_list_item": {"rich_text": _rich_text(text)},
    }


def _table_cell(text: str) -> List[Dict[str, Any]]:
    rich = _rich_text(text)
    if not rich:
        return [{"type": "text", "text": {"content": ""}}]
    return rich


def _table_row(cells: Iterable[str]) -> Dict[str, Any]:
    return {
        "object": "block",
        "type": "table_row",
        "table_row": {"cells": [_table_cell(cell) for cell in cells]},
    }


def _infobox_table(items: List[WikipediaInfoboxItem]) -> Dict[str, Any]:
    rows = [_table_row(["Attribut", "Valeur"])]
    for item in items:
        rows.append(_table_row([item.label, item.value]))

    return {
        "object": "block",
        "type": "table",
        "table": {
            "table_width": 2,
            "has_column_header": True,
            "has_row_header": False,
            "children": rows,
        },
    }


def _image_block(url: str) -> Dict[str, Any]:
    return {
        "object": "block",
        "type": "image",
        "image": {"type": "external", "external": {"url": url}},
    }


def build_wikipedia_blocks(page: WikipediaPage) -> List[Dict[str, Any]]:
    blocks: List[Dict[str, Any]] = []

    if page.summary:
        blocks.append(_heading("Résumé", level=2))
        blocks.append(_paragraph(page.summary))

    if page.url:
        blocks.append(_paragraph("Lire sur Wikipedia", link=page.url))

    if page.infobox:
        blocks.append(_heading("Infobox", level=2))
        blocks.append(_infobox_table(page.infobox))

    if page.sections:
        blocks.append(_heading("Sections", level=2))
        for section in page.sections:
            blocks.append(_bulleted(section.title))

        for section in page.sections:
            blocks.append(_heading(section.title, level=3))
            blocks.append(_paragraph(section.content))

    if page.images:
        blocks.append(_heading("Images", level=2))
        for url in page.images:
            blocks.append(_image_block(url))

    if page.sources:
        blocks.append(_heading("Sources", level=2))
        for source in page.sources:
            blocks.append(_numbered(source))

    return blocks


def publish_wikipedia_page_to_notion(
    title_or_url: str,
    *,
    parent_page_id: Optional[str] = None,
    wikipedia_service: Optional[WikipediaService] = None,
    notion_service: Optional[NotionService] = None,
) -> NotionPageRef:
    wiki = wikipedia_service or WikipediaService()
    notion = notion_service or NotionService()

    if parent_page_id is None:
        parent_page_id = (
            os.getenv("NOTION_WIKIPEDIA_PARENT_ID")
            or os.getenv("NOTION_PARENT_PAGE_ID")  # fallback global si tu veux
        )

    page = wiki.fetch_page(title_or_url)
    blocks = build_wikipedia_blocks(page)

    return notion.create_page_under_parent(
        title=page.title,
        blocks=blocks,
        parent_page_id=parent_page_id,
    )


def main() -> None:
    """
    Petit CLI interactif :
    - demande un titre/URL Wikipédia dans le terminal
    - publie la page dans Notion sous la page "Wikipedia" par défaut
    """
    # 1) Parent Notion : priorité à la variable d'env, sinon ta page "Wikipedia"
    parent_default = os.getenv(
        "NOTION_WIKIPEDIA_PARENT_ID",
        "2abe48e8-8d80-800c-9772-dfcaa5b35d5f",
    )

    print("=== Wikipedia → Notion ===")
    print("Press ENTER with empty input to quit.\n")

    # 2) On permet de changer de parent une fois au début
    parent_id = (
        input(f"Parent Notion page id [default: {parent_default}]: ").strip()
        or parent_default
    )

    if not parent_id:
        print("No parent id provided, aborting.")
        return

    while True:
        query = input("Titre ou URL Wikipédia (ENTER pour quitter) : ").strip()
        if not query:
            print("Bye 👋")
            break

        try:
            ref = publish_wikipedia_page_to_notion(
                query,
                parent_page_id=parent_id,
            )
        except Exception as exc:  # noqa: BLE001
            print(f"[ERROR] {exc}")
        else:
            print(f"[OK] Notion page created: {ref.url} (id={ref.page_id})\n")


if __name__ == "__main__":
    main()
