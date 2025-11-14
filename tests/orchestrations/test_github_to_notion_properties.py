from __future__ import annotations

from typing import Any, Dict, List

from hanuman.orchestrations.github_to_notion import (
    ISSUES_DB_TITLE_PROP,
    _build_issue_properties,
)


def test_build_issue_properties_basic() -> None:
    issue: Dict[str, Any] = {
        "title": "Fix bug in chess module",
        "url": "https://github.com/Prakasch/hanuman/issues/42",
        "state": "open",
        "number": 42,
        "labels": ["bug", "chess"],
    }
    repo_name = "Prakasch/hanuman"

    props = _build_issue_properties(issue, repo_name)

    # la clé de titre dépend de ISSUES_DB_TITLE_PROP
    assert ISSUES_DB_TITLE_PROP in props
    title_prop = props[ISSUES_DB_TITLE_PROP]
    assert title_prop["title"][0]["text"]["content"] == "Fix bug in chess module"

    assert props["URL"]["url"] == issue["url"]
    assert props["Etat"]["select"]["name"] == "open"
    assert props["Repo"]["select"]["name"] == repo_name
    assert props["Numéro"]["number"] == 42

    labels_prop: List[Dict[str, Any]] = props["Labels"]["multi_select"]
    assert {l["name"] for l in labels_prop} == {"bug", "chess"}


def test_build_issue_properties_dates_optional() -> None:
    issue: Dict[str, Any] = {
        "title": "Close old issue",
        "url": "https://github.com/Prakasch/hanuman/issues/10",
        "state": "closed",
        "number": 10,
        "labels": [],
        "created_at": "2025-01-01T12:00:00Z",
        "updated_at": "2025-01-02T13:30:00Z",
    }
    repo_name = "Prakasch/hanuman"

    props = _build_issue_properties(issue, repo_name)

    assert props["Etat"]["select"]["name"] == "closed"
    assert props["Créé le"]["date"]["start"] == "2025-01-01T12:00:00Z"
    assert props["Modifié le"]["date"]["start"] == "2025-01-02T13:30:00Z"

