from __future__ import annotations

import os
from typing import Any, Dict, Iterable, List, Optional, Sequence

from hanuman.services.core.notion_service import NotionPageRef, NotionService
from hanuman.services.core.wikipedia_service import (
    WikipediaInfoboxItem,
    WikipediaPage,
    WikipediaService,
)

MAX_RICH_TEXT = 2000


# =====================================================================
# Helpers Notion
# =====================================================================


def _rich_text(text: str) -> List[Dict[str, Any]]:
    text = text.strip()
    if not text:
        return []
    return [
        {
            "type": "text",
            "text": {
                "content": text,
            },
        }
    ]


def _paragraph(text: str) -> Dict[str, Any]:
    return {
        "object": "block",
        "type": "paragraph",
        "paragraph": {
            "rich_text": _rich_text(text),
        },
    }


def _heading(text: str, level: int = 2) -> Dict[str, Any]:
    level = max(1, min(level, 3))
    key = f"heading_{level}"
    return {
        "object": "block",
        "type": key,
        key: {
            "rich_text": _rich_text(text),
        },
    }


def _bulleted(text: str) -> Dict[str, Any]:
    return {
        "object": "block",
        "type": "bulleted_list_item",
        "bulleted_list_item": {
            "rich_text": _rich_text(text),
        },
    }


def _numbered(text: str) -> Dict[str, Any]:
    return {
        "object": "block",
        "type": "numbered_list_item",
        "numbered_list_item": {
            "rich_text": _rich_text(text),
        },
    }


def _image_block(url: str) -> Dict[str, Any]:
    return {
        "object": "block",
        "type": "image",
        "image": {
            "type": "external",
            "external": {"url": url},
        },
    }


def _chunk_text(text: str) -> Iterable[str]:
    """Coupe un long texte en segments compatibles Notion."""
    text = (text or "").strip()
    if not text:
        return

    start = 0
    length = len(text)
    while start < length:
        end = min(start + MAX_RICH_TEXT, length)
        chunk = text[start:end].strip()
        if chunk:
            yield chunk
        start = end


# =====================================================================
# Helpers Wikipedia (robustes aux variations de dataclasses)
# =====================================================================


def _get_attr(obj: Any, names: Sequence[str], default: Any = "") -> Any:
    for name in names:
        if hasattr(obj, name):
            value = getattr(obj, name)
            if value is not None:
                return value
    return default


def _section_title(section: Any) -> str:
    return str(_get_attr(section, ("title", "heading", "name"), "")).strip()


def _section_level(section: Any) -> int:
    value = _get_attr(section, ("level", "depth", "rank"), 1)
    try:
        level = int(value)
    except (TypeError, ValueError):
        return 1
    return max(1, level)


def _section_text(section: Any) -> str:
    # On essaie plusieurs conventions possibles
    value = _get_attr(section, ("content", "text", "body"), "")
    if value:
        return str(value)

    # Parfois le contenu est une liste de lignes
    lines = _get_attr(section, ("lines",), None)
    if isinstance(lines, (list, tuple)):
        return "\n".join(str(line) for line in lines)

    return ""


def _section_children(section: Any) -> List[Any]:
    children = _get_attr(section, ("children", "subsections", "sections"), [])
    if isinstance(children, (list, tuple)):
        return list(children)
    return []


def _flatten_sections(sections: Sequence[Any]) -> List[Any]:
    """Aplati l'arbre de sections en liste (pré-ordre)."""

    flat: List[Any] = []

    def _walk(items: Sequence[Any]) -> None:
        for sec in items:
            flat.append(sec)
            childs = _section_children(sec)
            if childs:
                _walk(childs)

    _walk(list(sections))
    return flat


def _format_infobox_item(item: WikipediaInfoboxItem) -> Optional[str]:
    raw_label = _get_attr(item, ("label", "name", "key"), "")
    raw_value = _get_attr(item, ("value",), "")

    label = str(raw_label).strip()
    value = str(raw_value).strip()

    if not (label or value):
        return None
    if label and value:
        return f"{label} : {value}"
    return label or value


def _infobox_table(items: Sequence[WikipediaInfoboxItem]) -> Optional[Dict[str, Any]]:
    """Construit une table Notion à 2 colonnes pour l'infobox."""

    rows: List[Dict[str, Any]] = []

    # Ligne d'en-tête
    header_cells = [
        _rich_text("Propriété"),
        _rich_text("Valeur"),
    ]
    rows.append(
        {
            "object": "block",
            "type": "table_row",
            "table_row": {
                "cells": header_cells,
            },
        }
    )

    # Lignes de données
    for item in items:
        label = _get_attr(item, ("label", "name", "key"), "").strip()
        value = _get_attr(item, ("value",), "").strip()
        if not (label or value):
            continue

        rows.append(
            {
                "object": "block",
                "type": "table_row",
                "table_row": {
                    "cells": [
                        _rich_text(label),
                        _rich_text(value),
                    ],
                },
            }
        )

    if len(rows) <= 1:
        # Pas de vraies données
        return None

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


