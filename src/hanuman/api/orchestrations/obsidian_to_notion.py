from __future__ import annotations
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pathlib import Path
import os
import requests

router = APIRouter(prefix="/obsidian", tags=["obsidian", "notion"])

NOTION_TOKEN = os.getenv("NOTION_TOKEN", "")
NOTION_VERSION = os.getenv("NOTION_VERSION", "2025-09-03")
DEFAULT_PARENT_ID = os.getenv("NOTION_PARENT_ID", "")  # page_id (avec tirets)

if not NOTION_TOKEN:
    raise RuntimeError("NOTION_TOKEN manquant dans l'environnement.")
if not NOTION_VERSION:
    raise RuntimeError("NOTION_VERSION manquant dans l'environnement.")
if not DEFAULT_PARENT_ID:
    # on laisse possible via requête, mais on prévient tôt
    print("[obsidian_to_notion] ⚠️ NOTION_PARENT_ID absent — pourra être passé dans la requête.")


class SyncOnePayload(BaseModel):
    path: str              # chemin vers le .md
    title: str | None = None
    parent_id: str | None = None  # si absent -> DEFAULT_PARENT_ID


def _md_to_blocks(md: str) -> list[dict]:
    """
    Convertit du Markdown basique → paragraph blocks Notion.
    (Simple et sûr: chaque ligne devient un paragraphe.
     On pourra enrichir plus tard: headings, lists, code, images…)
    """
    blocks: list[dict] = []
    for line in md.splitlines():
        text = line.rstrip()
        if not text:
            # paragraphe vide pour les sauts
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": []}
            })
            continue
        blocks.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {"type": "text", "text": {"content": text}}
                ]
            }
        })
    return blocks or [{
        "object": "block",
        "type": "paragraph",
        "paragraph": {"rich_text": [{"type": "text", "text": {"content": "(empty file)"}}]}
    }]


def _create_page(parent_page_id: str, title: str, children: list[dict]) -> dict:
    url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }
    payload = {
        "parent": {"page_id": parent_page_id},
        "properties": {
            "title": {
                "title": [{"type": "text", "text": {"content": title}}]
            }
        },
        "children": children,
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=30)
    if resp.status_code >= 400:
        raise HTTPException(
            status_code=resp.status_code,
            detail={"where": "notion.pages.create", "payload": payload, "resp": resp.text},
        )
    return resp.json()


@router.post("/sync_one")
def sync_one(payload: SyncOnePayload):
    """
    Pousse un fichier .md (Obsidian) vers Notion en créant une page enfant
    sous la page parent (NOTION_PARENT_ID par défaut).
    """
    md_path = Path(payload.path).expanduser().resolve()
    if not md_path.exists() or not md_path.is_file():
        raise HTTPException(status_code=400, detail=f"Fichier introuvable: {md_path}")

    title = payload.title or md_path.stem
    parent_id = (payload.parent_id or DEFAULT_PARENT_ID).strip()
    if not parent_id:
        raise HTTPException(status_code=400, detail="parent_id manquant (et NOTION_PARENT_ID vide).")

    md_text = md_path.read_text(encoding="utf-8", errors="replace")
    blocks = _md_to_blocks(md_text)
    page = _create_page(parent_id, title, blocks)

    return {
        "ok": True,
        "file": str(md_path),
        "notion_page_id": page.get("id"),
        "notion_url": page.get("url"),
        "title": title,
        "parent_id": parent_id,
    }
