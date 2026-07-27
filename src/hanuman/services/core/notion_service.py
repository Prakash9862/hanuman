# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, cast

import requests

from hanuman.config.env import (
    NOTION_PARENT_ID,
    NOTION_TOKEN,
    NOTION_VERSION,
)

API_BASE_URL = "https://api.notion.com"


# ---------------------------------------------------------------------------
# Exceptions dédiées
# ---------------------------------------------------------------------------


class NotionAuthError(RuntimeError):
    """Erreur d'authentification Notion (token manquant ou invalide)."""


class NotionApiError(RuntimeError):
    """Erreur renvoyée par l'API Notion."""


# ---------------------------------------------------------------------------
# Modèles simples
# ---------------------------------------------------------------------------


@dataclass
class NotionPageRef:
    page_id: str
    url: str


@dataclass
class NotionDatabaseRef:
    database_id: str
    data_source_id: str
    url: str


# ---------------------------------------------------------------------------
# Client / Service Notion centralisé
# ---------------------------------------------------------------------------


class NotionService:
    """Client Notion central pour Hanuman.

    - Utilise le token et la version d'API définis dans hanuman.config.env
    - Fournit des méthodes génériques : create_page, append_blocks, search, etc.
    - Sert de base à tous les orchestrateurs (Obsidian, GitHub, …)
    """

    def __init__(
        self,
        token: Optional[str] = None,
        api_base_url: str = API_BASE_URL,
        notion_version: Optional[str] = None,
    ) -> None:
        self._token = (token or NOTION_TOKEN or "").strip()
        if not self._token:
            raise NotionAuthError(
                "NOTION_TOKEN manquant. Configure-le dans le .env ou passe-le au constructeur."
            )

        self._api_base_url = api_base_url.rstrip("/")
        self._notion_version = (notion_version or NOTION_VERSION or "").strip() or "2025-09-03"
        # Cache local: database_id -> data_source_id (pour l'API 2025-09-03)
        self._data_source_cache: Dict[str, str] = {}

        # ----------------- internes ----------------- #

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self._token}",
            "Notion-Version": self._notion_version,
            "Content-Type": "application/json",
        }

    def _url(self, path: str) -> str:
        """
        Construit l'URL complète pour l'API Notion.

        - API_BASE_URL = "https://api.notion.com"
        - Tous les endpoints passent par /v1/...
        - `path` ne doit **pas** contenir /v1 au début.
        """
        cleaned = path.lstrip("/")  # "databases/xxx/query"
        return f"{self._api_base_url}/v1/{cleaned}"

    def _request(
        self,
        method: str,
        path: str,
        *,
        payload: Optional[Dict[str, Any]] = None,
        timeout: float = 30.0,
    ) -> Dict[str, Any]:
        """
        Enveloppe bas niveau autour de requests.

        - `path` est un chemin relatif sans /v1 (ex: "databases/{id}/query").
        - L'URL finale sera : https://api.notion.com/v1/<path>.
        """
        url = self._url(path)

        try:
            resp = requests.request(
                method=method,
                url=url,
                headers=self._headers(),
                json=payload if payload is not None else None,
                timeout=timeout,
            )
        except requests.RequestException as exc:
            raise NotionApiError(f"Erreur réseau vers Notion: {exc}") from exc

        if resp.status_code == 401:
            raise NotionAuthError("Token Notion invalide ou expiré.")

        if resp.status_code >= 300:
            raise NotionApiError(f"Erreur Notion {resp.status_code}: {resp.text}")

        return cast(Dict[str, Any], resp.json())

        # ----------------- helpers internes data_sources (API 2025-09-03) ----------------- #

    def _is_datasource_api(self) -> bool:
        """Retourne True si on utilise une version de l'API basée sur les data sources."""
        return self._notion_version.startswith("2025-")

    def _get_data_source_id_for_database(self, db_id: str) -> str:
        """
        Pour l'API 2025-09-03 :
        - On part d'un database_id
        - On récupère la liste des data_sources associées
        - On prend la première par défaut (cas classique: une seule)
        """
        db_id = db_id.strip()
        if not db_id:
            raise NotionApiError("database_id vide dans _get_data_source_id_for_database().")

        # cache pour éviter un GET à chaque query
        if db_id in self._data_source_cache:
            return self._data_source_cache[db_id]

        data = self._request("GET", f"databases/{db_id}")

        data_sources = data.get("data_sources") or []
        if not data_sources:
            raise NotionApiError(
                f"Aucune data_source trouvée pour la database {db_id} "
                "(vérifie que tu utilises bien l'API 2025-09-03 et que la database a au moins une data source)."
            )

        first = data_sources[0]
        raw_id = first.get("id", "")
        ds_id = str(raw_id).strip()
        if not ds_id:
            raise NotionApiError(
                f"Réponse Notion inattendue: data_source sans 'id' pour la database {db_id}."
            )

        self._data_source_cache[db_id] = ds_id
        return ds_id

    def _query_path_for_database(self, db_id: str) -> str:
        """
        Construit le path à utiliser pour une query selon la version de l'API :
        - ≤ 2022-06-28 : /v1/databases/{db_id}/query
        - 2025-09-03 :   /v1/data_sources/{data_source_id}/query
        """
        if self._is_datasource_api():
            ds_id = self._get_data_source_id_for_database(db_id)
            return f"data_sources/{ds_id}/query"

        return f"databases/{db_id}/query"

    # ----------------- API publique : pages ----------------- #

    def create_page_under_parent(
        self,
        title: str,
        blocks: List[Dict[str, Any]],
        parent_page_id: Optional[str] = None,
    ) -> NotionPageRef:
        """Crée une page enfant sous une page Notion (parent page_id)."""
        parent = (parent_page_id or (NOTION_PARENT_ID or "")).strip()
        if not parent:
            raise NotionApiError("NOTION_PARENT_ID manquant (dans .env ou param).")

        payload: Dict[str, Any] = {
            "parent": {"page_id": parent},
            "properties": {"title": {"title": [{"type": "text", "text": {"content": title}}]}},
        }

        if blocks:
            payload["children"] = blocks[:95]

        data = self._request("POST", "pages", payload=payload)
        page_id = data.get("id", "")
        url = data.get("url", "")

        return NotionPageRef(page_id=page_id, url=url)

    def create_page_in_database(
        self,
        database_id: str,
        properties: Dict[str, Any],
        children: Optional[List[Dict[str, Any]]] = None,
    ) -> NotionPageRef:
        """Crée une page dans une database Notion existante."""
        db_id = database_id.strip()
        if not db_id:
            raise NotionApiError("database_id manquant pour create_page_in_database().")

        payload: Dict[str, Any] = {
            "parent": {"database_id": db_id},
            "properties": properties,
        }

        if children:
            payload["children"] = children[:95]

        data = self._request("POST", "pages", payload=payload)
        page_id = data.get("id", "")
        url = data.get("url", "")

        return NotionPageRef(page_id=page_id, url=url)

    def create_page_in_data_source(
        self,
        database_id: str,
        properties: Dict[str, Any],
        children: Optional[List[Dict[str, Any]]] = None,
    ) -> NotionPageRef:
        """Crée une page dans la data source principale d'une database."""
        db_id = database_id.strip()
        if not db_id:
            raise NotionApiError("database_id manquant pour create_page_in_data_source().")
        data_source_id = self._get_data_source_id_for_database(db_id)
        payload: Dict[str, Any] = {
            "parent": {"type": "data_source_id", "data_source_id": data_source_id},
            "properties": properties,
        }
        if children:
            payload["children"] = children[:95]
        data = self._request("POST", "pages", payload=payload)
        return NotionPageRef(page_id=str(data.get("id", "")), url=str(data.get("url", "")))

    def create_database(
        self,
        parent_page_id: str,
        title: str,
        properties: Dict[str, Any],
    ) -> NotionDatabaseRef:
        """Crée une database et sa data source initiale sous une page précise."""
        parent = parent_page_id.strip()
        if not parent:
            raise NotionApiError("parent_page_id manquant pour create_database().")
        payload: Dict[str, Any] = {
            "parent": {"type": "page_id", "page_id": parent},
            "title": [{"type": "text", "text": {"content": title}}],
            "initial_data_source": {"properties": properties},
        }
        data = self._request("POST", "databases", payload=payload)
        database_id = str(data.get("id", "")).strip()
        data_sources = data.get("data_sources") or []
        data_source_id = str(data_sources[0].get("id", "")).strip() if data_sources else ""
        if not database_id or not data_source_id:
            raise NotionApiError("Réponse Notion incomplète après création de database.")
        self._data_source_cache[database_id] = data_source_id
        return NotionDatabaseRef(
            database_id=database_id,
            data_source_id=data_source_id,
            url=str(data.get("url", "")),
        )

    def retrieve_database(self, database_id: str) -> Dict[str, Any]:
        """Relit une database Notion."""
        if not database_id.strip():
            raise ValueError("database_id manquant pour retrieve_database().")
        return self._request("GET", f"databases/{database_id}")

    def retrieve_data_source(self, data_source_id: str) -> Dict[str, Any]:
        """Relit le schéma d'une data source Notion."""
        if not data_source_id.strip():
            raise ValueError("data_source_id manquant pour retrieve_data_source().")
        return self._request("GET", f"data_sources/{data_source_id}")

    def append_blocks(
        self,
        page_id: str,
        blocks: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Ajoute des blocs à une page existante."""
        if not page_id.strip():
            raise ValueError("page_id manquant pour append_blocks().")
        if not blocks:
            return {}

        payload = {
            "children": blocks[:95],
        }

        return self._request(
            "PATCH",
            f"blocks/{page_id}/children",
            payload=payload,
        )

    def update_block(
        self,
        block_id: str,
        block_type: str,
        content: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Met à jour le contenu d'un bloc existant sans le recréer."""
        if not block_id.strip():
            raise ValueError("block_id manquant pour update_block().")
        if not block_type.strip():
            raise ValueError("block_type manquant pour update_block().")
        return self._request(
            "PATCH",
            f"blocks/{block_id}",
            payload={block_type: content},
        )

    def query_database(
        self,
        database_id: str,
        filter_: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Interroge une database Notion et renvoie tous les résultats."""

        db_id = database_id.strip()
        if not db_id:
            raise NotionApiError("database_id manquant pour query_database().")

        base_payload: Dict[str, Any] = {}
        if filter_ is not None:
            base_payload["filter"] = filter_

        results: List[Dict[str, Any]] = []
        next_cursor: Optional[str] = None

        while True:
            payload = dict(base_payload)
            if next_cursor is not None:
                payload["start_cursor"] = next_cursor

            # Choix du bon endpoint selon la version (databases vs data_sources)
            path = self._query_path_for_database(db_id)

            data = self._request(
                "POST",
                path,
                payload=payload,
            )

            results.extend(data.get("results", []))

            if not data.get("has_more"):
                break

            next_cursor = data.get("next_cursor")

        return results

    def update_page_properties(
        self,
        page_id: str,
        properties: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Met à jour uniquement les propriétés d'une page Notion."""
        if not page_id.strip():
            raise ValueError("page_id manquant pour update_page_properties().")

        payload = {"properties": properties}
        return self._request("PATCH", f"pages/{page_id}", payload=payload)

    def retrieve_page(self, page_id: str) -> Dict[str, Any]:
        """Récupère les métadonnées d'une page Notion."""
        if not page_id.strip():
            raise ValueError("page_id manquant pour retrieve_page().")

        return self._request("GET", f"pages/{page_id}")

    def retrieve_block_children(self, block_id: str) -> List[Dict[str, Any]]:
        """Relit tous les blocs enfants directs avec pagination."""
        if not block_id.strip():
            raise ValueError("block_id manquant pour retrieve_block_children().")
        results: List[Dict[str, Any]] = []
        next_cursor: Optional[str] = None
        while True:
            path = f"blocks/{block_id}/children?page_size=100"
            if next_cursor is not None:
                path += f"&start_cursor={next_cursor}"
            data = self._request("GET", path)
            results.extend(data.get("results", []))
            if not data.get("has_more"):
                break
            next_cursor = data.get("next_cursor")
        return results

    def search(
        self,
        query: str,
        limit: int = 20,
    ) -> Dict[str, Any]:
        """Recherche globale dans Notion (pages, databases…)."""
        payload = {
            "query": query,
            "page_size": min(limit, 100),
        }
        return self._request("POST", "search", payload=payload)


# ---------------------------------------------------------------------------
# Compatibilité historique (Obsidian → Notion)
# ---------------------------------------------------------------------------


def _legacy_hdr() -> Dict[str, str]:
    """Ancienne fonction interne, conservée pour compatibilité éventuelle."""
    token = (NOTION_TOKEN or "").strip()
    if not token:
        raise RuntimeError("NOTION_TOKEN manquant.")
    return {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


def create_page_under_parent(
    title: str,
    blocks: List[Dict[str, Any]],
    parent_page_id: str | None = None,
) -> Dict[str, Any]:
    """API historique utilisée par certaines orchestrations.

    Wrapper autour de NotionService.create_page_under_parent
    pour ne pas casser le code existant.
    """
    service = NotionService()
    ref = service.create_page_under_parent(
        title=title,
        blocks=blocks,
        parent_page_id=parent_page_id,
    )
    return {
        "id": ref.page_id,
        "url": ref.url,
    }
