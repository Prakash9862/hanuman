# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, cast

import requests

from hanuman.config.env import (
    NOTION_PARENT_ID,
    NOTION_TOKEN,
    NOTION_VERSION,
)

API_BASE_URL = "https://api.notion.com/v1"


# ---------------------------------------------------------------------------
# Exceptions dédiées
# ---------------------------------------------------------------------------


class NotionAuthError(RuntimeError):
    """Erreur d'authentification Notion (token manquant ou invalide)."""


class NotionApiError(RuntimeError):
    """Erreur renvoyée par l'API Notion."""


# ---------------------------------------------------------------------------
# Modèles simples pour structurer un minimum
# ---------------------------------------------------------------------------


@dataclass
class NotionPageRef:
    page_id: str
    url: str


# ---------------------------------------------------------------------------
# Client / Service Notion centralisé
# ---------------------------------------------------------------------------


class NotionService:
    """Client Notion central pour Hanuman.

    - Utilise le token et la version d'API définis dans hanuman.config.env
    - Fournit des méthodes génériques : create_page, append_blocks, etc.
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
        self._notion_version = (
            notion_version or NOTION_VERSION
        ).strip() or "2025-09-03"

    # ----------------- internes ----------------- #

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self._token}",
            "Notion-Version": self._notion_version,
            "Content-Type": "application/json",
        }

    def _url(self, path: str) -> str:
        return f"{self._api_base_url}/{path.lstrip('/')}"

    def _request(
        self,
        method: str,
        path: str,
        *,
        payload: Optional[Dict[str, Any]] = None,
        timeout: float = 30.0,
    ) -> Dict[str, Any]:
        """Enveloppe bas niveau autour de requests."""
        data: Optional[str] = None
        if payload is not None:
            data = json.dumps(payload)

        try:
            resp = requests.request(
                method=method,
                url=self._url(path),
                headers=self._headers(),
                data=data,
                timeout=timeout,
            )
        except requests.RequestException as exc:
            raise NotionApiError(f"Erreur réseau vers Notion: {exc}") from exc

        if resp.status_code == 401:
            raise NotionAuthError("Token Notion invalide ou expiré.")

        if resp.status_code >= 300:
            raise NotionApiError(f"Erreur Notion {resp.status_code}: {resp.text}")

        return cast(Dict[str, Any], resp.json())

    # ----------------- API publique ----------------- #

    def create_page_under_parent(
        self,
        title: str,
        blocks: List[Dict[str, Any]],
        parent_page_id: Optional[str] = None,
    ) -> NotionPageRef:
        """Crée une page enfant sous une page Notion (parent page_id).

        - title : titre de la page (propriété 'title')
        - blocks : liste de blocs Notion déjà prêts (children)
        - parent_page_id : UUID (avec tirets). Si None, NOTION_PARENT_ID est utilisé.
        """
        parent = (parent_page_id or (NOTION_PARENT_ID or "")).strip()
        if not parent:
            raise NotionApiError("NOTION_PARENT_ID manquant (dans .env ou param).")

        payload: Dict[str, Any] = {
            "parent": {"page_id": parent},
            "properties": {
                "title": {"title": [{"type": "text", "text": {"content": title}}]}
            },
        }

        # petite marge de sécurité pour éviter les erreurs "too many children"
        if blocks:
            payload["children"] = blocks[:95]

        data = self._request("POST", "/pages", payload=payload)
        page_id = data.get("id", "")
        url = data.get("url", "")

        return NotionPageRef(page_id=page_id, url=url)

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
            f"/blocks/{page_id}/children",
            payload=payload,
        )

    def retrieve_page(self, page_id: str) -> Dict[str, Any]:
        """Récupère les métadonnées d'une page Notion."""
        if not page_id.strip():
            raise ValueError("page_id manquant pour retrieve_page().")

        return self._request("GET", f"/pages/{page_id}")

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
        return self._request("POST", "/search", payload=payload)


# ---------------------------------------------------------------------------
# FONCTION HISTORIQUE COMPATIBLE (NE PAS CASSER LES ORCHESTRATIONS EXISTANTES)
# ---------------------------------------------------------------------------


def _legacy_hdr() -> Dict[str, str]:
    """Ancienne fonction interne, conservée pour compatibilité éventuelle.

    Elle n'est plus utilisée en interne, mais on évite de casser d'anciens imports.
    """
    if not (NOTION_TOKEN or "").strip():
        raise RuntimeError("NOTION_TOKEN manquant.")
    return {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


def create_page_under_parent(
    title: str,
    blocks: List[Dict[str, Any]],
    parent_page_id: str | None = None,
) -> Dict[str, Any]:
    """API historique utilisée par les orchestrations (Obsidian → Notion).

    Cette fonction est un **wrapper** autour de NotionService, afin de ne
    rien casser dans le code existant :

        from hanuman.services.core.notion_service import create_page_under_parent

    Le comportement reste le même :
    - besoin d'un NOTION_PARENT_ID dans le .env (ou d'un parent explicite)
    - renvoie le dict JSON brut de Notion.

    Pour les nouvelles fonctionnalités, utiliser directement NotionService.
    """
    service = NotionService()
    ref = service.create_page_under_parent(
        title=title,
        blocks=blocks,
        parent_page_id=parent_page_id,
    )
    # On renvoie un dict proche de l'ancienne API (JSON Notion minimal)
    return {
        "id": ref.page_id,
        "url": ref.url,
    }
