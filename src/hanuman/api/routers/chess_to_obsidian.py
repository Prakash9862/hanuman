from fastapi import APIRouter, Query

from hanuman.orchestrations.chess_to_obsidian import sync_chess_to_obsidian

router = APIRouter(prefix="/chess", tags=["chess"])


@router.post("/sync", summary="Synchronise Chess.com vers Obsidian")
def sync_chess(limit: int = Query(200, ge=1, le=2000)) -> dict:
    return sync_chess_to_obsidian(limit=limit)