# =====================================================================
# Construction des blocks Notion à partir d'une page Wikipedia
# =====================================================================


def build_wikipedia_blocks(page: WikipediaPage) -> List[Dict[str, Any]]:
    """
    Style C – académique :
    - Résumé analytique
    - Infobox
    - Plan détaillé (table des matières)
    - Sections détaillées (chapitres)
    - Images
    - Sources
    """
    blocks: List[Dict[str, Any]] = []

    # 1) Résumé analytique
    summary = (getattr(page, "summary", "") or "").strip()
    if summary:
        blocks.append(_heading("Résumé analytique", level=1))
        for chunk in _chunk_text(summary):
            blocks.append(_paragraph(chunk))

    # 2) Infobox
    infobox_items = getattr(page, "infobox", None) or []
    if infobox_items:
        blocks.append(_heading("Infobox", level=2))

        # Liste à puces (déjà utilisée par d'autres tests / usages)
        for item in infobox_items:
            line = _format_infobox_item(item)
            if line:
                blocks.append(_bulleted(line))

        # Table Notion pour l'infobox (attendue par les tests structurels)
        table_block = _infobox_table(infobox_items)
        if table_block is not None:
            blocks.append(table_block)

    # 3) Plan détaillé
    sections = getattr(page, "sections", None) or []
    flat_sections = _flatten_sections(sections)

    if flat_sections:
        blocks.append(_heading("Plan détaillé", level=2))
        for index, sec in enumerate(flat_sections, start=1):
            title = _section_title(sec)
            if not title:
                continue
            level = _section_level(sec)
            # On encode le niveau dans le texte pour un pseudo-nesting
            prefix = f"{index}." if level <= 1 else f"{index}.{level}"
            blocks.append(_numbered(f"{prefix} {title}"))

        # 4) Sections détaillées
    if flat_sections:
        blocks.append(_heading("Sections détaillées", level=2))

    for sec in flat_sections:
        title = _section_title(sec)
        text = _section_text(sec)

        if title:
            # Dans les sections détaillées, on force un niveau 3 pour distinguer du plan
            blocks.append(_heading(title, level=3))

        if text:
            for chunk in _chunk_text(text):
                blocks.append(_paragraph(chunk))

    # 5) Images
    images = getattr(page, "images", None) or []
    clean_images = [url for url in images if isinstance(url, str) and url.strip()]

    if clean_images:
        blocks.append(_heading("Images", level=2))
        for url in clean_images:
            blocks.append(_image_block(url))

    # 6) Sources
    sources = getattr(page, "sources", None) or []
    clean_sources = [s for s in sources if isinstance(s, str) and s.strip()]

    if clean_sources:
        blocks.append(_heading("Sources", level=2))
        for src in clean_sources:
            blocks.append(_numbered(src))

    return blocks


# =====================================================================
# Publication dans Notion
# =====================================================================


def publish_wikipedia_page_to_notion(
    title_or_url: str,
    *,
    parent_page_id: Optional[str] = None,
    wikipedia_service: Optional[WikipediaService] = None,
    notion_service: Optional[NotionService] = None,
) -> NotionPageRef:
    if not title_or_url.strip():
        raise ValueError("title_or_url ne peut pas être vide.")

    wiki = wikipedia_service or WikipediaService()
    page: WikipediaPage = wiki.fetch_page(title_or_url)

    blocks = build_wikipedia_blocks(page)

    notion = notion_service or NotionService()
    ref = notion.create_page_under_parent(
        title=getattr(page, "title", title_or_url),
        blocks=blocks,
        parent_page_id=parent_page_id,
    )
    return ref


# =====================================================================
# CLI simple (comme avant, mais refactoré)
# =====================================================================


def main() -> None:
    """Petite interface CLI pour lancer la synchro Wikipédia → Notion."""

    from hanuman.config.env import NOTION_PARENT_ID  # import local pour éviter cycles

    print("=== Wikipedia → Notion ===")
    print("Press ENTER with empty input to quit.\n")

    default_parent = os.environ.get("NOTION_WIKIPEDIA_PARENT_ID") or NOTION_PARENT_ID

    prompt_parent = (
        f"Parent Notion page id [default: {default_parent}]: "
        if default_parent
        else "Parent Notion page id (ENTER pour utiliser la config Notion par défaut): "
    )

    parent_id = input(prompt_parent).strip()
    if not parent_id:
        parent_id = default_parent or None  # type: ignore[assignment]

    while True:
        query = input("Titre ou URL Wikipédia (ENTER pour quitter) : ").strip()
        if not query:
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
