import os

from fastapi import APIRouter
from pydantic import BaseModel

from hanuman.orchestrations.notion_to_obsidian import import_notion_page_to_obsidian
from hanuman.orchestrations.obsidian_to_notion import send_markdown_to_notion
from hanuman.orchestrations.wikipedia_to_notion import (
    publish_wikipedia_page_to_notion,
)
from hanuman.services.core.obsidian_service import ObsidianService

router = APIRouter(
    prefix="/orchestrations",
    tags=["orchestrations"],
)


class ObsidianToNotionIn(BaseModel):
    path: str
    parent_id: str | None = None
    parent_is_db: bool | None = None
    db_title_name: str | None = None


class NotionToObsidianIn(BaseModel):
    page_id: str
    destination_dir: str | None = None
    overwrite: bool = False


class WikipediaToNotionIn(BaseModel):
    query: str
    parent_id: str | None = None


@router.get("/obsidian-notion/notes")
def list_obsidian_notes():
    """Liste les notes proposées à l'orchestration Obsidian ↔ Notion."""
    try:
        return {"ok": True, "notes": ObsidianService().list_notes()}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


@router.post("/obsidian-notion/publish")
def obsidian_to_notion(body: ObsidianToNotionIn):
    """Publie une note du vault vers la page Notion parente configurée."""
    parent = (
        body.parent_id
        or os.environ.get("NOTION_OBSIDIAN_PARENT_ID")
        or os.environ.get("NOTION_PARENT_PAGE_ID")
        or os.environ.get("NOTION_PARENT_ID")
    )
    if not parent:
        return {
            "ok": False,
            "error": "Parent Notion manquant (NOTION_OBSIDIAN_PARENT_ID)",
        }

    try:
        note = ObsidianService().read_note(body.path)
        out = send_markdown_to_notion(
            markdown_path=note["absolute_path"],
            parent_id=parent,
            parent_is_db=body.parent_is_db,
            db_title_name=body.db_title_name or os.environ.get("NOTION_DB_TITLE_NAME", "Name"),
        )
        return {
            "ok": True,
            "status": "published",
            "note_path": note["path"],
            "notion": out,
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


@router.post("/obsidian-notion/import")
def notion_to_obsidian(body: NotionToObsidianIn):
    """Importe une page Notion dans le dossier Obsidian configuré."""
    try:
        result = import_notion_page_to_obsidian(
            body.page_id,
            destination_dir=body.destination_dir,
            overwrite=body.overwrite,
        )
        return {"ok": True, **result}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


@router.post("/obsidian-to-notion")
def legacy_obsidian_to_notion(body: ObsidianToNotionIn):
    """Compatibilité temporaire avec l'ancienne route."""
    return obsidian_to_notion(body)


@router.post("/wikipedia-to-notion")
def wikipedia_to_notion(body: WikipediaToNotionIn):
    try:
        ref = publish_wikipedia_page_to_notion(
            body.query,
            parent_page_id=body.parent_id,
        )
        return {"ok": True, "notion": {"id": ref.page_id, "url": ref.url}}
    except Exception as exc:  # pragma: no cover
        return {"ok": False, "error": str(exc)}


@router.get("/ping")
def orchestration_ping():
    return {"status": "ok", "module": "orchestrations"}
