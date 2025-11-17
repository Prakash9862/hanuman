from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from urllib.parse import quote, urlparse

import httpx

from hanuman.core.logging import get_logger
from hanuman.models.ping import PingResult
from hanuman.utils.decorators import trace_endpoint

logger = get_logger(__name__)

WIKIPEDIA_BASE_URL = "https://fr.wikipedia.org/api/rest_v1"
WIKIPEDIA_URL = f"{WIKIPEDIA_BASE_URL}/page/summary/OpenAI"
USER_AGENT = (
    "HanumanBot/1.0 (+https://github.com/prakasch; contact: prakash@example.com)"
)


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
        return PingResult(
            ok=True, source="wikipedia", detail={"title": data.get("title")}
        )

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


@dataclass
class WikipediaSearchResult:
    """Résultat de recherche Wikipedia simplifié."""

    title: str
    description: str
    url: str


def _strip_html(text: str) -> str:
    """
    Supprime TOUT le HTML et extensions MediaWiki.
    """
    import re
    from html import unescape

    if not text:
        return ""

    # Supprimer balises complexes MediaWiki (maplink, ref, table wiki)
    text = re.sub(r"<maplink[\s\S]*?</maplink>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"<ref[\s\S]*?</ref>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"<ref[^/>]*/>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"{\|[\s\S]*?\|}", "", text, flags=re.MULTILINE)  # tables wiki

    # Supprimer TOUTES les balises HTML
    text = re.sub(r"</?[^>]+>", "", text)

    # Échapper les entités HTML résiduelles (&nbsp; etc.)
    text = unescape(text)

    # Nettoyage des codes MediaWiki ({{...}}, [[...]], etc.)
    text = re.sub(r"\{\{[^}]+\}\}", "", text)  # templates
    text = re.sub(r"\[\[[^\]]+\|([^\]]+)\]\]", r"\1", text)  # [[lien|texte]]
    text = re.sub(r"\[\[([^\]]+)\]\]", r"\1", text)  # [[lien]]
    text = re.sub(r"\[https?:\/\/[^\s]+\s([^\]]+)\]", r"\1", text)  # [url texte]
    text = re.sub(r"\[https?:\/\/[^\]]+\]", "", text)  # [url]

    # Suppression espaces multiples
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def _extract_title(value: str) -> str:
    """Normalise un titre ou une URL Wikipedia en titre API.

    - "OpenAI"            -> "OpenAI"
    - "OpenAI Research"   -> "OpenAI_Research"
    - "https://fr.wikipedia.org/wiki/OpenAI#Historique" -> "OpenAI"
    """
    value = value.strip()
    if not value:
        raise ValueError("title_or_url ne peut pas être vide.")

    # Cas URL Wikipedia
    if value.startswith("http://") or value.startswith("https://"):
        parsed = urlparse(value)
        path = parsed.path or ""

        # On récupère la partie après /wiki/
        if "/wiki/" in path:
            title = path.split("/wiki/", 1)[1]
        else:
            title = path.rsplit("/", 1)[-1]

        # On enlève un éventuel fragment (#Section)
        if "#" in title:
            title = title.split("#", 1)[0]

        return title or value

    # Cas titre brut : espaces -> underscores
    return value.replace(" ", "_")


def _get_html(
    path: str,
    *,
    base_url: str,
    client: Optional[httpx.Client] = None,
    timeout: float = 10.0,
) -> str:
    """Récupère le HTML brut depuis l'API REST Wikipedia."""

    url = f"{base_url.rstrip('/')}/{path.lstrip('/')}"
    logger.debug("WikipediaService HTML request", extra={"url": url})

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html",
    }

    try:
        http_client = client or httpx
        response = http_client.get(url, headers=headers, timeout=timeout)
    except httpx.HTTPError as exc:  # pragma: no cover - réseau improbable en test
        raise RuntimeError(f"Erreur réseau vers Wikipedia (HTML): {exc}") from exc

    if response.status_code == 404:
        raise ValueError("Article Wikipedia introuvable (HTML)")

    if response.status_code >= 400:
        raise RuntimeError(
            f"Wikipedia HTML a renvoyé {response.status_code}: {response.text}"
        )

    return response.text


