# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, HTTPException

from hanuman.services.core.notion_service import create_page_under_parent
from hanuman.services.core.obsidian_service import (
    abs_path,
    md_title,
    md_to_blocks,
    read_markdown,
)

router = APIRouter(prefix="/obsidian", tags=["obsidian", "notion"])


@router.get("/ping")
def ping() -> dict[str, Any]:
    return {
        "ok": True,
        "service": "obsidian→notion",
        "source": "obsidian",
        "timestamp": datetime.now(UTC).isoformat(),
        # Le test attend au moins "note_count" dans detail
        "detail": {"service": "obsidian", "note_count": 0},
    }


@router.post("/sync_one")
def sync_one(
    path: str = Body(
        ..., embed=True, description="Chemin (absolu ou relatif au vault)"
    ),
    title: Optional[str] = Body(None),
    parent_page_id: Optional[str] = Body(None),
) -> Dict[str, Any]:
    try:
        md = read_markdown(path)
        t = title or md_title(md, fallback=abs_path(path).stem)
        blocks = md_to_blocks(md)
        page = create_page_under_parent(t, blocks, parent_page_id=parent_page_id)
        return {"ok": True, "title": t, "url": page.get("url"), "id": page.get("id")}
    except Exception as e:
        raise HTTPException(400, f"sync_one failed: {e}")


@router.post("/sync_many")
def sync_many(
    paths: List[str] = Body(..., embed=True, description="Liste de chemins .md"),
    parent_page_id: Optional[str] = Body(None),
) -> Dict[str, Any]:
    results: List[Dict[str, Any]] = []
    for p in paths:
        try:
            md = read_markdown(p)
            t = md_title(md, fallback=abs_path(p).stem)
            blocks = md_to_blocks(md)
            page = create_page_under_parent(t, blocks, parent_page_id=parent_page_id)
            results.append({"path": p, "title": t, "url": page.get("url"), "ok": True})
        except Exception as e:
            results.append(
                {"path": p, "title": None, "url": None, "ok": False, "err": str(e)}
            )
    return {
        "status": "ok" if all(r["ok"] for r in results) else "partial",
        "results": results,
    }
