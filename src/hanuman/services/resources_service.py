from __future__ import annotations

import os
from typing import Any
from urllib.parse import quote_plus, urlencode
from xml.etree import ElementTree

import httpx

YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
GALLICA_SRU_URL = "https://gallica.bnf.fr/services/engine/search/sru"
GALLICA_SEARCH_URL = "https://gallica.bnf.fr/services/engine/search/sru"
IMSLP_SEARCH_URL = "https://imslp.org/wiki/Special:Search"

HTTP_HEADERS = {
    "User-Agent": "Hanuman/0.2 (personal research assistant)",
    "Accept": "application/xml,text/xml;q=0.9,application/json;q=0.8,*/*;q=0.5",
}


def youtube_configured() -> bool:
    return bool(os.environ.get("YOUTUBE_API_KEY"))


def search_youtube(
    query: str,
    max_results: int = 25,
    *,
    page_token: str | None = None,
) -> dict[str, Any]:
    api_key = os.environ.get("YOUTUBE_API_KEY")
    if not api_key:
        raise ValueError("YouTube non configuré : ajoute YOUTUBE_API_KEY dans .env")

    params: dict[str, str | int] = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": max(1, min(max_results, 50)),
        "relevanceLanguage": "fr",
        "key": api_key,
    }
    if page_token:
        params["pageToken"] = page_token

    response = httpx.get(
        YOUTUBE_SEARCH_URL,
        params=params,
        headers=HTTP_HEADERS,
        timeout=20,
    )
    response.raise_for_status()
    payload = response.json()

    results: list[dict[str, Any]] = []
    for item in payload.get("items", []):
        video_id = (item.get("id") or {}).get("videoId")
        snippet = item.get("snippet") or {}
        if not video_id:
            continue
        results.append(
            {
                "id": video_id,
                "title": snippet.get("title", "Vidéo sans titre"),
                "description": snippet.get("description"),
                "channel": snippet.get("channelTitle"),
                "published_at": snippet.get("publishedAt"),
                "thumbnail": ((snippet.get("thumbnails") or {}).get("medium") or {}).get("url"),
                "url": f"https://www.youtube.com/watch?v={video_id}",
            }
        )

    return {
        "results": results,
        "next_page_token": payload.get("nextPageToken"),
        "prev_page_token": payload.get("prevPageToken"),
        "total_results": (payload.get("pageInfo") or {}).get("totalResults"),
    }


def build_gallica_search_url(query: str) -> str:
    return "https://gallica.bnf.fr/services/engine/search/sru?" + urlencode(
        {
            "version": "1.2",
            "operation": "searchRetrieve",
            "query": f'(gallica all "{query}")',
            "maximumRecords": 25,
        }
    )


def search_gallica(query: str, max_results: int = 10) -> list[dict[str, Any]]:
    response = httpx.get(
        GALLICA_SRU_URL,
        params={
            "version": "1.2",
            "operation": "searchRetrieve",
            "query": f'(gallica all "{query}")',
            "maximumRecords": max(1, min(max_results, 25)),
            "suggest": 0,
        },
        headers=HTTP_HEADERS,
        follow_redirects=True,
        timeout=25,
    )
    response.raise_for_status()

    root = ElementTree.fromstring(response.text)
    diagnostics = [
        element.text.strip()
        for element in root.iter()
        if element.tag.endswith("message") and element.text and element.text.strip()
    ]
    if diagnostics:
        raise RuntimeError("Réponse SRU Gallica : " + " ; ".join(diagnostics[:3]))

    dc = "{http://purl.org/dc/elements/1.1/}"
    records: list[dict[str, Any]] = []

    for record_data in root.iter():
        if not record_data.tag.endswith("recordData"):
            continue
        titles = [element.text for element in record_data.iter(f"{dc}title") if element.text]
        creators = [element.text for element in record_data.iter(f"{dc}creator") if element.text]
        dates = [element.text for element in record_data.iter(f"{dc}date") if element.text]
        types = [element.text for element in record_data.iter(f"{dc}type") if element.text]
        identifiers = [element.text for element in record_data.iter(f"{dc}identifier") if element.text]
        ark = next((value for value in identifiers if "gallica.bnf.fr/ark:" in value), None)
        records.append(
            {
                "title": titles[0] if titles else "Document sans titre",
                "creators": creators,
                "dates": dates,
                "types": types,
                "ark": ark,
                "url": ark,
            }
        )
    return records


def build_imslp_search_url(query: str) -> str:
    return f"{IMSLP_SEARCH_URL}?{urlencode({'search': query})}"


def build_google_maps_search_url(location: str) -> str:
    return f"https://www.google.com/maps/search/?api=1&query={quote_plus(location)}"


def build_google_maps_directions_url(location: str) -> str:
    return f"https://www.google.com/maps/dir/?api=1&destination={quote_plus(location)}"
