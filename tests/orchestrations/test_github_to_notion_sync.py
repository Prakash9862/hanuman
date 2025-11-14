from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

import hanuman.orchestrations.github_to_notion as gtn


@dataclass
class FakePageRef:
    page_id: str
    url: str


class FakeGithubService:
    def __init__(self, issues: List[Dict[str, Any]]) -> None:
        self._issues = issues

    def list_issues(
        self,
        full_name: str,
        state: str,
        limit: int,
    ) -> List[Dict[str, Any]]:
        # On s’en fiche du repo / state dans ces tests, on renvoie juste la liste
        return self._issues[:limit]


class FakeNotionService:
    def __init__(self, existing_issue_number: int | None = None) -> None:
        # Si ce numéro est non nul, on simule une page déjà présente
        self.existing_issue_number = existing_issue_number
        self.created: List[Dict[str, Any]] = []
        self.updated: List[Dict[str, Any]] = []

    def query_database(
        self,
        db_id: str,
        filter_: Dict[str, Any] | None = None,
    ) -> List[Dict[str, Any]]:
        """Simule une recherche dans la DB Notion.

        Si existing_issue_number est défini et que le filtre demande ce numéro,
        on renvoie une page factice avec un id stable.
        """
        if self.existing_issue_number is None:
            return []

        if not filter_:
            return [{"id": "existing-page"}]

        number_filter = filter_.get("number", {}) if isinstance(filter_, dict) else {}
        equals_value = number_filter.get("equals")
        if equals_value == self.existing_issue_number:
            return [{"id": "existing-page"}]

        return []

    def create_page_in_database(
        self,
        db_id: str,
        properties: Dict[str, Any],
    ) -> FakePageRef:
        """Simule la création d’une page, et stocke l’appel."""
        number = properties.get("Numéro", {}).get("number", 0)
        page_id = f"page-{number}"
        url = f"https://notion.fake/{page_id}"
        self.created.append(
            {
                "db_id": db_id,
                "properties": properties,
                "page_id": page_id,
                "url": url,
            }
        )
        return FakePageRef(page_id=page_id, url=url)

    def update_page_properties(
        self,
        page_id: str,
        properties: Dict[str, Any],
    ) -> None:
        """Simule une mise à jour de page."""
        self.updated.append(
            {
                "page_id": page_id,
                "properties": properties,
            }
        )


def test_sync_creates_new_page_when_issue_not_present(monkeypatch: Any) -> None:
    """Si l’issue n’existe pas dans Notion, on doit créer une page."""
    issues = [
        {
            "title": "New issue",
            "url": "https://github.com/Prakasch/hanuman/issues/1",
            "state": "open",
            "number": 1,
            "labels": ["bug", "chess"],
        }
    ]

    fake_github = FakeGithubService(issues=issues)
    fake_notion = FakeNotionService(existing_issue_number=None)

    monkeypatch.setattr(gtn, "NOTION_ISSUES_DB_ID", "fake-db-id")
    monkeypatch.setattr(gtn, "GithubService", lambda: fake_github)
    monkeypatch.setattr(gtn, "NotionService", lambda: fake_notion)

    gtn.sync_github_issues_to_notion(
        repo="Prakasch/hanuman",
        state="open",
        limit=10,
    )

    assert len(fake_notion.created) == 1
    created = fake_notion.created[0]
    assert created["db_id"] == "fake-db-id"
    props = created["properties"]
    assert props["Numéro"]["number"] == 1
    assert props["Etat"]["select"]["name"] == "open"
    labels = {label["name"] for label in props["Labels"]["multi_select"]}
    assert labels == {"bug", "chess"}

    assert len(fake_notion.updated) == 0


def test_sync_updates_existing_page_when_issue_already_in_notion(
    monkeypatch: Any,
) -> None:
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
    fake_notion = FakeNotionService(existing_issue_number=2)

    monkeypatch.setattr(gtn, "NOTION_ISSUES_DB_ID", "fake-db-id")
    monkeypatch.setattr(gtn, "GithubService", lambda: fake_github)
    monkeypatch.setattr(gtn, "NotionService", lambda: fake_notion)

    gtn.sync_github_issues_to_notion(
        repo="Prakasch/hanuman",
        state="all",
        limit=10,
    )

    # Pas de création
    assert len(fake_notion.created) == 0

    # Une seule mise à jour de la page existante
    assert len(fake_notion.updated) == 1
    updated = fake_notion.updated[0]
    assert updated["page_id"] == "existing-page"
    props = updated["properties"]
    assert props["Numéro"]["number"] == 2
    assert props["Etat"]["select"]["name"] == "closed"
    labels = {label["name"] for label in props["Labels"]["multi_select"]}
    assert labels == {"refactor"}
