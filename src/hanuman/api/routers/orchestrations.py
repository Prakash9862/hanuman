import os

from fastapi import APIRouter
from pydantic import BaseModel

# Import du moteur d’orchestration
from hanuman.orchestrations.obsidian_to_notion import send_markdown_to_notion
from hanuman.orchestrations.wikipedia_to_notion import (
    publish_wikipedia_page_to_notion,
)

router = APIRouter(
    prefix="/orchestrations",
    tags=["orchestrations"],
)


# === Modèles d’entrée ===
class ObsidianToNotionIn(BaseModel):
    path: str
    parent_id: str | None = None
    parent_is_db: bool | None = None
    db_title_name: str | None = None


class WikipediaToNotionIn(BaseModel):
    query: str
    parent_id: str | None = None


# === Endpoint Obsidian → Notion ===
@router.post("/obsidian-to-notion")
def obsidian_to_notion(body: ObsidianToNotionIn):
    """
    Envoie un fichier Markdown d'Obsidian vers Notion.
    Le parent peut être une page ou une base de données.
    """
    parent = (
        body.parent_id
        or os.environ.get("NOTION_PARENT_PAGE_ID")
        or os.environ.get("NOTION_PARENT_ID")
    )

    if not parent:
        return {
            "ok": False,
            "error": "Parent Notion manquant (env NOTION_PARENT_PAGE_ID/NOTION_PARENT_ID ou body.parent_id)",
        }

    try:
        out = send_markdown_to_notion(
            path=body.path,
            parent_id=parent,
            parent_is_db=body.parent_is_db,
            db_title_name=body.db_title_name
            or os.environ.get("NOTION_DB_TITLE_NAME", "Name"),
        )
        return {"ok": True, "notion": out}

    except Exception as e:
        return {"ok": False, "error": str(e)}


# === Endpoint Wikipedia → Notion ===
@router.post("/wikipedia-to-notion")
def wikipedia_to_notion(body: WikipediaToNotionIn):
    try:
        ref = publish_wikipedia_page_to_notion(
            body.query,
            parent_page_id=body.parent_id,
        )
        return {"ok": True, "notion": {"id": ref.page_id, "url": ref.url}}
    except Exception as exc:  # pragma: no cover - renvoyé comme erreur HTTP
        return {"ok": False, "error": str(exc)}


# === Endpoint basique de ping (sanity check) ===
@router.get("/ping")
def orchestration_ping():
    """Test rapide que la route /orchestrations est bien active."""
    return {"status": "ok", "module": "orchestrations"}
