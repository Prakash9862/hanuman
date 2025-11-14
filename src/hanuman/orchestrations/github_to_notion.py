from __future__ import annotations

import argparse
from typing import Any, Dict, List, Optional

from hanuman.config.env import GITHUB_REPO, NOTION_ISSUES_DB_ID
from hanuman.services.core.github_service import GithubService
from hanuman.services.core.notion_service import NotionService

# Nom de la propriété titre dans ta database Notion "Issues".
# Si ta colonne titre s'appelle "Nom" dans Notion, change ici.
ISSUES_DB_TITLE_PROP = "Name"  # ou "Nom"


def _build_issue_properties(issue: Dict[str, Any], repo_name: str) -> Dict[str, Any]:
    """Construit le dict 'properties' pour Notion à partir d'une issue GitHub."""

    title = str(issue.get("title", "")).strip() or f"Issue #{issue.get('number')}"
    url = str(issue.get("url", "")).strip()
    state = str(issue.get("state", "open")).strip()
    number = int(issue.get("number", 0))
    labels: List[str] = list(issue.get("labels", []))

    properties: Dict[str, Any] = {
        # Propriété titre de ta database Notion
        ISSUES_DB_TITLE_PROP: {
            "title": [
                {"type": "text", "text": {"content": title}},
            ]
        },
        "URL": {"url": url or None},
        "Etat": {"select": {"name": state}},
        "Repo": {"select": {"name": repo_name}},
        "Numéro": {"number": number},
    }

    if labels:
        properties["Labels"] = {
            "multi_select": [{"name": label} for label in labels],
        }

    created_at = issue.get("created_at")
    updated_at = issue.get("updated_at")

    if created_at:
        properties["Créé le"] = {"date": {"start": created_at}}
    if updated_at:
        properties["Modifié le"] = {"date": {"start": updated_at}}

    return properties


def _find_issue_page_by_number(
    notion: NotionService,
    issue_number: int,
    limit: int = 10,
) -> Optional[str]:
    """Essaie de retrouver la page Notion correspondant à une issue GitHub donnée.

    Stratégie :
    - on utilise Notion /search avec comme query le numéro (ou rien)
    - on filtre ensuite côté Python les résultats :
        - uniquement les pages
        - qui possèdent une propriété 'Numéro' == issue_number
        - et qui appartiennent à la bonne database (parent.database_id = NOTION_ISSUES_DB_ID)
    """

    # On recherche sans query (ou avec le numéro) pour limiter un peu
    data = notion.search(query=str(issue_number), limit=limit)

    results = data.get("results", [])
    for result in results:
        if result.get("object") != "page":
            continue

        parent = result.get("parent", {})
        parent_db_id = parent.get("database_id")
        if parent_db_id and NOTION_ISSUES_DB_ID and parent_db_id != NOTION_ISSUES_DB_ID:
            # Page d'une autre database → on ignore
            continue

        props = result.get("properties", {})
        numero_prop = props.get("Numéro", {})
        number_value = numero_prop.get("number")

        if isinstance(number_value, (int, float)) and int(number_value) == issue_number:
            return result.get("id")

    return None


def sync_github_issues_to_notion(
    repo: str | None = None,
    state: str = "open",
    limit: int = 50,
) -> None:
    """Synchronise les issues GitHub vers la database Notion Issues.

    - crée une page pour les issues absentes
    - met à jour les propriétés pour les issues déjà présentes
    """

    if not NOTION_ISSUES_DB_ID:
        raise RuntimeError(
            "NOTION_ISSUES_DB_ID n'est pas configuré dans le .env. "
            "Mets l'ID de ta database Notion 'Issues'."
        )

    repo_name = (repo or GITHUB_REPO or "").strip()
    if not repo_name:
        raise RuntimeError(
            "Aucun repo GitHub spécifié. "
            "Passe --repo 'owner/name' ou configure GITHUB_REPO dans le .env."
        )

    github = GithubService()
    notion = NotionService()

    issues = github.list_issues(full_name=repo_name, state=state, limit=limit)
    if not issues:
        print(f"[github→notion] aucune issue trouvée pour {repo_name} (state={state})")
        return

    print(
        f"[github→notion] {len(issues)} issues trouvées sur {repo_name} "
        f"(state={state}, limit={limit})"
    )

    created_count = 0
    updated_count = 0

    for issue in issues:
        number = int(issue.get("number", 0))
        props = _build_issue_properties(issue, repo_name)

        page_id = _find_issue_page_by_number(notion, number)
        if page_id:
            notion.update_page_properties(page_id, props)
            updated_count += 1
            print(f"  - Issue #{number} → mise à jour de la page Notion {page_id}")
        else:
            page_ref = notion.create_page_in_database(NOTION_ISSUES_DB_ID, props)
            created_count += 1
            print(
                f"  - Issue #{number} → création page Notion {page_ref.page_id} "
                f"({page_ref.url})"
            )

    print(
        f"[github→notion] Synchronisation terminée : "
        f"{created_count} pages créées, {updated_count} mises à jour."
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Synchronise les issues GitHub vers la database Notion 'Issues'."
    )
    parser.add_argument(
        "--repo",
        type=str,
        default=None,
        help="Nom complet du repo GitHub (ex: 'Prakash9862/hanuman'). "
        "Si absent, utilise GITHUB_REPO du .env.",
    )
    parser.add_argument(
        "--state",
        type=str,
        choices=["open", "closed", "all"],
        default="open",
        help="État des issues à synchroniser (par défaut: open).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Nombre maximum d'issues à récupérer (max 100).",
    )

    args = parser.parse_args()
    sync_github_issues_to_notion(
        repo=args.repo,
        state=args.state,
        limit=args.limit,
    )


if __name__ == "__main__":
    main()