def _build_long_summary(html_text: str, max_chars: int = 4000) -> str:
    """
    Construit un résumé long à partir de l'introduction (avant le premier h2/h3/h4).
    """

    if not html_text:
        return ""

    # On coupe au premier titre de section
    heading_pattern = re.compile(r"<h[2-4][^>]*>", re.IGNORECASE)
    m = heading_pattern.search(html_text)
    intro_html = html_text[: m.start()] if m else html_text

    # On récupère tous les paragraphes de l'intro
    paragraphs = re.findall(
        r"<p[^>]*>(.*?)</p>",
        intro_html,
        flags=re.IGNORECASE | re.DOTALL,
    )
    chunks: List[str] = []
    for p in paragraphs:
        txt = _strip_html(p)
        if txt:
            chunks.append(txt)

    intro_text = "\n\n".join(chunks).strip()
    if not intro_text:
        return ""

    if len(intro_text) > max_chars:
        # On coupe proprement à la fin d'un mot
        trimmed = intro_text[:max_chars]
        last_space = trimmed.rfind(" ")
        if last_space > 0:
            trimmed = trimmed[:last_space]
        return trimmed.strip() + "…"

    return intro_text


def _split_sections_from_html(html_text: str) -> List[WikipediaSection]:
    """
    Découpe le HTML en sections basées sur les titres h2/h3/h4.
    Chaque section = titre + contenu suivant jusqu'au prochain titre.
    """

    sections: List[WikipediaSection] = []
    if not html_text:
        return sections

    pattern = re.compile(
        r"<h([2-4])[^>]*>(.*?)</h\1>",
        flags=re.IGNORECASE | re.DOTALL,
    )
    matches = list(pattern.finditer(html_text))
    if not matches:
        return sections

    for idx, match in enumerate(matches):
        heading_html = match.group(2)
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(html_text)
        body_html = html_text[start:end]

        title = _strip_html(heading_html)
        cleaned = _strip_html(body_html)
        content = clean_wikipedia_text(cleaned)

        if title or content:
            sections.append(WikipediaSection(title=title, content=content))

    return sections


