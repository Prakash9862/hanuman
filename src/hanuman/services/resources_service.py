from __future__ import annotations

import os
from typing import Any
from urllib.parse import quote_plus, urlencode
from xml.etree import ElementTree

import httpx

YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
GALLICA_SRU_URL = "https://gallica.bnf.fr/SRU"
IMSLP_SEARCH_URL = "https://imslp.org/wiki/Special:Search"


def youtube_configured() -> bool:
    return bool(os.environ.get("YOUTUBE_API_KEY"))


def search_youtube(query: str, max_results: int = 10) -> list[dict[str, Any]]:
    api_key = os.environ.get("YOUTUBE_API_KEY")
    if not api_key:
        raise ValueError("YouTube non configuré : ajoute YOUTUBE_API_KEY dans .env")

    response = httpx.get(
        YOUTUBE_SEARCH_URL,
        params={
            "part": "snippet",
            "q": query,
            "type": "video",
            "maxResults": max(1, min(max_results, 25)),
            "relevanceLanguage": "fr",
            "key": api_key,
        },
        timeout=20,
    )
    response.raise_for_status()

    results: list[dict[str, Any]] = []
    for item in response.json().get("items", []):
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
    return results


def search_gallica(query: str, max_results: int = 10) -> list[dict[str, Any]]:
    response = httpx.get(
        GALLICA_SRU_URL,
        params={
            "version": "1.2",
            "operation": "searchRetrieve",
            "query": f'gallica all "{query}"',
            "maximumRecords": max(1, min(max_results, 25)),
            "suggest": 0,
        },
        timeout=25,
    )
    response.raise_for_status()

    root = ElementTree.fromstring(response.text)
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
