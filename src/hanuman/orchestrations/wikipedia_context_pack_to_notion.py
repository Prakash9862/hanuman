from __future__ import annotations

import argparse
import os
from typing import Any, Dict, List, Sequence, Tuple

from hanuman.orchestrations.wikipedia_to_notion import (
    _heading,
    _paragraph,
    build_wikipedia_blocks,
)
from hanuman.services.core.notion_service import NotionPageRef, NotionService
from hanuman.services.core.wikipedia_service import (
    WikipediaSearchResult,
    WikipediaService,
)


def _bulleted_links(parts: Sequence[Tuple[str, str | None]]) -> Dict[str, Any]:
    rich: List[Dict[str, Any]] = []
    for index, (text, url) in enumerate(parts):
        payload: Dict[str, Any] = {"content": text}
        if url:
            payload["link"] = {"url": url}
        rich.append({"type": "text", "text": payload})

        if index < len(parts) - 1:
            rich.append({"type": "text", "text": {"content": " • "}})

    return {
        "object": "block",
        "type": "bulleted_list_item",
        "bulleted_list_item": {"rich_text": rich},
    }


def publish_wikipedia_context_pack(
    topic: str,
    *,
    max_pages: int = 5,
    parent_page_id: str | None = None,
    wikipedia_service: WikipediaService | None = None,
    notion_service: NotionService | None = None,
) -> NotionPageRef:
    """Recherche plusieurs pages Wikipédia et les publie dans Notion."""

    wiki = wikipedia_service or WikipediaService()
    notion = notion_service or NotionService()

    parent = parent_page_id

    if not isinstance(parent, str) or not parent:
        raise ValueError("Aucun parent Notion fourni (NOTION_WIKIPEDIA_PARENT_ID).")

    try:
        search_results: List[WikipediaSearchResult] = wiki.search_pages(topic, limit=max_pages)
    except ValueError as exc:
        # Par exemple : "Article Wikipedia introuvable" venant du client Wikipedia
        raise ValueError(
            f"Aucun résultat Wikipedia pour '{topic}' "
            f"(vérifie l'orthographe ou essaie un autre mot-clé)."
        ) from exc

    if not search_results:
        raise ValueError(f"Aucun résultat Wikipedia pour '{topic}'.")

    overview_blocks = [
        _heading(f"Pack Wikipedia : {topic}", level=2),
        _paragraph(
            f"{len(search_results)} pages sélectionnées via la recherche Wikipedia pour '{topic}'."
        ),
        _heading("Pages importées", level=3),
    ]

    overview_ref = notion.create_page_under_parent(
        title=f"Wikipedia | {topic}",
        blocks=overview_blocks,
        parent_page_id=parent,
    )

    link_blocks: List[dict] = []

    for result in search_results:
        page = wiki.fetch_page(result.title)
        child_ref = notion.create_page_under_parent(
            title=page.title,
            blocks=build_wikipedia_blocks(page),
            parent_page_id=overview_ref.page_id,
        )

        description = result.description or page.summary[:200]
        link_blocks.append(
            _bulleted_links(
                [
                    (page.title, child_ref.url),
                    ("Wikipedia", result.url),
                ]
            )
        )
        if description:
            link_blocks.append(_paragraph(description))

    if link_blocks:
        notion.append_blocks(overview_ref.page_id, link_blocks)

    return overview_ref


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="hanuman.orchestrations.wikipedia_context_pack_to_notion",
        description="Importe plusieurs pages Wikipedia pertinentes dans Notion.",
    )
    parser.add_argument(
        "--topic",
        required=False,
        default=None,
        help="Sujet ou requête de recherche (sinon demandé en mode interactif).",
    )

    parser.add_argument(
        "--max-pages",
        type=int,
        default=5,
        help="Nombre maximum de pages à importer (défaut: 5).",
    )
    parser.add_argument(
        "--parent-page-id",
        help="Page Notion parent (sinon NOTION_WIKIPEDIA_PARENT_ID / NOTION_PARENT_PAGE_ID).",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    # --- Sujet ---
    topic = args.topic
    if topic is None:
        # Mode interactif (quand lancé depuis le terminal)
        if argv is None:
            topic = input("Sujet Wikipedia : ").strip()
            if not topic:
                print("Aucun sujet fourni, arrêt.")
                return
        else:
            # En mode non-interactif (tests ou appels internes), on exige le topic
            raise SystemExit("Argument --topic obligatoire en mode non interactif.")

    # --- Nombre de pages ---
    max_pages = args.max_pages
    if argv is None:
        raw = input(f"Nombre maximum de pages (ENTER pour {max_pages}) : ").strip()
        if raw:
            try:
                max_pages = int(raw)
            except ValueError:
                print("Valeur invalide, on garde la valeur par défaut.")

    # --- Parent Notion ---
    parent = (
        args.parent_page_id
        or os.getenv("NOTION_WIKIPEDIA_PARENT_ID")
        or os.getenv("NOTION_PARENT_PAGE_ID")
    )

    if not parent:
        raise SystemExit(
            "Impossible de trouver une page parent Notion. "
            "Définis NOTION_WIKIPEDIA_PARENT_ID ou NOTION_PARENT_PAGE_ID dans ton .env."
        )

    # --- Exécution ---
    try:
        ref = publish_wikipedia_context_pack(
            topic=topic,
            max_pages=max_pages,
            parent_page_id=parent,
        )
    except ValueError as exc:
        print(f"[ERREUR] {exc}")
        return

    print(f"[OK] Pack Wikipedia créé : {ref.url} (id={ref.page_id})")


if __name__ == "__main__":
    main()
