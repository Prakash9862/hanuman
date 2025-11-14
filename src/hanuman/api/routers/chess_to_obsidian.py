from fastapi import APIRouter, Query

from hanuman.orchestrations.chess_to_obsidian import sync_chess_to_obsidian

router = APIRouter(
    prefix="/chess",
    tags=["chess"],
)


@router.post("/sync", summary="Sync Chess.com games to Obsidian vault")
def sync_chess(limit: int = Query(200, ge=1, le=2000)) -> dict:
    """
    Lance la synchronisation des parties Chess.com vers le vault Obsidian Echecs.
    """
    sync_chess_to_obsidian(limit=limit)
    return {
        "status": "ok",
        "synced": True,
        "limit": limit,
    }
