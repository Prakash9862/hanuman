import os
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from hanuman.models.obsidian_notion import (
    ObsidianNotionItemsResponse,
    ObsidianNotionStats,
)
from hanuman.orchestrations.obsidian_notion_dashboard import build_items, build_stats
from hanuman.orchestrations.obsidian_to_notion_safe import send_markdown_to_notion_safe
from hanuman.orchestrations.wikipedia_to_notion import (
    publish_wikipedia_page_to_notion,
)

router = APIRouter(prefix="/orchestrations", tags=["orchestrations"])


class ObsidianToNotionIn(BaseModel):
    path: str
    parent_id: str | None = None
    parent_is_db: bool | None = None
    db_title_name: str | None = None


class WikipediaToNotionIn(BaseModel):
    query: str
    parent_id: str | None = None


def _resolve_obsidian_markdown_path(raw_path: str) -> Path:
    requested = Path(raw_path).expanduser()
    if requested.is_absolute():
        resolved = requested.resolve()
    else:
        vault_raw = os.environ.get("OBSIDIAN_VAULT_PATH") or os.environ.get("OBSIDIAN_VAULT_DIR")
        if not vault_raw:
            raise RuntimeError("OBSIDIAN_VAULT_PATH manquant dans l'environnement")
        vault = Path(vault_raw).expanduser().resolve()
        resolved = (vault / requested).resolve()
        try:
            resolved.relative_to(vault)
        except ValueError as exc:
            raise ValueError("Le fichier demandé se trouve hors du vault Obsidian.") from exc

    if not resolved.is_file():
        raise FileNotFoundError(f"Markdown introuvable: {resolved}")
    if resolved.suffix.lower() != ".md":
        raise ValueError("Seuls les fichiers Markdown du vault peuvent être publiés.")
    return resolved


@router.get("/obsidian-notion/items", response_model=ObsidianNotionItemsResponse)
def obsidian_notion_items(
    query: str | None = Query(default=None, description="Recherche par titre, chemin ou tag"),
) -> ObsidianNotionItemsResponse:
    try:
        items = build_items(query)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return ObsidianNotionItemsResponse(items=items, total=len(items))


@router.get("/obsidian-notion/stats", response_model=ObsidianNotionStats)
def obsidian_notion_stats() -> ObsidianNotionStats:
    try:
        return build_stats(build_items())
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/obsidian-to-notion")
def obsidian_to_notion(body: ObsidianToNotionIn):
    parent = (
        body.parent_id
        or os.environ.get("NOTION_OBSIDIAN_PARENT_ID")
        or os.environ.get("NOTION_PARENT_PAGE_ID")
        or os.environ.get("NOTION_PARENT_ID")
    )
    if not parent:
        raise HTTPException(
            status_code=400,
            detail="Parent Notion manquant (NOTION_OBSIDIAN_PARENT_ID/NOTION_PARENT_PAGE_ID/NOTION_PARENT_ID)",
        )

    try:
        markdown_path = _resolve_obsidian_markdown_path(body.path)
        out = send_markdown_to_notion_safe(
            markdown_path=str(markdown_path),
            parent_id=parent,
            parent_is_db=body.parent_is_db,
            db_title_name=body.db_title_name or os.environ.get("NOTION_DB_TITLE_NAME", "Name"),
        )
        return {"ok": True, "notion": out}
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


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
        ref = publish_wikipedia_page_to_notion(body.query, parent_page_id=parent)
        return {"ok": True, "notion": {"id": ref.page_id, "url": ref.url}}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


@router.get("/ping")
def orchestration_ping():
    return {"status": "ok", "module": "orchestrations"}
