from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from hanuman.models.github_project_memory import GitHubProjectMemoryInput
from hanuman.orchestrations.github_project_memory_notion import (
    NOTION_TEST_PARENT_PAGE_ID,
    apply_github_project_memory,
)
from hanuman.services.core.notion_service import NotionDatabaseRef, NotionPageRef
from tests.orchestrations.test_github_project_memory import (
    REPOSITORY,
    SHA_1,
    SHA_2,
    SHA_3,
    FakeGithubService,
    raw_commit,
)


def _response_rich_text(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    response: list[dict[str, Any]] = []
    for item in items:
        text = item["text"]
        link = text.get("link")
        response.append(
            {
                "plain_text": text["content"],
                "href": link.get("url") if link else None,
                "text": None,
            }
        )
    return response


def _response_properties(properties: dict[str, Any]) -> dict[str, Any]:
    response: dict[str, Any] = {}
    for name, value in properties.items():
        if "title" in value:
            response[name] = {
                "type": "title",
                "title": _response_rich_text(value["title"]),
            }
        elif "rich_text" in value:
            response[name] = {
                "type": "rich_text",
                "rich_text": _response_rich_text(value["rich_text"]),
            }
        elif "number" in value:
            response[name] = {"type": "number", "number": value["number"]}
        elif "url" in value:
            response[name] = {"type": "url", "url": value["url"]}
        elif "date" in value:
            response[name] = {"type": "date", "date": value["date"]}
        elif "select" in value:
            response[name] = {"type": "select", "select": value["select"]}
        elif "relation" in value:
            response[name] = {"type": "relation", "relation": value["relation"]}
        else:
            raise AssertionError(f"Propriété inattendue : {name}")
    return response


def _response_blocks(
    blocks: list[dict[str, Any]],
    *,
    offset: int = 0,
) -> list[dict[str, Any]]:
    response: list[dict[str, Any]] = []
    for block in blocks:
        block_type = block["type"]
        response.append(
            {
                "id": f"block-{offset + len(response) + 1}",
                "type": block_type,
                block_type: {
                    "rich_text": _response_rich_text(block[block_type].get("rich_text", []))
                },
            }
        )
    return response


class StatefulNotionService:
    def __init__(self) -> None:
        self.databases: dict[str, dict[str, Any]] = {}
        self.data_sources: dict[str, dict[str, Any]] = {}
        self.pages: dict[str, dict[str, Any]] = {}
        self.blocks: dict[str, list[dict[str, Any]]] = {}
        self.database_creations = 0
        self.page_creations = 0
        self.update_calls = 0
        self.append_calls = 0
        self.block_update_calls = 0
        self.delete_calls = 0

    def search(self, query: str, limit: int = 20) -> dict[str, Any]:
        del limit
        return {
            "results": [
                database
                for database in self.databases.values()
                if database["title"][0]["plain_text"] == query
            ]
        }

    def create_database(
        self,
        parent_page_id: str,
        title: str,
        properties: dict[str, Any],
    ) -> NotionDatabaseRef:
        self.database_creations += 1
        database_id = f"database-{self.database_creations}"
        data_source_id = f"data-source-{self.database_creations}"
        database = {
            "object": "database",
            "id": database_id,
            "parent": {"type": "page_id", "page_id": parent_page_id},
            "title": [{"plain_text": title}],
            "data_sources": [{"id": data_source_id}],
            "url": f"https://notion.test/{database_id}",
        }
        self.databases[database_id] = database
        self.data_sources[data_source_id] = {
            "id": data_source_id,
            "properties": {
                name: {"type": next(iter(configuration))}
                for name, configuration in properties.items()
            },
        }
        return NotionDatabaseRef(database_id, data_source_id, database["url"])

    def retrieve_database(self, database_id: str) -> dict[str, Any]:
        return self.databases[database_id]

    def retrieve_data_source(self, data_source_id: str) -> dict[str, Any]:
        return self.data_sources[data_source_id]

    def query_database(
        self,
        database_id: str,
        filter_: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        data_source_id = self.databases[database_id]["data_sources"][0]["id"]
        candidates = [
            page
            for page in self.pages.values()
            if page["parent"]["data_source_id"] == data_source_id
        ]
        if filter_ is None:
            return candidates
        property_name = filter_["property"]
        expected_filter = filter_["number"] if "number" in filter_ else filter_["rich_text"]
        expected = expected_filter["equals"]
        return [
            page
            for page in candidates
            if (
                page["properties"][property_name]["number"]
                if "number" in filter_
                else page["properties"][property_name]["rich_text"][0]["plain_text"]
            )
            == expected
        ]

    def create_page_in_data_source(
        self,
        database_id: str,
        properties: dict[str, Any],
        children: list[dict[str, Any]] | None = None,
    ) -> NotionPageRef:
        self.page_creations += 1
        page_id = f"page-{self.page_creations}"
        data_source_id = self.databases[database_id]["data_sources"][0]["id"]
        self.pages[page_id] = {
            "object": "page",
            "id": page_id,
            "parent": {
                "type": "data_source_id",
                "data_source_id": data_source_id,
            },
            "properties": _response_properties(properties),
            "url": f"https://notion.test/{page_id}",
        }
        self.blocks[page_id] = _response_blocks(children or [])
        return NotionPageRef(page_id, self.pages[page_id]["url"])

    def retrieve_page(self, page_id: str) -> dict[str, Any]:
        return self.pages[page_id]

    def retrieve_block_children(self, block_id: str) -> list[dict[str, Any]]:
        return self.blocks[block_id]

    def update_page_properties(
        self,
        page_id: str,
        properties: dict[str, Any],
    ) -> dict[str, Any]:
        self.update_calls += 1
        self.pages[page_id]["properties"].update(_response_properties(properties))
        return self.pages[page_id]

    def update_block(
        self,
        block_id: str,
        block_type: str,
        content: dict[str, Any],
    ) -> dict[str, Any]:
        self.block_update_calls += 1
        for blocks in self.blocks.values():
            for block in blocks:
                if block["id"] == block_id:
                    block[block_type] = {
                        "rich_text": _response_rich_text(content.get("rich_text", []))
                    }
                    return block
        raise AssertionError(f"Bloc inconnu : {block_id}")

    def append_blocks(
        self,
        page_id: str,
        blocks: list[dict[str, Any]],
    ) -> dict[str, Any]:
        self.append_calls += 1
        self.blocks[page_id].extend(_response_blocks(blocks, offset=len(self.blocks[page_id])))
        return {}


def _flow_input() -> GitHubProjectMemoryInput:
    return GitHubProjectMemoryInput(
        repository=REPOSITORY,
        branch="main",
        max_commits=3,
        session_window_hours=24,
        session_max_duration_hours=1,
        allowed_repositories=(REPOSITORY,),
    )


def _github_service() -> FakeGithubService:
    started_at = datetime(2026, 7, 1, 9, tzinfo=UTC)
    return FakeGithubService(
        [
            raw_commit(
                SHA_1,
                committed_at=started_at,
                message="docs: project memory",
            ),
            raw_commit(
                SHA_2,
                parent=SHA_1,
                committed_at=started_at + timedelta(minutes=30),
                message="test: verification",
            ),
            raw_commit(
                SHA_3,
                parent=SHA_2,
                committed_at=started_at + timedelta(hours=2),
                message="feat(flows): notion apply",
            ),
        ]
    )


def test_apply_creates_databases_repository_sessions_content_and_relation() -> None:
    notion = StatefulNotionService()

    run = apply_github_project_memory(
        _flow_input(),
        github_factory=_github_service,
        notion_factory=lambda: notion,  # type: ignore[arg-type]
    )

    assert run.status == "succeeded"
    assert run.result.status == "verified"
    assert run.result.verification == "passed"
    assert notion.database_creations == 2
    assert notion.page_creations == 3
    assert run.metrics["notion_databases_created"] == 2
    assert run.metrics["notion_pages_created"] == 3
    assert run.metrics["notion_updates"] == 0
    assert run.metrics["notion_deletions"] == 0
    assert {database["title"][0]["plain_text"] for database in notion.databases.values()} == {
        "Repositories",
        "Development Sessions",
    }
    assert {database["parent"]["page_id"] for database in notion.databases.values()} == {
        NOTION_TEST_PARENT_PAGE_ID
    }

    repository_page = next(
        page for page in notion.pages.values() if "GitHub Repository ID" in page["properties"]
    )
    session_pages = [page for page in notion.pages.values() if "Session ID" in page["properties"]]
    assert len(session_pages) == 2
    for page in session_pages:
        assert page["properties"]["Repository"]["relation"] == [{"id": repository_page["id"]}]
        assert [block["type"] for block in notion.blocks[page["id"]]][:3] == [
            "heading_2",
            "paragraph",
            "heading_2",
        ]
        commit_count = page["properties"]["Commit Count"]["number"]
        assert len(notion.blocks[page["id"]]) == 3 + commit_count

    assert [step.step_id for step in run.step_results[-2:]] == [
        "apply_notion",
        "verify_notion",
    ]
    assert notion.update_calls == 0
    assert notion.delete_calls == 0


def test_second_apply_is_no_change_without_duplication() -> None:
    notion = StatefulNotionService()
    first = apply_github_project_memory(
        _flow_input(),
        github_factory=_github_service,
        notion_factory=lambda: notion,  # type: ignore[arg-type]
    )
    second = apply_github_project_memory(
        _flow_input(),
        github_factory=_github_service,
        notion_factory=lambda: notion,  # type: ignore[arg-type]
    )

    assert first.result.verification == "passed"
    assert second.result.verification == "passed"
    assert second.result.resources_created == 0
    assert second.result.resources_skipped == 5
    assert second.metrics["external_writes"] == 0
    assert second.metrics["notion_no_change"] == 5
    assert notion.database_creations == 2
    assert notion.page_creations == 3
    assert len(notion.databases) == 2
    assert len(notion.pages) == 3
    assert all(effect.effect_type.endswith(".no_change") for effect in second.result.effects)
    assert first.idempotency_key == second.idempotency_key
    assert first.result.plan is not None
    assert second.result.plan is not None
    assert first.result.plan.fingerprint == second.result.plan.fingerprint
    assert notion.update_calls == 0
    assert notion.delete_calls == 0


def test_existing_different_summary_is_updated_and_verified() -> None:
    notion = StatefulNotionService()
    first = apply_github_project_memory(
        _flow_input(),
        github_factory=_github_service,
        notion_factory=lambda: notion,  # type: ignore[arg-type]
    )
    session_page_id = next(
        page_id for page_id, page in notion.pages.items() if "Session ID" in page["properties"]
    )
    notion.blocks[session_page_id][1]["paragraph"]["rich_text"][0][
        "plain_text"
    ] = "Contenu manuel différent"

    second = apply_github_project_memory(
        _flow_input(),
        github_factory=_github_service,
        notion_factory=lambda: notion,  # type: ignore[arg-type]
    )

    assert first.result.verification == "passed"
    assert second.status == "succeeded"
    assert second.result.verification == "passed"
    assert second.result.resources_updated == 1
    assert notion.block_update_calls == 1
    assert notion.delete_calls == 0


def test_existing_session_updates_properties_summary_and_appends_only_new_commit() -> None:
    notion = StatefulNotionService()
    started_at = datetime(2026, 7, 1, 9, 0, 45, tzinfo=UTC)
    first_github = FakeGithubService(
        [
            raw_commit(
                SHA_1,
                committed_at=started_at,
                message="docs(notion): initial projection",
            )
        ]
    )
    second_github = FakeGithubService(
        [
            raw_commit(
                SHA_1,
                committed_at=started_at,
                message="docs(notion): initial projection",
            ),
            raw_commit(
                SHA_2,
                parent=SHA_1,
                committed_at=started_at + timedelta(minutes=20),
                message="feat(sync): incremental projection",
            ),
        ]
    )

    first = apply_github_project_memory(
        _flow_input(),
        github_factory=lambda: first_github,
        notion_factory=lambda: notion,  # type: ignore[arg-type]
    )
    second = apply_github_project_memory(
        _flow_input(),
        github_factory=lambda: second_github,
        notion_factory=lambda: notion,  # type: ignore[arg-type]
    )
    third = apply_github_project_memory(
        _flow_input(),
        github_factory=lambda: second_github,
        notion_factory=lambda: notion,  # type: ignore[arg-type]
    )

    assert first.result.verification == "passed"
    assert second.result.verification == "passed"
    assert second.result.resources_created == 0
    assert second.result.resources_updated == 2  # repository et session
    assert second.metrics["commits_added"] == 1
    assert second.metrics["commits_already_present"] == 1
    assert notion.append_calls == 1
    session_page = next(
        page for page in notion.pages.values() if "Session ID" in page["properties"]
    )
    assert session_page["properties"]["Commit Count"]["number"] == 2
    assert session_page["properties"]["Title"]["title"][0]["plain_text"] == (
        "main — Documentation et Notion"
    )
    assert session_page["properties"]["Started At"]["date"]["start"].endswith("09:00:00+00:00")
    assert len(notion.blocks[session_page["id"]]) == 5

    assert third.result.verification == "passed"
    assert third.result.resources_created == 0
    assert third.result.resources_updated == 0
    assert third.metrics["external_writes"] == 0
    assert third.metrics["commits_added"] == 0
    assert third.metrics["commits_already_present"] == 2
    assert notion.append_calls == 1
    assert notion.delete_calls == 0


def test_notion_dates_compare_at_minute_precision() -> None:
    notion = StatefulNotionService()
    first = apply_github_project_memory(
        _flow_input(),
        github_factory=_github_service,
        notion_factory=lambda: notion,  # type: ignore[arg-type]
    )
    for page in notion.pages.values():
        for name in ("Created At", "Updated At", "Started At", "Last Activity", "Ended At"):
            property_value = page["properties"].get(name)
            if property_value and property_value["date"] is not None:
                property_value["date"]["start"] = property_value["date"]["start"].replace(
                    ":00+00:00",
                    ":37+00:00",
                )

    second = apply_github_project_memory(
        _flow_input(),
        github_factory=_github_service,
        notion_factory=lambda: notion,  # type: ignore[arg-type]
    )

    assert first.result.verification == "passed"
    assert second.result.verification == "passed"
    assert second.result.resources_updated == 0
    assert second.metrics["external_writes"] == 0