def _extract_infobox_and_sources_from_html(
    html_text: str,
) -> tuple[List[WikipediaInfoboxItem], List[str]]:
    """
    Extrait grossièrement :
    - les infos d'infobox (tableau à droite)
    - les références (liste <ol class="references">)
    """

    infobox_items: List[WikipediaInfoboxItem] = []
    sources: List[str] = []

    if not html_text:
        return infobox_items, sources

    # --- Infobox ---------------------------------------------------------
    infobox_match = re.search(
        r"<table[^>]*class=\"[^\"]*infobox[^\"]*\"[^>]*>(.*?)</table>",
        html_text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if infobox_match:
        table_html = infobox_match.group(1)
        rows = re.findall(
            r"<tr[^>]*>(.*?)</tr>",
            table_html,
            flags=re.IGNORECASE | re.DOTALL,
        )
        for row in rows:
            header_match = re.search(
                r"<th[^>]*>(.*?)</th>",
                row,
                flags=re.IGNORECASE | re.DOTALL,
            )
            cell_match = re.search(
                r"<td[^>]*>(.*?)</td>",
                row,
                flags=re.IGNORECASE | re.DOTALL,
            )

            label = _strip_html(header_match.group(1)) if header_match else ""
            value = _strip_html(cell_match.group(1)) if cell_match else ""

            if label or value:
                infobox_items.append(WikipediaInfoboxItem(label=label, value=value))

    # --- Sources / références --------------------------------------------
    refs_match = re.search(
        r"<ol[^>]*class=\"[^\"]*references[^\"]*\"[^>]*>(.*?)</ol>",
        html_text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if refs_match:
        list_html = refs_match.group(1)
        parts = re.split(
            r"<li[^>]*>",
            list_html,
            flags=re.IGNORECASE,
        )
        for raw in parts:
            cleaned = _strip_html(raw).strip()
            if cleaned:
                sources.append(cleaned)

    return infobox_items, sources


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

        # 1) Résumé / métadonnées simples
        summary_data = self._get(f"page/summary/{title}")

        display_title = str(
            summary_data.get("title") or summary_data.get("displaytitle") or title
        )

        url = (
            summary_data.get("content_urls", {})
            .get("desktop", {})
            .get("page", f"https://fr.wikipedia.org/wiki/{title}")
        )

        # Image principale
        images: List[str] = []
        thumb = summary_data.get("originalimage") or summary_data.get("thumbnail")
        if isinstance(thumb, dict):
            source = thumb.get("source")
            if isinstance(source, str):
                images.append(source)

        # 2) HTML complet pour sections / résumé long / infobox / sources
        try:
            html_text = _get_html(
                f"page/html/{title}",
                base_url=self._base_url,
                client=self._client,
                timeout=self._timeout,
            )
        except Exception as exc:  # noqa: BLE001
            # Fallback : au moins on garde le résumé court
            logger.warning(
                "Impossible de récupérer le HTML complet Wikipedia, "
                "fallback sur le summary uniquement.",
                extra={"error": str(exc)},
            )
            summary = str(summary_data.get("extract") or "").strip()
            return WikipediaPage(
                title=display_title,
                summary=summary,
                sections=[],
                infobox=[],
                sources=[],
                images=images,
                url=url,
            )

        # Résumé très complet (intro entière)
        long_summary = _build_long_summary(html_text)
        raw_summary = long_summary or str(summary_data.get("extract") or "").strip()
        summary = clean_wikipedia_text(raw_summary)

        # Sections structurées
        sections = _split_sections_from_html(html_text)

        # Infobox + sources
        infobox, sources = _extract_infobox_and_sources_from_html(html_text)

        return WikipediaPage(
            title=display_title,
            summary=summary,
            sections=sections,
            infobox=infobox,
            sources=sources,
            images=images,
            url=url,
        )

    def search_pages(
        self, query: str, *, limit: int = 5
    ) -> List[WikipediaSearchResult]:
        """
        Recherche des pages Wikipedia pertinentes pour une requête donnée.

        Retourne une liste de WikipediaSearchResult (titre, description, url).
        """
        q = (query or "").strip()
        if not q:
            raise ValueError("query ne peut pas être vide pour search_pages().")

        # Endpoint REST de recherche de titres
        path = f"search/title?q={quote(q)}&limit={limit}"
        data = self._get(path)

        pages = data.get("pages") or []
        results: List[WikipediaSearchResult] = []

        for item in pages[:limit]:
            if not isinstance(item, dict):
                continue

            title = str(item.get("title") or "").strip()
            if not title:
                continue

            description = str(
                item.get("description") or item.get("extract") or ""
            ).strip()

            url = (
                item.get("content_urls", {})
                .get("desktop", {})
                .get("page", f"https://fr.wikipedia.org/wiki/{_extract_title(title)}")
            )

            results.append(
                WikipediaSearchResult(
                    title=title,
                    description=description,
                    url=url,
                )
            )

        return results


def clean_wikipedia_text(text: str) -> str:
    """
    Prend du texte Wikipédia (HTML / wikitexte / Parsoid),
    retire le bruit technique et renvoie un paragraphe lisible pour Notion.
    """
    if not text:
        return ""

    # 1) Base : on enlève HTML + wikitexte "classique"
    cleaned = _strip_html(text)

    # 2) On vire les fragments JSON / Parsoid qui traînent parfois dans le flux
    #    du style  "html":"<div ...>", data-mw=..., etc.
    cleaned = re.sub(r'"html"\s*:\s*".*?"', "", cleaned)
    cleaned = re.sub(r'"data-mw"\s*:\s*\{.*?\}', "", cleaned)
    cleaned = re.sub(r"data-mw='.*?'", "", cleaned)

    # 3) Tokens purement techniques (mw-*, noviewer, ids internes...)
    tokens: list[str] = []
    for token in cleaned.split():
        lower = token.lower()
        if "mw-" in lower or "noviewer" in lower:
            continue
        if lower.startswith('id="mw') or lower.startswith('id=\\"mw'):
            continue
        tokens.append(token)
    cleaned = " ".join(tokens)

    # 4) Ponctuation et références résiduelles
    cleaned = cleaned.replace(" ,", ",")
    cleaned = cleaned.replace(" .", ".")
    cleaned = cleaned.replace(" ;", ";")
    cleaned = cleaned.replace(" :", ":")
    cleaned = cleaned.replace("( ", "(").replace(" )", ")")

    # Numéros de notes [1], [12], [a]...
    cleaned = re.sub(r"\[[^\]]+\]", "", cleaned)

    # Espaces multiples
    cleaned = re.sub(r"\s{2,}", " ", cleaned)

    return cleaned.strip()
