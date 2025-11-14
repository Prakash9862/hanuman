
from __future__ import annotations

from typing import Any, Dict, List

import hanuman.orchestrations.github_to_notion as gtn


class FakeGithubService:
    """Fake minimal de GithubService pour les tests de sync."""

    def __init__(self, issues: List[Dict[str, Any]]) -> None:
        self._issues = issues

    def list_issues(
        self,
        full_name: str | None = None,
        state: str = "open",
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        # On ignore full_name/state/limit dans ce fake simple
        return self._issues


class FakePageRef:
    def __init__(self, page_id: str, url: str) -> None:
        self.page_id = page_id
        self.url = url


class FakeNotionService:
    """Fake minimal de NotionService pour vérifier create/update."""

    def __init__(self, existing_issue_number: int | None = None) -> None:
        # Si existing_issue_number est défini, on fera comme si une page
        # existait déjà pour ce numéro d'issue.
        self._existing_issue_number = existing_issue_number
        self.created: List[Dict[str, Any]] = []
        self.updated: List[Dict[str, Any]] = []

    # --- interface attendue par github_to_notion ---

    def search(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """Simule la recherche Notion utilisée dans _find_issue_page_by_number.

        On renvoie une page uniquement si query correspond au numéro existant.
        """
        if self._existing_issue_number is None:
            return {"results": []}

        # query est une string, on essaie de la convertir
        try:
            q_number = int(query)
        except ValueError:
            return {"results": []}

        if q_number != self._existing_issue_number:
            return {"results": []}

        return {
            "results": [
                {
                    "object": "page",
                    "id": "page-existing",
                    "parent": {"database_id": gtn.NOTION_ISSUES_DB_ID},
                    "properties": {
                        "Numéro": {"number": self._existing_issue_number},
                    },
                }
            ]
        }

    def create_page_in_database(
        self,
        database_id: str,
        properties: Dict[str, Any],
        children: List[Dict[str, Any]] | None = None,
    ) -> FakePageRef:
        self.created.append(
            {
                "database_id": database_id,
                "properties": properties,
            }
        )
        return FakePageRef(page_id="page-created", url="https://notion.fake/page-created")

    def update_page_properties(
        self,
        page_id: str,
        properties: Dict[str, Any],
    ) -> Dict[str, Any]:
        self.updated.append(
            {
                "page_id": page_id,
                "properties": properties,
            }
        )
        return {"id": page_id}

def test_sync_creates_new_page_when_issue_not_present(monkeypatch: Any) -> None:
    """Si l'issue n'existe pas encore dans Notion, on doit créer une page."""

    issues = [
        {
            "title": "New issue",
            "url": "https://github.com/Prakasch/hanuman/issues/1",
            "state": "open",
            "number": 1,
            "labels": ["bug"],
        }
    ]

    fake_github = FakeGithubService(issues=issues)
    fake_notion = FakeNotionService(existing_issue_number=None)

    # On force un NOTION_ISSUES_DB_ID non vide pour éviter RuntimeError
    monkeypatch.setattr(gtn, "NOTION_ISSUES_DB_ID", "fake-db-id")

    # On remplace les services réels par nos fakes
    monkeypatch.setattr(gtn, "GithubService", lambda: fake_github)
    monkeypatch.setattr(gtn, "NotionService", lambda: fake_notion)

    # Appel de la fonction à tester
    gtn.sync_github_issues_to_notion(
        repo="Prakasch/hanuman",
        state="open",
        limit=10,
    )

    # On doit avoir créé une page, et aucune mise à jour
    assert len(fake_notion.created) == 1
    assert len(fake_notion.updated) == 0

    created_props = fake_notion.created[0]["properties"]
    assert created_props["Numéro"]["number"] == 1
    assert created_props["Etat"]["select"]["name"] == "open"


def test_sync_updates_existing_page_when_issue_already_in_notion(monkeypatch: Any) -> None:
    """Si une page existe déjà pour ce numéro, on doit faire un update, pas une création."""

    issues = [
        {
            "title": "Existing issue updated",
            "url": "https://github.com/Prakasch/hanuman/issues/2",
            "state": "closed",
            "number": 2,
            "labels": ["refactor"],
        }
    ]

    fake_github = FakeGithubService(issues=issues)
    # On simule le fait que l'issue #2 existe déjà dans Notion
    fake_notion = FakeNotionService(existing_issue_number=2)

    monkeypatch.setattr(gtn, "NOTION_ISSUES_DB_ID", "fake-db-id")
    monkeypatch.setattr(gtn, "GithubService", lambda: fake_github)
    monkeypatch.setattr(gtn, "NotionService", lambda: fake_notion)

    gtn.sync_github_issues_to_notion(
        repo="Prakasch/hanuman",
        state="all",
        limit=10,
    )

    # Ici, on attend une mise à jour, mais aucune création
    assert len(fake_notion.created) == 0
    assert len(fake_notion.updated) == 1

    updated = fake_notion.updated[0]
    assert updated["page_id"] == "page-existing"
    props = updated["properties"]
    assert props["Numéro"]["number"] == 2
    assert props["Etat"]["select"]["name"] == "closed"
    assert {l["name"] for l in props["Labels"]["multi_select"]} == {"refactor"}
