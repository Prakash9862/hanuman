from __future__ import annotations

import html
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from urllib.parse import unquote, urlparse

import httpx

from hanuman.core.logging import get_logger
from hanuman.models.ping import PingResult
from hanuman.utils.decorators import trace_endpoint

logger = get_logger(__name__)

WIKIPEDIA_BASE_URL = "https://fr.wikipedia.org/api/rest_v1"
WIKIPEDIA_URL = f"{WIKIPEDIA_BASE_URL}/page/summary/OpenAI"
USER_AGENT = "HanumanBot/1.0 (+https://github.com/prakasch; contact: prakash@example.com)"


@trace_endpoint("wikipedia", catch=True)
def ping_wikipedia() -> PingResult:
    """Ping simple vers l'API Wikipedia pour les checks de santé."""
    resp = httpx.get(
        WIKIPEDIA_URL,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
        timeout=5,
    )

    if resp.status_code == 200:
        data = resp.json()
        return PingResult(ok=True, source="wikipedia", detail={"title": data.get("title")})

    if resp.status_code == 404:
        raise ValueError("Article non trouvé")

    raise RuntimeError(f"Unexpected status: {resp.status_code}")


@dataclass
class WikipediaSection:
    """Section simplifiée d'un article Wikipedia."""

    title: str
    content: str


@dataclass
class WikipediaInfoboxItem:
    """Entrée d'infobox Wikipedia (clé → valeur)."""

    label: str
    value: str


@dataclass
class WikipediaPage:
    """Représentation normalisée de la page Wikipedia utilisée par les orchestrations."""

    title: str
    summary: str
    sections: List[WikipediaSection]
    infobox: List[WikipediaInfoboxItem]
    sources: List[str]
    images: List[str]
    url: str


def _strip_html(text: str) -> str:
    """Supprime les balises HTML de Wikipedia et normalise les espaces."""

    if not text:
        return ""

    cleaned = re.sub(r"<\s*br\s*/?>", "\n", text, flags=re.IGNORECASE)
    cleaned = re.sub(r"</(p|div)>", "\n", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"<[^>]+>", "", cleaned)
    cleaned = html.unescape(cleaned)
    cleaned = cleaned.replace("\xa0", " ")
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


def _extract_title(title_or_url: str) -> str:
    """Transforme un titre ou une URL Wikipedia en *title* utilisable par l'API."""

    value = title_or_url.strip()
    if not value:
        raise ValueError("Titre Wikipedia vide")

    if "://" in value:
        parsed = urlparse(value)
        last_segment = parsed.path.rsplit("/", 1)[-1]
    else:
        last_segment = value

    cleaned = unquote(last_segment.split("#", 1)[0])
    return cleaned.replace(" ", "_")


class WikipediaService:
    """Client minimaliste autour de l'API REST Wikipedia."""

    def __init__(
        self,
        *,
        base_url: str = WIKIPEDIA_BASE_URL,
        client: Optional[httpx.Client] = None,
        timeout: float = 10.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._client = client
        self._timeout = timeout

    def _get(self, path: str) -> Dict[str, Any]:
        url = f"{self._base_url}/{path.lstrip('/')}"
        logger.debug("WikipediaService request", extra={"url": url})

        headers = {
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
        }

        try:
            client = self._client or httpx
            response = client.get(url, headers=headers, timeout=self._timeout)
        except httpx.HTTPError as exc:  # pragma: no cover - réseau improbable en test
            raise RuntimeError(f"Erreur réseau vers Wikipedia: {exc}") from exc

        if response.status_code == 404:
            raise ValueError("Article Wikipedia introuvable")

        if response.status_code >= 400:
            raise RuntimeError(
                f"Wikipedia a renvoyé {response.status_code}: {response.text}"
            )

        data = response.json()
        if not isinstance(data, dict):
            raise RuntimeError("Réponse Wikipedia inattendue")

        return data

    def fetch_page(self, title_or_url: str) -> WikipediaPage:
        """Récupère les informations clefs d'une page Wikipedia."""

        title = _extract_title(title_or_url)

        # 1) Résumé
        summary_data = self._get(f"page/summary/{title}")

    # 2) Sections complètes (mobile-sections)
        try:
            sections_data = self._get(f"page/mobile-sections/{title}")
        except RuntimeError as exc:
            if "Mobile Content Service is decommissioned" in str(exc):
                logger.warning(
                    "Wikipedia mobile-sections API décommissionnée : "
                    "continuer sans sections détaillées."
                )
                sections_data = {}  # Fallback propre
            else:
                raise



        summary = str(summary_data.get("extract") or "").strip()
        display_title = str(
            summary_data.get("title") or summary_data.get("displaytitle") or title
        )
        url = (
            summary_data.get("content_urls", {})
            .get("desktop", {})
            .get("page", f"https://fr.wikipedia.org/wiki/{title}")
        )

        # Images
        images: List[str] = []
        thumb = summary_data.get("originalimage") or summary_data.get("thumbnail")
        if isinstance(thumb, dict):
            source = thumb.get("source")
            if isinstance(source, str):
                images.append(source)

        # Sections brutes (lead + remaining)
        raw_sections: List[Dict[str, Any]] = []
        if isinstance(sections_data, dict):
            lead = sections_data.get("lead", {})
            remaining = sections_data.get("remaining", {})

            if isinstance(lead, dict):
                lead_sections = lead.get("sections")
                if isinstance(lead_sections, list):
                    raw_sections.extend(
                        [s for s in lead_sections if isinstance(s, dict)]
                    )

            if isinstance(remaining, dict):
                remaining_sections = remaining.get("sections")
                if isinstance(remaining_sections, list):
                    raw_sections.extend(
                        [s for s in remaining_sections if isinstance(s, dict)]
                    )

        sections: List[WikipediaSection] = []
        for section in raw_sections:
            sec_title = str(section.get("line") or "").strip()
            text_html = str(section.get("text") or "")
            content = _strip_html(text_html)
            if sec_title or content:
                sections.append(WikipediaSection(title=sec_title, content=content))

        # Infobox
        infobox: List[WikipediaInfoboxItem] = []
        lead = sections_data.get("lead", {}) if isinstance(sections_data, dict) else {}
        infobox_raw = lead.get("infobox")
        if isinstance(infobox_raw, list):
            for item in infobox_raw:
                if not isinstance(item, dict):
                    continue
                label = _strip_html(str(item.get("label") or ""))
                value = _strip_html(str(item.get("value") or ""))
                if not label and not value:
                    continue
                infobox.append(WikipediaInfoboxItem(label=label, value=value))

        # Sources : on cherche une section 'Références' / 'Sources'
        sources: List[str] = []
        for section in raw_sections:
            title_lower = str(section.get("line") or "").lower()
            anchor = str(section.get("anchor") or "").lower()
            if any(
                key in title_lower
                for key in ("références", "references", "bibliographie", "sources")
            ) or any(key in anchor for key in ("references", "notes", "sources")):
                text_html = str(section.get("text") or "")
                items = re.split(r"<li[^>]*>", text_html)
                for raw in items:
                    cleaned = _strip_html(raw)
                    if cleaned:
                        sources.append(cleaned)

        return WikipediaPage(
            title=display_title,
            summary=summary,
            sections=sections,
            infobox=infobox,
            sources=sources,
            images=images,
            url=url,
        )
