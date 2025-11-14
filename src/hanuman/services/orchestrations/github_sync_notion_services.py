"""
Compatibilité v5 → v6 pour la sync GitHub → Notion.

Ce module existait en v5-dev sous le nom
`hanuman.services.orchestrations.github_sync_notion_services`.

En v6-dev, la logique réelle a été déplacée dans
`hanuman.orchestrations.github_to_notion`.

On garde ce fichier comme fine couche de compatibilité pour les tests
et tout ancien code qui importerait encore l'ancien chemin.
"""

from __future__ import annotations

from typing import Any, Optional

from hanuman.orchestrations.github_to_notion import (
    sync_github_issues_to_notion,
)


__all__ = ["sync_github_issues_to_notion", "main"]


def main(
    *,
    repo: Optional[str] = None,
    state: str = "open",
    limit: int = 50,
) -> None:
    """Wrapper léger autour de `sync_github_issues_to_notion`.

    Permet d'appeler l'ancien module comme un script si besoin.
    """
    sync_github_issues_to_notion(
        repo=repo,
        state=state,
        limit=limit,
    )

