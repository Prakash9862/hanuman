from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from hanuman.services.resources_service import (
    build_google_maps_directions_url,
    build_google_maps_search_url,
    build_imslp_search_url,
    search_gallica,
    search_youtube,
    youtube_configured,
)

router = APIRouter(prefix="/resources", tags=["resources"])


@router.get("/youtube/status")
def youtube_status() -> dict[str, object]:
    configured = youtube_configured()
    return {
        "ok": configured,
        "configured": configured,
        "message": None if configured else "YOUTUBE_API_KEY absente",
    }


@router.get("/youtube/search")
def youtube_search(
    q: str = Query(min_length=1),
    max_results: int = Query(default=10, ge=1, le=25),
) -> dict[str, object]:
    try:
        results = search_youtube(q, max_results=max_results)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Erreur YouTube : {exc}") from exc
    return {"ok": True, "count": len(results), "results": results}


@router.get("/gallica/status")
def gallica_status() -> dict[str, object]:
    return {"ok": True, "configured": True}


@router.get("/gallica/search")
def gallica_search(
    q: str = Query(min_length=1),
    max_results: int = Query(default=10, ge=1, le=25),
) -> dict[str, object]:
    try:
        results = search_gallica(q, max_results=max_results)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Erreur Gallica : {exc}") from exc
    return {"ok": True, "count": len(results), "results": results}


@router.get("/imslp/status")
def imslp_status() -> dict[str, object]:
    return {
        "ok": True,
        "configured": True,
        "mode": "search_link",
    }


@router.get("/imslp/search")
def imslp_search(q: str = Query(min_length=1)) -> dict[str, object]:
    return {
        "ok": True,
        "query": q,
        "url": build_imslp_search_url(q),
    }


@router.get("/maps/search")
def maps_search(location: str = Query(min_length=1)) -> dict[str, object]:
    return {
        "ok": True,
        "location": location,
        "url": build_google_maps_search_url(location),
    }


@router.get("/maps/directions")
def maps_directions(location: str = Query(min_length=1)) -> dict[str, object]:
    return {
        "ok": True,
        "location": location,
        "url": build_google_maps_directions_url(location),
    }
