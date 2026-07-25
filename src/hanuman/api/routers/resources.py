from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from hanuman.services.chess_analysis_queue_service import (
    count_analysis_queue,
    get_analysis_queue_status,
    start_analysis_queue,
    stop_analysis_queue,
)
from hanuman.services.local_programs_service import inspect_program, inspect_programs
from hanuman.services.resources_service import (
    build_gallica_search_url,
    build_google_maps_directions_url,
    build_google_maps_search_url,
    search_gallica,
    search_imslp,
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
    max_results: int = Query(default=25, ge=1, le=50),
    page_token: str | None = Query(default=None),
) -> dict[str, object]:
    try:
        page = search_youtube(q, max_results=max_results, page_token=page_token)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Erreur YouTube : {exc}") from exc

    results = page["results"]
    return {
        "ok": True,
        "count": len(results),
        "results": results,
        "next_page_token": page.get("next_page_token"),
        "prev_page_token": page.get("prev_page_token"),
        "total_results": page.get("total_results"),
    }


@router.get("/gallica/status")
def gallica_status() -> dict[str, object]:
    return {
        "ok": True,
        "configured": True,
        "mode": "sru_with_browser_fallback",
    }


@router.get("/gallica/search")
def gallica_search(
    q: str = Query(min_length=1),
    max_results: int = Query(default=10, ge=1, le=25),
) -> dict[str, object]:
    fallback_url = build_gallica_search_url(q)
    try:
        results = search_gallica(q, max_results=max_results)
    except Exception as exc:
        return {
            "ok": False,
            "count": 0,
            "results": [],
            "message": f"La recherche directe Gallica est indisponible : {exc}",
            "fallback_url": fallback_url,
        }
    return {
        "ok": True,
        "count": len(results),
        "results": results,
        "fallback_url": fallback_url,
    }


@router.get("/imslp/status")
def imslp_status() -> dict[str, object]:
    return {"ok": True, "configured": True, "mode": "mediawiki_api"}


@router.get("/imslp/search")
def imslp_search(
    q: str = Query(min_length=1),
    max_results: int = Query(default=20, ge=1, le=50),
) -> dict[str, object]:
    try:
        results = search_imslp(q, max_results=max_results)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Erreur IMSLP : {exc}") from exc
    return {"ok": True, "count": len(results), "results": results}


@router.get("/maps/status")
def maps_status() -> dict[str, object]:
    return {"ok": True, "configured": True, "mode": "universal_urls"}


@router.get("/maps/search")
def maps_search(location: str = Query(min_length=1)) -> dict[str, object]:
    return {"ok": True, "location": location, "url": build_google_maps_search_url(location)}


@router.get("/maps/directions")
def maps_directions(location: str = Query(min_length=1)) -> dict[str, object]:
    return {"ok": True, "location": location, "url": build_google_maps_directions_url(location)}


@router.get("/programs/status")
def programs_status() -> dict[str, object]:
    programs = inspect_programs()
    return {"ok": all(item["ok"] for item in programs), "count": len(programs), "programs": programs}


@router.get("/programs/{program_id}/status")
def program_status(program_id: str) -> dict[str, object]:
    try:
        return inspect_program(program_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Programme inconnu") from exc


@router.get("/chess/analysis/status")
def chess_analysis_status() -> dict[str, object]:
    return {
        "ok": True,
        "queue": count_analysis_queue(),
        "state": get_analysis_queue_status(),
    }


@router.post("/chess/analysis/start")
def chess_analysis_start(
    depth: int = Query(default=12, ge=8, le=24),
    limit: int | None = Query(default=25, ge=1, le=1000),
) -> dict[str, object]:
    return start_analysis_queue(depth=depth, limit=limit)


@router.post("/chess/analysis/stop")
def chess_analysis_stop() -> dict[str, object]:
    return stop_analysis_queue()
