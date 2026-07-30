from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from hanuman.orchestrations.chess_analysis import _validated_chess_root
from hanuman.services.chess_analysis_queue_service import (
    count_analysis_queue,
    get_analysis_queue_status,
    start_analysis_queue,
    stop_analysis_queue,
)
from hanuman.services.chess_view_rebuild_service import refresh_chess_knowledge
from hanuman.services.core.anki_service import list_anki_decks
from hanuman.services.core.clock_service import (
    DEFAULT_TIMEZONE,
    get_clock_snapshot,
    list_timezones,
    ping_clock,
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


@router.get("/devdocs/status")
def devdocs_status() -> dict[str, object]:
    from hanuman.services.core.devdocs_service import ping_devdocs

    status = ping_devdocs()
    return {
        "ok": status.ok,
        "configured": status.configured,
        "message": status.message,
        "url": status.url,
    }


@router.get("/devdocs/documentations")
def devdocs_documentations() -> dict[str, object]:
    from hanuman.services.connectors.devdocs import DevdocsConnectorError
    from hanuman.services.core.devdocs_service import list_devdocs_documentations

    try:
        documentations = list_devdocs_documentations()
    except DevdocsConnectorError as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        ) from exc

    return {
        "ok": True,
        "count": len(documentations),
        "documentations": [documentation.to_dict() for documentation in documentations],
    }


@router.get("/devdocs/search")
def devdocs_search(
    q: str = Query(min_length=1),
) -> dict[str, object]:
    from hanuman.services.core.devdocs_service import build_devdocs_search

    try:
        result = build_devdocs_search(q)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "ok": True,
        **result,
    }


@router.get("/maps/search")
def maps_search(location: str = Query(min_length=1)) -> dict[str, object]:
    return {"ok": True, "location": location, "url": build_google_maps_search_url(location)}


@router.get("/maps/directions")
def maps_directions(location: str = Query(min_length=1)) -> dict[str, object]:
    return {"ok": True, "location": location, "url": build_google_maps_directions_url(location)}


@router.get("/programs/status")
def programs_status() -> dict[str, object]:
    programs = inspect_programs()
    return {
        "ok": all(item["ok"] for item in programs),
        "count": len(programs),
        "programs": programs,
    }


@router.get("/anki/decks")
def anki_decks() -> dict[str, object]:
    try:
        decks = list_anki_decks()
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Impossible de lire les paquets Anki : {exc}",
        ) from exc

    return {
        "ok": True,
        "count": len(decks),
        "decks": decks,
    }


@router.get("/clock/status")
def clock_status() -> dict[str, object]:
    """Retourne l'état de la capacité temporelle locale."""

    result = ping_clock()
    return result.model_dump()


@router.get("/clock/now")
def clock_now(
    timezone: str = Query(default=DEFAULT_TIMEZONE, min_length=1),
) -> dict[str, object]:
    """Retourne l'instant courant enrichi dans le fuseau demandé."""

    try:
        snapshot = get_clock_snapshot(timezone)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "ok": True,
        **snapshot.to_dict(),
    }


@router.get("/clock/timezones")
def clock_timezones(
    q: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
) -> dict[str, object]:
    """Liste les fuseaux IANA disponibles."""

    timezones = list_timezones(query=q, limit=limit)

    return {
        "ok": True,
        "count": len(timezones),
        "timezones": timezones,
    }


# scaffold:connector-routes:start
@router.get("/contacts/status")
def contacts_status() -> dict[str, object]:
    from hanuman.services.core.contacts_service import ping_contacts

    status = ping_contacts()
    return {
        "ok": status.ok,
        "configured": status.configured,
        "message": status.message,
    }


@router.get("/monkeytype/status")
def monkeytype_status() -> dict[str, object]:
    from hanuman.services.core.monkeytype_service import ping_monkeytype

    status = ping_monkeytype()
    return {
        "ok": status.ok,
        "configured": status.configured,
        "message": status.message,
    }


# scaffold:connector-routes:end


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


@router.post("/chess/knowledge/refresh")
def chess_knowledge_refresh() -> dict[str, object]:
    try:
        report = refresh_chess_knowledge(_validated_chess_root())
    except (OSError, UnicodeError, ValueError, RuntimeError) as exc:
        raise HTTPException(
            status_code=500, detail=f"Actualisation Chess impossible : {exc}"
        ) from exc
    return {
        "ok": True,
        "message": (
            f"{report.notes_discovered} parties trouvées ; "
            f"{report.analyses_valid} analyses valides ; "
            f"{report.games_pending} parties non analysées ; "
            f"{report.analyses_orphaned} analyse(s) orpheline(s) ; "
            f"{report.views_written} vue(s) Obsidian reconstruite(s)."
        ),
        "report": {
            "games_found": report.notes_discovered,
            "analyses_valid": report.analyses_valid,
            "games_pending": report.games_pending,
            "analyses_invalid": report.analyses_invalid,
            "analyses_orphaned": report.analyses_orphaned,
            "views_written": report.views_written,
            "opening_indexes_written": report.opening_indexes_written,
        },
    }
