import os

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from hanuman.models.obsidian_notion import (
    ObsidianNotionItemsResponse,
    ObsidianNotionStats,
)
from hanuman.orchestrations.obsidian_notion_dashboard import build_items, build_stats
from hanuman.orchestrations.obsidian_to_notion import send_markdown_to_notion
from hanuman.orchestrations.wikipedia_to_notion import (
    publish_wikipedia_page_to_notion,
)

router = APIRouter(
    prefix="/orchestrations",
    tags=["orchestrations"],
)


class ObsidianToNotionIn(BaseModel):
    path: str
    parent_id: str | None = None
    parent_is_db: bool | None = None
    db_title_name: str | None = None


class WikipediaToNotionIn(BaseModel):
    query: str
    parent_id: str | None = None


@router.get(
    "/obsidian-notion/items",
    response_model=ObsidianNotionItemsResponse,
)
def obsidian_notion_items(
    query: str | None = Query(default=None, description="Recherche par titre, chemin ou tag"),
) -> ObsidianNotionItemsResponse:
    """Fusionne l'inventaire du vault et des pages Notion dédiées."""
    try:
        items = build_items(query)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return ObsidianNotionItemsResponse(items=items, total=len(items))


@router.get(
    "/obsidian-notion/stats",
    response_model=ObsidianNotionStats,
)
def obsidian_notion_stats() -> ObsidianNotionStats:
    """Retourne les statistiques d'état de l'orchestration."""
    try:
        return build_stats(build_items())
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/obsidian-to-notion")
def obsidian_to_notion(body: ObsidianToNotionIn):
    """
    Envoie un fichier Markdown d'Obsidian vers Notion.
    Le parent peut être une page ou une base de données.
    """
    parent = (
        body.parent_id
        or os.environ.get("NOTION_OBSIDIAN_PARENT_ID")
        or os.environ.get("NOTION_PARENT_PAGE_ID")
        or os.environ.get("NOTION_PARENT_ID")
    )

    if not parent:
        return {
            "ok": False,
            "error": "Parent Notion manquant (NOTION_OBSIDIAN_PARENT_ID/NOTION_PARENT_PAGE_ID/NOTION_PARENT_ID)",
        }

    try:
        out = send_markdown_to_notion(
            markdown_path=body.path,
            parent_id=parent,
            parent_is_db=body.parent_is_db,
            db_title_name=body.db_title_name or os.environ.get("NOTION_DB_TITLE_NAME", "Name"),
        )
        return {"ok": True, "notion": out}

    except Exception as exc:
        return {"ok": False, "error": str(exc)}


@router.post("/wikipedia-to-notion")
def wikipedia_to_notion(body: WikipediaToNotionIn):
    parent = (
        body.parent_id
        or os.environ.get("NOTION_WIKIPEDIA_PARENT_ID")
        or os.environ.get("NOTION_PARENT_PAGE_ID")
        or os.environ.get("NOTION_PARENT_ID")
    )

    if not parent:
        return {
            "ok": False,
            "error": "Parent Notion manquant (NOTION_WIKIPEDIA_PARENT_ID/NOTION_PARENT_PAGE_ID/NOTION_PARENT_ID)",
        }

    try:
        ref = publish_wikipedia_page_to_notion(
            body.query,
            parent_page_id=parent,
        )
        return {"ok": True, "notion": {"id": ref.page_id, "url": ref.url}}
    except Exception as exc:  # pragma: no cover - renvoyé comme erreur HTTP
        return {"ok": False, "error": str(exc)}


@router.get("/ping")
def orchestration_ping():
    """Test rapide que la route /orchestrations est bien active."""
    return {"status": "ok", "module": "orchestrations"}
